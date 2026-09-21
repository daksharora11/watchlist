#!/usr/bin/env python3
"""Fetch delayed quotes for the watchlist and write data/prices.json.

Standard library only, so the GitHub workflow needs no installs.
Primary source: Yahoo Finance's public chart endpoint (unofficial, ~15 min delay).
Fallback per ticker: Stooq's CSV quote (no 52-week range, so the page keeps its snapshot range).

This script never fails the workflow. If a ticker cannot be fetched, the page keeps
showing its Sept 18 snapshot price for that ticker and says so in the header.
"""
import csv
import io
import json
import math
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

# Keep this list in sync with the tickers in index.html.
TICKERS = ["MU", "SNDK", "LRCX", "MRVL", "INTC", "NVDA", "COIN", "HOOD", "MSTR", "VLO", "FRO", "VST", "CEG", "ADBE", "NKE"]

# (label, Yahoo symbol, display kind) for the market strip at the top of the page.
PULSE = [
    ("S&P 500", "^GSPC", "pct"),
    ("Nasdaq", "^IXIC", "pct"),
    ("Dow", "^DJI", "pct"),
    ("10-yr yield", "^TNX", "yield"),
    ("Bitcoin", "BTC-USD", "price"),
]

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "prices.json")
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")


def get(url, tries=3, timeout=20):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", "replace")
        except Exception as exc:  # network errors, HTTP 429, timeouts
            last = exc
            time.sleep(1.5 * (i + 1))
    raise last


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) and v > 0 else None


def yahoo_meta(symbol):
    enc = urllib.parse.quote(symbol, safe="")
    err = None
    for host in ("query1", "query2"):
        try:
            raw = get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{enc}?range=1d&interval=1d", tries=2)
            return json.loads(raw)["chart"]["result"][0]["meta"]
        except Exception as exc:
            err = exc
    raise err


def from_yahoo(ticker):
    m = yahoo_meta(ticker)
    price = num(m.get("regularMarketPrice"))
    if not price:
        raise ValueError("no price in response")
    as_of = None
    if m.get("regularMarketTime"):
        as_of = datetime.fromtimestamp(m["regularMarketTime"], timezone.utc).isoformat(timespec="seconds")
    return {
        "price": price,
        "prev": num(m.get("previousClose")) or num(m.get("chartPreviousClose")),
        "hi52": num(m.get("fiftyTwoWeekHigh")),
        "lo52": num(m.get("fiftyTwoWeekLow")),
        "asOf": as_of,
        "source": "Yahoo Finance",
    }


def from_stooq(ticker):
    raw = get(f"https://stooq.com/q/l/?s={ticker.lower()}.us&f=sd2t2ohlcv&h&e=csv", tries=2)
    row = next(csv.DictReader(io.StringIO(raw)))
    price = num(row.get("Close"))
    if not price:
        raise ValueError("no data")
    return {"price": price, "open": num(row.get("Open")), "asOf": None, "source": "Stooq"}


def main():
    quotes, missing = {}, []
    for t in TICKERS:
        q = None
        for fn in (from_yahoo, from_stooq):
            try:
                q = fn(t)
                break
            except Exception as exc:
                print(f"{t}: {fn.__name__} failed ({exc})", file=sys.stderr)
        if q:
            quotes[t] = {k: v for k, v in q.items() if v is not None}
            print(f"{t}: {q['price']} via {q['source']}")
        else:
            missing.append(t)
        time.sleep(0.3)

    pulse = []
    for label, symbol, kind in PULSE:
        try:
            m = yahoo_meta(symbol)
            price = num(m.get("regularMarketPrice"))
            if price:
                pulse.append({"label": label, "kind": kind, "price": price,
                              "prev": num(m.get("previousClose")) or num(m.get("chartPreviousClose"))})
        except Exception as exc:
            print(f"{label}: failed ({exc})", file=sys.stderr)
        time.sleep(0.3)

    out = {
        "updated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "Yahoo Finance with Stooq fallback; delayed about 15 minutes",
        "quotes": quotes,
        "missing": missing,
        "pulse": pulse,
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=2)
        fh.write("\n")

    if not quotes:
        print("::warning::No quotes could be fetched. The site will keep showing the Sept 18 snapshot.")
    elif missing:
        print(f"::warning::Missing quotes for: {', '.join(missing)}")
    print(f"Wrote {len(quotes)} quotes, {len(pulse)} market-strip items.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
