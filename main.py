import pandas as pd
from data.fetcher import fetch_data
from strategy.orb import compute_orb
from risk.manager import compute_targets, position_size

CAPITAL     = 50_000
RISK_PCT    = 0.01
ORB_MINUTES = 15
TICKER      = "RELIANCE.NS"

df = fetch_data(TICKER, period="5d", interval="5m")
df = compute_orb(df, ORB_MINUTES)

trades = []
for date, day_df in df.groupby(df.index.date):
    position = None
    for idx, row in day_df.iterrows():
        if pd.isna(row['orb_high']):
            continue
        if position is None:
            if row['Close'] > row['orb_high']:
                sl, tp = compute_targets('BUY', row['Close'], row['orb_high'], row['orb_low'])
                qty    = position_size(CAPITAL, RISK_PCT, row['Close'], sl)
                position = dict(side='BUY', entry=row['Close'], sl=sl, tp=tp,
                                qty=qty, entry_time=idx)
            elif row['Close'] < row['orb_low']:
                sl, tp = compute_targets('SELL', row['Close'], row['orb_high'], row['orb_low'])
                qty    = position_size(CAPITAL, RISK_PCT, row['Close'], sl)
                position = dict(side='SELL', entry=row['Close'], sl=sl, tp=tp,
                                qty=qty, entry_time=idx)
        elif position:
            exit_reason = exit_price = None
            if position['side'] == 'BUY':
                if row['Low']  <= position['sl']: exit_reason, exit_price = 'SL', position['sl']
                if row['High'] >= position['tp']: exit_reason, exit_price = 'TP', position['tp']
            else:
                if row['High'] >= position['sl']: exit_reason, exit_price = 'SL', position['sl']
                if row['Low']  <= position['tp']: exit_reason, exit_price = 'TP', position['tp']
            if exit_reason:
                pnl = (exit_price - position['entry']) * position['qty']
                if position['side'] == 'SELL': pnl = -pnl
                trades.append({**position, 'exit': exit_price, 'exit_time': idx,
                                'reason': exit_reason, 'pnl': round(pnl, 2)})
                position = None

if trades:
    trade_df = pd.DataFrame(trades)
    print(trade_df[['side','entry','exit','reason','pnl']].to_string())
    print(f"\nTotal P&L:  ₹{trade_df['pnl'].sum():.2f}")
    print(f"Win rate:   {(trade_df['pnl'] > 0).mean()*100:.1f}%")
    print(f"Trades:     {len(trade_df)}")
    trade_df.to_csv("paper_trades.csv", index=False)
    print("\nTrade log saved to paper_trades.csv")
else:
    print("No trades triggered. Try increasing period to 30d.")
