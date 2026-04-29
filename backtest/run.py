from backtesting import Backtest, Strategy
from backtesting.lib import crossover
import pandas as pd
from data.fetcher import fetch_data
from strategy.orb import compute_orb

class ORBStrategy(Strategy):
    orb_minutes = 15
    risk_pct    = 0.01   # 1% per trade
    rr_ratio    = 2.0

    def init(self):
        pass

    def next(self):
        price    = self.data.Close[-1]
        orb_high = self.data.orb_high[-1]
        orb_low  = self.data.orb_low[-1]

        if pd.isna(orb_high) or self.position:
            return

        if price > orb_high:
            sl = orb_low
            tp = price + self.rr_ratio * (price - sl)
            self.buy(sl=sl, tp=tp)

        elif price < orb_low:
            sl = orb_high
            tp = price - self.rr_ratio * (sl - price)
            self.sell(sl=sl, tp=tp)

df = fetch_data("RELIANCE.NS", period="30d", interval="5m")
df = compute_orb(df, orb_minutes=15)

bt = Backtest(df, ORBStrategy, cash=50000, commission=0.0002)
stats = bt.run()

print(stats)
bt.plot()