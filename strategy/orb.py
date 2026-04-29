import pandas as pd
MARKET_OPEN = "09:15"

def compute_orb(df: pd.DataFrame, orb_minutes: int = 15) -> pd.DataFrame:
    df = df.copy()
    df['orb_high'] = float('nan')
    df['orb_low']  = float('nan')

    for date, day_df in df.groupby(df.index.date):
        open_time = pd.Timestamp(f"{date} {MARKET_OPEN}", tz=day_df.index.tz)
        end_time  = open_time + pd.Timedelta(minutes=orb_minutes)

        orb_candles = day_df[(day_df.index >= open_time) & (day_df.index <= end_time)]
        if orb_candles.empty:
            continue

        orb_high = orb_candles['High'].max()
        orb_low  = orb_candles['Low'].min()

        after_orb = day_df[day_df.index > end_time]
        df.loc[after_orb.index, 'orb_high'] = orb_high
        df.loc[after_orb.index, 'orb_low']  = orb_low

    return df