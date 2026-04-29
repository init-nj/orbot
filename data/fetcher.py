# data/fetcher.py
import yfinance as yf
import pandas as pd


def fetch_data(ticker: str, period: str = "30d", interval: str = "5m") -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    df.index = pd.to_datetime(df.index)
    df.index = df.index.tz_convert("Asia/Kolkata")

    # Fix MultiIndex columns yfinance now returns
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df.dropna(inplace=True)
    return df


if __name__ == "__main__":
    df = fetch_data("RELIANCE.NS")
    print(df.head())