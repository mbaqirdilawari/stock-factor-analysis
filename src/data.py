"""Step 1: get the two data sets.

1. Monthly stock prices, from Yahoo Finance (through the yfinance package).
2. Monthly Fama-French factors, from Kenneth French's free data library.

Both are downloaded once and saved in the data/ folder, so a second run is fast.
"""
import io
import time
import zipfile
from pathlib import Path

import pandas as pd
import requests

FF_URL = (
    "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/"
    "F-F_Research_Data_5_Factors_2x3_CSV.zip"
)
FACTOR_COLUMNS = ["Mkt-RF", "SMB", "HML", "RMW", "CMA", "RF"]


def parse_french_csv(text):
    """Turn the text of the Fama-French file into a table of monthly factors.

    The file has a few lines of notes, then a monthly table, then a yearly
    table. We keep only the monthly table. The numbers are in percent, so we
    divide by 100 to get plain returns (1.5 becomes 0.015).
    """
    rows = []
    started = False
    for line in text.splitlines():
        parts = [p.strip() for p in line.split(",")]
        is_month_row = len(parts) == 7 and parts[0].isdigit() and len(parts[0]) == 6
        if is_month_row:
            started = True
            rows.append(parts)
        elif started:
            break  # the monthly table has ended
    if not rows:
        raise ValueError("Could not find the monthly table in the factor file.")

    table = pd.DataFrame(rows, columns=["Date"] + FACTOR_COLUMNS)
    table["Date"] = pd.to_datetime(table["Date"], format="%Y%m").dt.to_period("M")
    table = table.set_index("Date").astype(float) / 100
    return table


def download_factors(cache_dir, refresh=False):
    """Get the monthly factors (from the saved copy if there is one)."""
    cache_file = Path(cache_dir) / "ff5_monthly.csv"
    if cache_file.exists() and not refresh:
        table = pd.read_csv(cache_file, index_col=0)
        table.index = pd.PeriodIndex(table.index, freq="M")
        return table

    reply = requests.get(FF_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
    reply.raise_for_status()
    with zipfile.ZipFile(io.BytesIO(reply.content)) as archive:
        name = archive.namelist()[0]
        text = archive.read(name).decode("latin-1")
    table = parse_french_csv(text)

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    table.to_csv(cache_file)
    return table


def _download_one(ticker, start, tries=3):
    """Download the daily closing prices of ONE stock, trying a few times.

    We download one stock at a time, without parallel threads. Downloading
    many at once can make yfinance's small local database lock up
    ("database is locked").
    """
    import yfinance as yf  # imported here so the tests do not need it

    for attempt in range(tries):
        try:
            raw = yf.download(ticker, start=start, auto_adjust=True, progress=False, threads=False)
            close = raw["Close"]
            if hasattr(close, "columns"):  # some versions return a one-column table
                close = close.iloc[:, 0]
            close = close.dropna()
            if not close.empty:
                return close
        except Exception:
            pass  # try again below
        time.sleep(2)
    raise RuntimeError(f"No price data came back for {ticker}. Wait a few minutes and run it again.")


def download_returns(tickers, start, cache_dir, refresh=False):
    """Get monthly stock returns (from the saved copy if there is one)."""
    cache_file = Path(cache_dir) / "monthly_returns.csv"
    if cache_file.exists() and not refresh:
        table = pd.read_csv(cache_file, index_col=0)
        table.index = pd.PeriodIndex(table.index, freq="M")
        return table

    prices = pd.DataFrame({ticker: _download_one(ticker, start) for ticker in tickers})

    # Take the last price of each month, then the percent change from month to month.
    month_end = prices.groupby(prices.index.to_period("M")).last()
    returns = month_end.pct_change().iloc[1:]

    cache_file.parent.mkdir(parents=True, exist_ok=True)
    returns.to_csv(cache_file)
    return returns


def line_up(returns, factors):
    """Keep only the months that exist in both data sets.

    Then subtract the risk-free rate (RF) from each stock return. The result is
    called the "excess return", which is what the factor models explain.
    """
    both = returns.join(factors, how="inner").dropna()
    stocks = both[list(returns.columns)]
    factor_table = both[FACTOR_COLUMNS]
    excess = stocks.sub(factor_table["RF"], axis=0)
    return excess, factor_table