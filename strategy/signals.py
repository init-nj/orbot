import pandas as pd
def generate_signals(df):
    df = df.copy()
    df['signal'] = None
    df['signal_triggered'] = False

    for date, day_df in df.groupby(df.index.date):
        triggered = False
        for idx, row in day_df.iterrows():
            if pd.isna(row['orb_high']) or triggered:
                continue
            if row['Close'] > row['orb_high']:
                df.at[idx, 'signal'] = 'BUY'
                df.at[idx, 'signal_triggered'] = True
                triggered = True
            elif row['Close'] < row['orb_low']:
                df.at[idx, 'signal'] = 'SELL'
                df.at[idx, 'signal_triggered'] = True
                triggered = True

    return df
