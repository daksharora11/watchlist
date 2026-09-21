# Momentum watchlist

A 13-stock tracker page. Research aid only, not investment advice.

## Part 1: put the page online (no automation, nothing to go wrong)

1. github.com -> **+** (top right) -> **New repository**. Name: `watchlist`. Choose **Public**. Click **Create repository**.
2. Unzip the download. Open the unzipped `watchlist` folder, select everything INSIDE it (index.html, data, scripts, setup, README.md) and drag it onto the repository page (**uploading an existing file** link, or Add file -> Upload files). Do not drag the outer folder. Click **Commit changes**.
3. Check the repo's main page: `index.html` must be listed at the top level, next to the `data` and `scripts` folders.
4. **Settings -> Pages -> Build and deployment -> Source: Deploy from a branch.** Branch: `main`, folder: `/ (root)`. Click **Save**.
5. Wait 2-3 minutes, then open `https://YOUR-USERNAME.github.io/watchlist/`.

You should see the tracker with a "Snapshot: Sept 18" note. That means hosting works.

## Part 2: turn on automatic price updates

1. In the repo click **Add file -> Create new file**.
2. In the name box type `.github/workflows/refresh-prices.yml` (typing each `/` creates a folder).
3. Paste in the full contents of `setup/refresh-prices.yml`. Click **Commit changes**.
4. **Actions** tab -> **Refresh prices** -> **Run workflow**. Wait about a minute for the green check.
5. Wait 1-2 minutes, then reload your page. The header should now say "Prices updated ...".

After that it refreshes itself every 15 minutes on weekdays during US market hours (13:00-21:59 UTC).

## Notes

- Prices come from Yahoo Finance's unofficial public endpoint (Stooq as fallback) and are delayed about 15 minutes. If a ticker can't be fetched, the page keeps its Sept 18 snapshot price for it.
- Each refresh adds a small "Update prices" commit to the repo. That is normal.
- News, analyst ratings, P/E and the buy/sell notes do not update by themselves.
- GitHub pauses scheduled workflows after 60 days without repo activity. Click **Run workflow** to restart it.
- To change the stock list, edit `TICKERS` in `scripts/update_prices.py` and `STOCKS` in `index.html`.
