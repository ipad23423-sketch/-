import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="Scalp PRO v4.2", layout="wide")

# --- ОТРИМАННЯ ВСІХ МОНЕТ (CoinGecko Market) ---
@st.cache_data(ttl=300)
def get_all_coins():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 250, 'page': 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # Створюємо зрозумілий тикер як на Binance
            df['ticker'] = df['symbol'].str.upper() + "USDT"
            return df
        return None
    except: return None

def get_ohlc_data(coin_id, timeframe):
    days_map = {"5m": "1", "15m": "1", "1h": "1", "4h": "7", "1d": "30", "1w": "max"}
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
st.sidebar.title("💎 Scalp Futures Finder")
df_market = get_all_coins()

if df_market is not None:
    # Пошук по тикеру (наприклад, EDENUSDT)
    ticker_list = sorted(df_market['ticker'].tolist())
    target_ticker = st.sidebar.selectbox("🔍 Пошук монети (напр. EDENUSDT)", ticker_list, index=ticker_list.index("BTCUSDT") if "BTCUSDT" in ticker_list else 0)
    
    # Знаходимо дані обраної монети
    coin_row = df_market[df_market['ticker'] == target_ticker].iloc[0]
    
    # Таймфрейми
    tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h", "1d", "1w"], index=1, horizontal=True)

    tab1, tab2 = st.tabs(["📊 TradingView (Binance)", "🕯️ Custom Candlestick + Levels"])

    with tab1:
        # Конвертуємо таймфрейм для TradingView
        tv_tf = {"5m": "5", "15m": "15", "1h": "60", "4h": "240", "1d": "D", "1w": "W"}[tf]
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_ticker}PERP&interval={tv_tf}&theme=dark" 
            width="100%" height="700" frameborder="0"></iframe>
        """, unsafe_allow_html=True)

    with tab2:
        st.subheader(f"🕯️ {target_ticker} - Аналіз рівнів ({tf})")
        ohlc = get_ohlc_data(coin_row['id'], tf)
        
        if ohlc is not None:
            # Математика рівнів (Pivot)
            h, l, c = coin_row['high_24h'], coin_row['low_24h'], coin_row['current_price']
            pivot = (h + l + c) / 3
            levels = {"R2": pivot+(h-l), "R1": (2*pivot)-l, "S1": (2*pivot)-h, "S2": pivot-(h-l)}

            fig = go.Figure(data=[go.Candlestick(
                x=ohlc['time'], open=ohlc['open'], high=ohlc['high'],
                low=ohlc['low'], close=ohlc['close'], name=target_ticker
            )])

            for name, val in levels.items():
                color = "rgba(255, 70, 70, 0.8)" if "R" in name else "rgba(70, 255, 70, 0.8)"
                fig.add_hline(y=val, line_dash="dash", line_color=color, annotation_text=name)

            fig.update_layout(template="plotly_dark", height=700, xaxis_rangeslider_visible=False)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Завантаження свічок... Спробуйте оновити через 5 секунд.")
else:
    st.error("Не вдалося підключитися до бази монет.")

time.sleep(60)
st.rerun()
