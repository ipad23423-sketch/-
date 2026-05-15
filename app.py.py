import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# Спробуємо імпортувати аналітику, якщо вона встановлена
try:
    import pandas_ta as ta
    has_ta = True
except ImportError:
    has_ta = False

st.set_page_config(page_title="Scalp PRO v4.5", layout="wide")

# --- ОТРИМАННЯ СПИСКУ МОНЕТ (Резервне) ---
def get_all_futures():
    try:
        # Використовуємо спот-ендпоінт для списку, він стабільніший
        res = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=5)
        if res.status_code == 200:
            return sorted([s['symbol'] for s in res.json() if s['symbol'].endswith('USDT')])
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EDENUSDT"]

# --- ОТРИМАННЯ СВІЧОК ---
def get_candles(symbol, interval):
    tf_map = {"5m":"5m", "15m":"15m", "1h":"1h", "4h":"4h", "1d":"1d"}
    url = "https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': tf_map.get(interval, "15m"), 'limit': 100}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            df = pd.DataFrame(res.json(), columns=['time','open','high','low','close','v','ct','q','t','tb','tq','i'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            for c in ['open','high','low','close']: df[c] = df[c].astype(float)
            return df
    except: return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Scalp PRO v4.5")
all_symbols = get_all_futures()

target = st.sidebar.selectbox("🔍 Актив", all_symbols, index=all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0)
tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d"], index=1, horizontal=True)

tab1, tab2 = st.tabs(["📊 TradingView Live", "🕯️ Аналіз Рівнів"])

with tab1:
    tv_tf = {"5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}[tf]
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval={tv_tf}&theme=dark" 
        width="100%" height="750" frameborder="0"></iframe>
    """, unsafe_allow_html=True)

with tab2:
    df = get_candles(target, tf)
    if df is not None:
        # Pivot Рівні
        h, l, c = df['high'].max(), df['low'].min(), df['close'].iloc[-1]
        p = (h + l + c) / 3
        levels = {"R1": (2*p)-l, "S1": (2*p)-h}
        
        fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        for name, val in levels.items():
            fig.add_hline(y=val, line_dash="dash", line_color="red" if "R" in name else "green", annotation_text=name)
        
        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False)
        st.plotly_chart(fig, use_container_width=True)

        if has_ta:
            df['RSI'] = ta.rsi(df['close'], length=14)
            fig_rsi = go.Figure(go.Scatter(x=df['time'], y=df['RSI'], name="RSI", line=dict(color='purple')))
            fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
            fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
            fig_rsi.update_layout(template="plotly_dark", height=200)
            st.plotly_chart(fig_rsi, use_container_width=True)
        else:
            st.info("💡 Додай pandas-ta в requirements.txt, щоб побачити RSI.")
    else:
        st.warning("Чекаємо на дані від Binance...")

time.sleep(60)
st.rerun()
