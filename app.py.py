import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
import time

# Намагаємось підключити RSI, якщо бібліотека встановилася
try:
    import pandas_ta as ta
    has_ta = True
except ImportError:
    has_ta = False

st.set_page_config(page_title="Scalp PRO v4.6", layout="wide")

# --- 1. ГАРАНТОВАНЕ ОТРИМАННЯ СПИСКУ МОНЕТ ---
def get_stable_symbols():
    # Резервний список (TOP-50 ф'ючерсів), якщо API не відповість
    backup_list = [
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "ADAUSDT", "AVAXUSDT", "DOGEUSDT", "DOTUSDT", "LINKUSDT",
        "MATICUSDT", "OPUSDT", "ARBUSDT", "EDENUSDT", "HYPEUSDT", "SUIUSDT", "SEIUSDT", "TIAUSDT", "ORDIUSDT", "TRXUSDT",
        "LTCUSDT", "BCHUSDT", "ATOMUSDT", "NEARUSDT", "APTUSDT", "STXUSDT", "FILUSDT", "INJUSDT", "RNDRUSDT", "LDOUSDT"
    ]
    try:
        # Пробуємо отримати свіжий список
        res = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=3)
        if res.status_code == 200:
            api_list = [s['symbol'] for s in res.json() if s['symbol'].endswith('USDT')]
            return sorted(list(set(api_list + backup_list))) # Змішуємо для надійності
        return sorted(backup_list)
    except:
        return sorted(backup_list)

# --- 2. ОТРИМАННЯ СВІЧОК ---
def get_candles(symbol, interval):
    tf_map = {"5m":"5m", "15m":"15m", "1h":"1h", "4h":"4h", "1d":"1d"}
    # Використовуємо публічне дзеркало для обходу блокувань
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
st.sidebar.title("💎 Scalp PRO v4.6")
all_symbols = get_stable_symbols()

# Тепер selectbox ніколи не буде порожнім
target = st.sidebar.selectbox("🔍 Актив", all_symbols, index=all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0)
tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d"], index=1, horizontal=True)

tab1, tab2 = st.tabs(["📊 TradingView Live", "🎯 Аналіз (Candles & RSI)"])

with tab1:
    tv_tf = {"5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}[tf]
    st.markdown(f"""
        <div style="height:750px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval={tv_tf}&theme=dark" 
            width="100%" height="750" frameborder="0"></iframe>
        </div>
    """, unsafe_allow_html=True)

with tab2:
    df = get_candles(target, tf)
    if df is not None:
        # Розрахунок Pivot
        h, l, c = df['high'].max(), df['low'].min(), df['close'].iloc[-1]
        p = (h + l + c) / 3
        levels = {"Resistance": (2*p)-l, "Support": (2*p)-h}
        
        # Графік свічок
        fig = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name=target)])
        for name, val in levels.items():
            fig.add_hline(y=val, line_dash="dash", line_color="red" if "Res" in name else "green", annotation_text=name)
        
        fig.update_layout(template="plotly_dark", height=550, xaxis_rangeslider_visible=False, margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)

        # RSI (якщо встановлено)
        if has_ta:
            df['RSI'] = ta.rsi(df['close'], length=14)
            fig_rsi = go.Figure(go.Scatter(x=df['time'], y=df['RSI'], name="RSI", line=dict(color='#ab63fa')))
            fig_rsi.add_hline(y=70, line_dash="dot", line_color="#ff4b4b")
            fig_rsi.add_hline(y=30, line_dash="dot", line_color="#00ff41")
            fig_rsi.update_layout(template="plotly_dark", height=180, margin=dict(l=0,r=0,t=0,b=0))
            st.plotly_chart(fig_rsi, use_container_width=True)
        else:
            st.info("💡 RSI з'явиться після встановлення pandas-ta у requirements.txt")
    else:
        st.error(f"⚠️ Не вдалося отримати свічки для {target}. Спробуйте оновити сторінку.")

st.sidebar.caption(f"Статус: Online | Монет: {len(all_symbols)}")
time.sleep(60)
st.rerun()
