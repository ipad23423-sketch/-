import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Scalp PRO v4.4 - ALL COINS", layout="wide")

# --- 1. ПОВНИЙ СПИСОК Ф'ЮЧЕРСІВ (БЕЗ ОБМЕЖЕНЬ) ---
def get_binance_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        res = requests.get(url, timeout=15)
        if res.status_code == 200:
            data = res.json()
            # Фільтруємо: тільки USDT, тільки ті, що торгуються, і прибираємо індекси (якщо є)
            symbols = [
                s['symbol'] for s in data['symbols'] 
                if s['quoteAsset'] == 'USDT' 
                and s['status'] == 'TRADING'
                and s['contractType'] == 'PERPETUAL'
            ]
            return sorted(symbols)
        return []
    except Exception as e:
        st.error(f"Помилка API: {e}")
        return []

# --- 2. ОТРИМАННЯ СВІЧОК ---
def get_binance_ohlc(symbol, timeframe):
    tf_map = {"5m": "5m", "15m": "15m", "1h": "1h", "4h": "4h", "1d": "1d", "1w": "1w"}
    url = "https://fapi.binance.com/fapi/v1/klines"
    params = {'symbol': symbol, 'interval': tf_map.get(timeframe, "15m"), 'limit': 150}
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

# --- ГОЛОВНА ЛОГІКА ---
all_tickers = get_binance_futures_symbols()

if all_tickers:
    st.sidebar.title(f"🚀 Трейдинг ({len(all_tickers)} пар)")
    
    # Вибір монети з повного списку
    target_ticker = st.sidebar.selectbox("🔍 Пошук монети", all_tickers, index=all_tickers.index("BTCUSDT") if "BTCUSDT" in all_tickers else 0)
    
    tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d", "1w"], index=1, horizontal=True)

    tab1, tab2 = st.tabs(["📊 TradingView Live", "🎯 Scalp Levels (Pivot)"])

    with tab1:
        tv_tf = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D", "1w": "W"}[tf]
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_ticker}PERP&interval={tv_tf}&theme=dark" 
            width="100%" height="750" frameborder="0"></iframe>
        """, unsafe_allow_html=True)

    with tab2:
        ohlc = get_binance_ohlc(target_ticker, tf)
        if ohlc is not None:
            # Pivot Points за останні свічки
            h, l, c = ohlc['high'].max(), ohlc['low'].min(), ohlc['close'].iloc[-1]
            p = (h + l + c) / 3
            levels = {"R2": p+(h-l), "R1": (2*p)-l, "S1": (2*p)-h, "S2": p-(h-l)}

            fig = go.Figure(data=[go.Candlestick(
                x=ohlc['time'], open=ohlc['open'], high=ohlc['high'],
                low=ohlc['low'], close=ohlc['close']
            )])

            for name, val in levels.items():
                clr = "red" if "R" in name else "green"
                fig.add_hline(y=val, line_dash="dash", line_color=clr, annotation_text=name)

            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("Не вдалося підтягнути дані свічок.")
else:
    st.warning("⚠️ Список монет пустий. Перевіряємо зв'язок з Binance...")
    if st.button("Оновити список"):
        st.rerun()

time.sleep(60)
st.rerun()
