import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Scalp PRO v4.3 - Full List", layout="wide")

# --- 1. ОТРИМАННЯ ВСІХ ТИКЕРІВ З BINANCE FUTURES ---
@st.cache_data(ttl=3600)
def get_binance_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # Беремо лише USDT пари, які активно торгуються
            symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
            return sorted(symbols)
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# --- 2. ДАНІ ДЛЯ СВІЧОК (Binance API - тепер без блокувань для OHLC) ---
def get_binance_ohlc(symbol, timeframe):
    # Мапимо таймфрейми під Binance API
    tf_map = {"5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {'symbol': symbol, 'interval': tf_map.get(timeframe, "15m"), 'limit': 100}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json(), columns=[
                'time', 'open', 'high', 'low', 'close', 'volume', 
                'close_time', 'qav', 'num_trades', 'taker_base', 'taker_quote', 'ignore'
            ])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            for col in ['open', 'high', 'low', 'close']:
                df[col] = df[col].astype(float)
            return df
        return None
    except: return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("🐳 Full Futures Scalp")

all_tickers = get_binance_futures_symbols()
target_ticker = st.sidebar.selectbox("🔍 Пошук (всі ф'ючерси Binance)", all_tickers, index=all_tickers.index("BTCUSDT") if "BTCUSDT" in all_tickers else 0)

tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d", "1w"], index=1, horizontal=True)

tab1, tab2 = st.tabs(["📊 TradingView (Live)", "🕯️ Scalp Candles + Pivot Levels"])

with tab1:
    tv_tf = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D", "1w": "W"}[tf]
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_ticker}PERP&interval={tv_tf}&theme=dark" 
        width="100%" height="700" frameborder="0"></iframe>
    """, unsafe_allow_html=True)

with tab2:
    st.subheader(f"🕯️ {target_ticker} - Аналіз ({tf})")
    ohlc = get_binance_ohlc(target_ticker, tf)
    
    if ohlc is not None:
        # Розрахунок рівнів на основі останніх 100 свічок
        last_h = ohlc['high'].max()
        last_l = ohlc['low'].min()
        last_c = ohlc['close'].iloc[-1]
        
        pivot = (last_h + last_l + last_c) / 3
        levels = {
            "R2 (Max Range)": pivot + (last_h - last_l),
            "R1 (Resistance)": (2 * pivot) - last_l,
            "S1 (Support)": (2 * pivot) - last_h,
            "S2 (Min Range)": pivot - (last_h - last_l)
        }

        fig = go.Figure(data=[go.Candlestick(
            x=ohlc['time'], open=ohlc['open'], high=ohlc['high'],
            low=ohlc['low'], close=ohlc['close'], name=target_ticker
        )])

        for name, val in levels.items():
            color = "rgba(255, 70, 70, 0.7)" if "R" in name else "rgba(70, 255, 70, 0.7)"
            fig.add_hline(y=val, line_dash="dash", line_color=color, annotation_text=name)

        fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Не вдалося завантажити свічки для цієї пари. Спробуйте іншу.")

st.sidebar.markdown(f"✅ Всього знайдено монет: **{len(all_tickers)}**")
time.sleep(60)
st.rerun()
