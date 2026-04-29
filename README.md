# orbot — Opening Range Breakout BOT

A modular algorithmic trading project that implements and backtests the **Opening Range Breakout (ORB)** strategy with a modern interactive dashboard.

---

## Overview

This project simulates an **intraday breakout strategy** where trades are taken when price breaks above or below the opening range of a trading session.

It includes:

*  Interactive Streamlit dashboard
*  Strategy logic (ORB)
* ️ Backtesting engine
*  Risk management module
*  Market data fetching (Yahoo Finance)

---

## Project Structure

```
orbot/
│
├── backtest/           # Backtesting engine
│   └── run.py
│
├── data/               # Data fetching layer
│   └── fetcher.py
│
├── strategy/           # Strategy logic
│   ├── orb.py
│   └── signals.py
│
├── risk/               # Risk management system
│   └── manager.py
│
├── notebooks/          # Research & experimentation
│   └── exploration.ipynb
│
├── dashboard.py        # Streamlit dashboard (main UI)
├── main.py             # Entry point (CLI / pipeline)
└── .venv/              # Virtual environment (ignored)
```

---

## Features

### Strategy

* Opening Range Breakout (ORB)
* Configurable opening range duration
* Buy/Sell breakout detection

### Backtesting

* Trade simulation (paper trading)
* Equity curve tracking
* P&L calculation
* Drawdown analysis

### Risk Management

* Fixed % risk per trade
* Dynamic position sizing
* Risk-to-reward ratio control

### Dashboard

* Candlestick charts (Plotly)
* ORB levels visualization
* Trade markers (Buy/Sell)
* Equity curve
* Downloadable trade logs

---

## How It Works

1. Fetch intraday market data
2. Compute ORB levels (high & low of first N minutes)
3. Generate breakout signals
4. Execute simulated trades
5. Track equity and performance metrics

---

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/your-username/orb-trading-system.git
cd orb-trading-system
```

### 2. Create virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # Linux / Mac
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Usage

### Run Dashboard

```bash
streamlit run dashboard.py
```

### Run Backtest (CLI)

```bash
python main.py
```

---

## Example Strategy Logic

* Define opening range (e.g., first 15 minutes)
* If price breaks **above ORB high → BUY**
* If price breaks **below ORB low → SELL**
* Stop Loss = opposite ORB boundary
* Take Profit = based on Risk:Reward ratio

---

## Key Metrics

* Total P&L
* Win Rate
* Max Drawdown
* Average Win / Loss
* Equity Curve

---

## Limitations

* Uses Yahoo Finance (not tick-level accurate)
* No slippage or brokerage modeling (yet)
* Not suitable for live trading without improvements

---

## Future Improvements

* Add brokerage & slippage simulation
* Live trading integration (Zerodha Kite API)
* Advanced indicators (VWAP, RSI filters)
* ML-based signal filtering
* Strategy optimization (parameter tuning)

---

## Learning Outcomes

This project demonstrates:

* Algorithmic trading fundamentals
* Backtesting system design
* Data handling with Pandas
* Financial risk management
* Dashboard development with Streamlit

---

## License

This project is for educational purposes only.
Not financial advice.

---