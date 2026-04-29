import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ORB Trading - Open Range Break",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Syne:wght@400;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Syne', sans-serif; }

.stApp { background: #0d0f12; }

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111318 !important;
    border-right: 1px solid #1e2128;
}
section[data-testid="stSidebar"] * { color: #c8cdd8 !important; }
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label { color: #6b7280 !important; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }

/* Metric cards */
[data-testid="metric-container"] {
    background: #111318;
    border: 1px solid #1e2128;
    border-radius: 10px;
    padding: 1rem 1.25rem;
}
[data-testid="metric-container"] label { color: #6b7280 !important; font-size: 11px; letter-spacing: 0.08em; text-transform: uppercase; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 1.6rem !important; color: #e8eaf0 !important; }
[data-testid="stMetricDelta"] { font-family: 'JetBrains Mono', monospace !important; }

/* Buttons */
.stButton > button {
    background: #1a73e8 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Syne', sans-serif !important;
    font-weight: 600 !important;
    letter-spacing: 0.04em;
    padding: 0.5rem 1.5rem !important;
    width: 100%;
}
.stButton > button:hover { background: #1557b0 !important; }

/* Headings */
h1, h2, h3 { color: #e8eaf0 !important; font-family: 'Syne', sans-serif !important; }

/* Dataframe */
[data-testid="stDataFrame"] { border: 1px solid #1e2128 !important; border-radius: 10px; overflow: hidden; }

/* Divider */
hr { border-color: #1e2128 !important; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] { background: #111318; border-radius: 10px; padding: 4px; gap: 4px; }
.stTabs [data-baseweb="tab"] { background: transparent; color: #6b7280 !important; border-radius: 8px; font-family: 'Syne', sans-serif; }
.stTabs [aria-selected="true"] { background: #1e2128 !important; color: #e8eaf0 !important; }

/* Status pills */
.pill-win  { background:#0f2d1a; color:#34d399; padding:2px 10px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:12px; }
.pill-loss { background:#2d0f0f; color:#f87171; padding:2px 10px; border-radius:20px; font-family:'JetBrains Mono',monospace; font-size:12px; }
</style>
""", unsafe_allow_html=True)


# ── Helper functions ───────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(ticker, period=period, interval=interval, progress=False)
    if df.empty:
        return pd.DataFrame()
    df.index = pd.to_datetime(df.index)
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert("Asia/Kolkata")
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    df.dropna(inplace=True)
    return df


def compute_orb(df: pd.DataFrame, orb_minutes: int, market_open: str) -> pd.DataFrame:
    df = df.copy()
    df['orb_high'] = np.nan
    df['orb_low']  = np.nan
    for date, day_df in df.groupby(df.index.date):
        open_time = pd.Timestamp(f"{date} {market_open}", tz=day_df.index.tz)
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


def run_paper_trade(df: pd.DataFrame, capital: float, risk_pct: float, rr_ratio: float):
    trades = []
    equity = [capital]
    current_equity = capital

    for date, day_df in df.groupby(df.index.date):
        position = None
        for idx, row in day_df.iterrows():
            if pd.isna(row['orb_high']):
                continue
            if position is None:
                if row['Close'] > row['orb_high']:
                    sl = row['orb_low']
                    tp = row['Close'] + rr_ratio * (row['Close'] - sl)
                    risk_amt = current_equity * risk_pct
                    qty = max(1, int(risk_amt / abs(row['Close'] - sl))) if abs(row['Close'] - sl) > 0 else 1
                    position = dict(side='BUY', entry=row['Close'], sl=sl, tp=tp,
                                    qty=qty, entry_time=idx, orb_high=row['orb_high'], orb_low=row['orb_low'])
                elif row['Close'] < row['orb_low']:
                    sl = row['orb_high']
                    tp = row['Close'] - rr_ratio * (sl - row['Close'])
                    risk_amt = current_equity * risk_pct
                    qty = max(1, int(risk_amt / abs(row['Close'] - sl))) if abs(row['Close'] - sl) > 0 else 1
                    position = dict(side='SELL', entry=row['Close'], sl=sl, tp=tp,
                                    qty=qty, entry_time=idx, orb_high=row['orb_high'], orb_low=row['orb_low'])
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
                    current_equity += pnl
                    trades.append({**position, 'exit': exit_price, 'exit_time': idx,
                                   'reason': exit_reason, 'pnl': round(pnl, 2),
                                   'equity': round(current_equity, 2)})
                    equity.append(current_equity)
                    position = None
    return pd.DataFrame(trades), equity


def build_chart(df: pd.DataFrame, trades_df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.75, 0.25],
        vertical_spacing=0.03,
    )

    # Candlestick
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        increasing_line_color='#34d399', decreasing_line_color='#f87171',
        increasing_fillcolor='#34d399', decreasing_fillcolor='#f87171',
        name=ticker, line_width=1,
    ), row=1, col=1)

    # ORB lines
    for date, day_df in df.groupby(df.index.date):
        orb_slice = day_df.dropna(subset=['orb_high', 'orb_low'])
        if orb_slice.empty:
            continue
        orb_h = orb_slice['orb_high'].iloc[0]
        orb_l = orb_slice['orb_low'].iloc[0]
        x0, x1 = orb_slice.index[0], orb_slice.index[-1]
        fig.add_shape(type='line', x0=x0, x1=x1, y0=orb_h, y1=orb_h,
                      line=dict(color='#60a5fa', width=1, dash='dot'), row=1, col=1)
        fig.add_shape(type='line', x0=x0, x1=x1, y0=orb_l, y1=orb_l,
                      line=dict(color='#fb923c', width=1, dash='dot'), row=1, col=1)

    # Trade markers
    if not trades_df.empty:
        buys  = trades_df[trades_df['side'] == 'BUY']
        sells = trades_df[trades_df['side'] == 'SELL']
        if not buys.empty:
            fig.add_trace(go.Scatter(
                x=buys['entry_time'], y=buys['entry'],
                mode='markers', marker=dict(symbol='triangle-up', color='#34d399', size=10),
                name='Buy entry',
            ), row=1, col=1)
        if not sells.empty:
            fig.add_trace(go.Scatter(
                x=sells['entry_time'], y=sells['entry'],
                mode='markers', marker=dict(symbol='triangle-down', color='#f87171', size=10),
                name='Sell entry',
            ), row=1, col=1)

    # Volume bars
    colors = ['#34d399' if c >= o else '#f87171'
              for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=colors, opacity=0.5, name='Volume',
    ), row=2, col=1)

    fig.update_layout(
        paper_bgcolor='#0d0f12', plot_bgcolor='#0d0f12',
        font=dict(family='JetBrains Mono', color='#6b7280', size=11),
        xaxis_rangeslider_visible=False,
        legend=dict(bgcolor='#111318', bordercolor='#1e2128', borderwidth=1),
        margin=dict(l=0, r=0, t=10, b=0),
        height=520,
    )
    for axis in ['xaxis', 'yaxis', 'xaxis2', 'yaxis2']:
        fig.update_layout(**{axis: dict(
            gridcolor='#1e2128', zerolinecolor='#1e2128',
            tickfont=dict(color='#6b7280'),
        )})
    return fig


def build_equity_chart(equity: list, capital: float) -> go.Figure:
    fig = go.Figure()
    x = list(range(len(equity)))
    fig.add_trace(go.Scatter(
        x=x, y=equity,
        fill='tozeroy',
        fillcolor='rgba(26,115,232,0.08)',
        line=dict(color='#1a73e8', width=2),
        name='Equity',
    ))
    fig.add_hline(y=capital, line=dict(color='#6b7280', dash='dot', width=1))
    fig.update_layout(
        paper_bgcolor='#0d0f12', plot_bgcolor='#0d0f12',
        font=dict(family='JetBrains Mono', color='#6b7280', size=11),
        margin=dict(l=0, r=0, t=10, b=0),
        height=220,
        showlegend=False,
        xaxis=dict(gridcolor='#1e2128', zerolinecolor='#1e2128', tickfont=dict(color='#6b7280')),
        yaxis=dict(gridcolor='#1e2128', zerolinecolor='#1e2128', tickfont=dict(color='#6b7280')),
    )
    return fig


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("## ⚡ ORB Bot")
    st.markdown("<p style='color:#6b7280;font-size:12px;margin-top:-12px;'>Opening Range Breakout</p>", unsafe_allow_html=True)
    st.divider()

    st.markdown("**Instrument**")
    market = st.selectbox("Market", ["NSE (India)", "US Stocks", "Crypto"], label_visibility="collapsed")
    ticker_presets = {
        "NSE (India)":  ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "NIFTY50=F", "Custom"],
        "US Stocks":    ["AAPL", "TSLA", "NVDA", "MSFT", "SPY", "Custom"],
        "Crypto":       ["BTC-USD", "ETH-USD", "SOL-USD", "Custom"],
    }
    market_open_defaults = {"NSE (India)": "09:15", "US Stocks": "09:30", "Crypto": "00:00"}

    ticker_choice = st.selectbox("Ticker", ticker_presets[market])
    if ticker_choice == "Custom":
        ticker = st.text_input("Enter ticker symbol", "RELIANCE.NS")
    else:
        ticker = ticker_choice

    st.divider()
    st.markdown("**Data**")
    period_map = {"5 days": "5d", "15 days": "15d", "30 days": "30d", "60 days": "60d"}
    period_label = st.select_slider("Period", options=list(period_map.keys()), value="30 days")
    period = period_map[period_label]

    interval_map = {"1 min": "1m", "5 min": "5m", "15 min": "15m"}
    interval_label = st.selectbox("Candle interval", list(interval_map.keys()), index=1)
    interval = interval_map[interval_label]

    st.divider()
    st.markdown("**Strategy**")
    orb_minutes  = st.slider("Opening range (minutes)", 5, 60, 15, step=5)
    market_open  = st.text_input("Market open time", market_open_defaults[market])

    st.divider()
    st.markdown("**Risk**")
    capital  = st.number_input("Starting capital (₹)", value=50000, step=5000)
    risk_pct = st.slider("Risk per trade (%)", 0.5, 3.0, 1.0, step=0.5) / 100
    rr_ratio = st.slider("Risk : Reward ratio", 1.0, 4.0, 2.0, step=0.5)

    st.divider()
    run_btn = st.button("▶  Run simulation")


# ── Main area ──────────────────────────────────────────────────────────────────

st.markdown("# Opening Range Breakout")
st.markdown(f"<p style='color:#6b7280;margin-top:-16px;font-size:13px;'>Paper trading simulation · {ticker} · {period_label} · {orb_minutes}-min ORB</p>", unsafe_allow_html=True)

if not run_btn:
    st.markdown("""
    <div style='background:#111318;border:1px solid #1e2128;border-radius:12px;padding:2.5rem;text-align:center;margin-top:2rem;'>
        <p style='color:#6b7280;font-size:14px;'>Configure parameters in the sidebar and press <strong style="color:#e8eaf0">▶ Run simulation</strong> to begin.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# Run pipeline
with st.spinner("Fetching data..."):
    df = fetch_data(ticker, period, interval)

if df.empty:
    st.error(f"No data returned for **{ticker}**. Try a different ticker or period.")
    st.stop()

with st.spinner("Computing ORB levels..."):
    df = compute_orb(df, orb_minutes, market_open)

with st.spinner("Running paper trades..."):
    trades_df, equity_curve = run_paper_trade(df, capital, risk_pct, rr_ratio)

# ── Metrics ────────────────────────────────────────────────────────────────────
total_pnl   = trades_df['pnl'].sum() if not trades_df.empty else 0
win_rate    = (trades_df['pnl'] > 0).mean() * 100 if not trades_df.empty else 0
num_trades  = len(trades_df)
final_eq    = equity_curve[-1] if equity_curve else capital
max_dd      = 0.0
if len(equity_curve) > 1:
    eq_arr  = np.array(equity_curve)
    roll_max = np.maximum.accumulate(eq_arr)
    dd       = (eq_arr - roll_max) / roll_max * 100
    max_dd   = dd.min()

avg_win  = trades_df.loc[trades_df['pnl'] > 0, 'pnl'].mean() if not trades_df.empty else 0
avg_loss = trades_df.loc[trades_df['pnl'] <= 0, 'pnl'].mean() if not trades_df.empty else 0

c1, c2, c3, c4, c5, c6 = st.columns(6)
c1.metric("Total P&L", f"₹{total_pnl:,.0f}", delta=f"{(total_pnl/capital)*100:.1f}%")
c2.metric("Win rate",  f"{win_rate:.1f}%")
c3.metric("Trades",    str(num_trades))
c4.metric("Max drawdown", f"{max_dd:.1f}%")
c5.metric("Avg win",   f"₹{avg_win:,.0f}")
c6.metric("Avg loss",  f"₹{avg_loss:,.0f}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊  Price chart", "📈  Equity curve", "📋  Trade log"])

with tab1:
    st.plotly_chart(build_chart(df, trades_df, ticker), use_container_width=True)
    st.markdown("<p style='color:#6b7280;font-size:11px;'>🔵 dotted = ORB high &nbsp;|&nbsp; 🟠 dotted = ORB low &nbsp;|&nbsp; ▲ = BUY entry &nbsp;|&nbsp; ▼ = SELL entry</p>", unsafe_allow_html=True)

with tab2:
    if len(equity_curve) > 1:
        st.plotly_chart(build_equity_chart(equity_curve, capital), use_container_width=True)
        st.markdown(f"<p style='color:#6b7280;font-size:12px;'>Started at ₹{capital:,} → ended at ₹{final_eq:,.0f}</p>", unsafe_allow_html=True)
    else:
        st.info("No trades executed — equity curve unavailable.")

with tab3:
    if trades_df.empty:
        st.info("No trades were triggered in this period. Try a longer period or different ticker.")
    else:
        display_df = trades_df[['entry_time','side','entry','exit','sl','tp','qty','reason','pnl']].copy()
        display_df['entry_time'] = display_df['entry_time'].dt.strftime('%d %b %H:%M')
        display_df.columns = ['Time', 'Side', 'Entry', 'Exit', 'SL', 'TP', 'Qty', 'Reason', 'P&L']
        numeric_cols = display_df.select_dtypes(include=[np.number]).columns
        display_df[numeric_cols] = display_df[numeric_cols].round(2)
        st.dataframe(
            display_df.style.map(
                lambda v: 'color: #34d399' if isinstance(v, (int, float)) and v > 0 else
                'color: #f87171' if isinstance(v, (int, float)) and v < 0 else '',
                subset=['P&L']
            ),
            use_container_width=True,
            hide_index=True,
        )
        csv = trades_df.to_csv(index=False).encode()
        st.download_button("⬇  Download trade log (CSV)", csv, "orb_trades.csv", "text/csv")