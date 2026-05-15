import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import time

st.set_page_config(page_title="Scalp PRO v4.5", layout="wide")

# --- 1. РЕЗЕРВНЕ ОТРИМАННЯ ВСІХ МОНЕТ ---
def get_all_futures():
    # Використовуємо dapi для перевірки списку, якщо fapi лежить
    endpoints = [
        "https://fapi.binance.com/fapi/v1/ticker/price",
        "https://api.binance.com/api/v3/ticker/price"
    ]
    for url in endpoints:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                data = res.json()
                symbols = [s['symbol'] for s in data if s['symbol'].endswith('USDT')]
                return sorted(symbols)
        except: continue
    return ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EDENUSDT", "HYPEUSDT"]

# --- 2. ОТРИМАННЯ СВІЧОК (З ДЗЕРКАЛА) ---
def get_candles(symbol, interval):
    # Мапимо таймфрейми
    tf_map = {"5m":"5m", "15m":"15m", "1h":"1h", "4h":"4h", "1d":"1d", "1w":"1w"}
    url = f"https://api.binance.com/api/v3/klines"
    params = {'symbol': symbol, 'interval': tf_map[interval], 'limit': 100}
    try:
        res = requests.get(url, params=params, timeout=5)
        if res.status_code == 200:
            df = pd.DataFrame(res.json(), columns=['time','open','high','low','close','vol','ct','qav','trades','tb','tq','i'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            for c in ['open','high','low','close']: df[c] = df[c].astype(float)
            return df
        return None
    except: return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Scalp PRO v4.5")
all_symbols = get_all_futures()

# Пошук активу
target = st.sidebar.selectbox("🔍 Оберіть актив (Всі пари)", all_symbols, 
                              index=all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0)

# Таймфрейм
tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d", "1w"], index=1, horizontal=True)

tab1, tab2 = st.tabs(["📊 TradingView Live", "🕯️ Свічки + Рівні + RSI"])

with tab1:
    # TradingView працює на боці клієнта, тому він завжди бачить всі монети
    tv_tf = {"5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D", "1w":"W"}[tf]
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval={tv_tf}&theme=dark" 
        width="100%" height="750" frameborder="0"></iframe>
    """, unsafe_allow_html=True)

with tab2:
    df = get_candles(target, tf)
    if df is not None:
        # Розрахунок Pivot Levels
        h, l, c = df['high'].max(), df['low'].min(), df['close'].iloc[-1]
        pivot = (h + l + c) / 3
        levels = {"R2": pivot+(h-l), "R1": (2*pivot)-l, "S1": (2*pivot)-h, "S2": pivot-(h-l)}
        
        # RSI для скальпінгу
        df['RSI'] = ta.rsi(df['close'], length=14)

        # Свічний графік
        fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'])])
        
        for name, val in levels.items():
            fig.add_hline(y=val, line_dash="dash", line_color="red" if "R" in name else "green", annotation_text=name)

        fig.update_layout(template="plotly_dark", height=600, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)
        
        # Окремий графік RSI під низом
        fig_rsi = go.Figure(go.Scatter(x=df['time'], y=df['RSI'], line=dict(color='purple')))
        fig_rsi.add_hline(y=70, line_dash="dot", line_color="red")
        fig_rsi.add_hline(y=30, line_dash="dot", line_color="green")
        fig_rsi.update_layout(template="plotly_dark", height=200, margin=dict(l=0,r=0,t=0,b=0))
        st.plotly_chart(fig_rsi, use_container_width=True)
    else:
        st.error(f"Не вдалося підтягнути свічки для {target}. Спробуйте оновити.")

st.sidebar.info(f"Знайдено монет: {len(all_symbols)}")
time.sleep(60)
st.rerun()
