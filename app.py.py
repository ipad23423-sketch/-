import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="PRO Scalp Terminal v4.1", layout="wide")

# --- ОТРИМАННЯ ДАНИХ ---
@st.cache_data(ttl=60)
def get_global_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 100, 'page': 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else None
    except: return None

def get_ohlc_data(coin_id, timeframe):
    # Визначаємо кількість днів залежно від обраного таймфрейму
    # CoinGecko повертає: 1-2 дні = 30хв свічки, 7-30 днів = 4год свічки і т.д.
    days_map = {
        "5m": "1", "15m": "1", "1h": "1", 
        "4h": "7", "1d": "30", "1w": "max"
    }
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {'vs_currency': 'usd', 'days': days_map.get(timeframe, "1")}
    
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json(), columns=['time', 'open', 'high', 'low', 'close'])
            df['time'] = pd.to_datetime(df['time'], unit='ms')
            return df
        return None
    except: return None

# --- ІНТЕРФЕЙС ---
df_market = get_global_data()

if df_market is not None:
    st.sidebar.title("💎 Scalp PRO 4.1")
    coin_choice = st.sidebar.selectbox("Оберіть актив", df_market['name'].tolist())
    coin_row = df_market[df_market['name'] == coin_choice].iloc[0]
    target_tv = coin_row['symbol'].upper() + "USDT"

    # Вибір таймфрейму (новий віджет)
    tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d", "1w"], index=2, horizontal=True)

    tab1, tab2 = st.tabs(["📊 TradingView (Full)", "🕯️ Scalp Candlestick (Custom)"])

    with tab1:
        # Для TradingView ми просто передаємо інтервал (1, 15, 60, D, W)
        tv_intervals = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D", "1w": "W"}
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_tv}&interval={tv_intervals[tf]}&theme=dark" 
            width="100%" height="650" frameborder="0"></iframe>
        """, unsafe_allow_html=True)

    with tab2:
        st.subheader(f"🕯️ {coin_choice} - {tf} Chart")
        ohlc_df = get_ohlc_data(coin_row['id'], tf)
        
        if ohlc_df is not None:
            # Розрахунок рівнів
            h, l, c = coin_row['high_24h'], coin_row['low_24h'], coin_row['current_price']
            pivot = (h + l + c) / 3
            levels = {
                "R2": pivot + (h - l), "R1": (2 * pivot) - l,
                "S1": (2 * pivot) - h, "S2": pivot - (h - l)
            }

            fig = go.Figure(data=[go.Candlestick(
                x=ohlc_df['time'], open=ohlc_df['open'], high=ohlc_df['high'],
                low=ohlc_df['low'], close=ohlc_df['close'], name='Price'
            )])

            for name, val in levels.items():
                color = "red" if "R" in name else "green"
                fig.add_hline(y=val, line_dash="dash", line_color=color, annotation_text=name)

            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Дані для цього таймфрейму завантажуються...")

else:
    st.error("Помилка маркет-даних.")

time.sleep(60)
st.rerun()
