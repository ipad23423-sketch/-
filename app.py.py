import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="PRO Scalp Terminal v4.0", layout="wide")

# --- ОТРИМАННЯ ДАНИХ ТА СВІЧОК ---
@st.cache_data(ttl=60)
def get_global_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 100, 'page': 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        return pd.DataFrame(res.json()) if res.status_code == 200 else None
    except: return None

def get_ohlc_data(coin_id):
    # Отримуємо свічки за останні 1-2 дні
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/ohlc"
    params = {'vs_currency': 'usd', 'days': '1'}
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
    st.sidebar.title("💎 Scalp PRO 4.0")
    # Вибір монети по її ID (потрібно для OHLC)
    coin_choice = st.sidebar.selectbox("Оберіть актив", df_market['name'].tolist())
    coin_row = df_market[df_market['name'] == coin_choice].iloc[0]
    target_tv = coin_row['symbol'].upper() + "USDT"

    tab1, tab2 = st.tabs(["📊 Головна (TradingView)", "🕯️ Свічний графік + Рівні"])

    with tab1:
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_tv}&interval=15&theme=dark" 
            width="100%" height="650" frameborder="0"></iframe>
        """, unsafe_allow_html=True)

    with tab2:
        st.subheader(f"🕯️ Scalp Chart: {coin_choice}")
        ohlc_df = get_ohlc_data(coin_row['id'])
        
        if ohlc_df is not None:
            # Розрахунок рівнів на основі останніх даних
            h, l, c = coin_row['high_24h'], coin_row['low_24h'], coin_row['current_price']
            pivot = (h + l + c) / 3
            levels = {
                "Resistance 2": pivot + (h - l),
                "Resistance 1": (2 * pivot) - l,
                "Support 1": (2 * pivot) - h,
                "Support 2": pivot - (h - l)
            }

            # Створюємо свічний графік
            fig = go.Figure(data=[go.Candlestick(
                x=ohlc_df['time'],
                open=ohlc_df['open'], high=ohlc_df['high'],
                low=ohlc_df['low'], close=ohlc_df['close'],
                name='Свічки'
            )])

            # Додаємо рівні як горизонтальні лінії
            for name, val in levels.items():
                line_color = "rgba(255, 0, 0, 0.6)" if "Resistance" in name else "rgba(0, 255, 0, 0.6)"
                fig.add_hline(y=val, line_dash="dash", line_color=line_color, 
                              annotation_text=name, annotation_position="top left")

            fig.update_layout(
                template="plotly_dark",
                height=700,
                xaxis_rangeslider_visible=False,
                yaxis_title="Ціна (USD)"
            )
            st.plotly_chart(fig, use_container_width=True)
            st.info("💡 Зелені пунктирні лінії — зони підтримки, червоні — спротиву.")
        else:
            st.warning("Не вдалося завантажити свічкові дані. Спробуйте іншу монету.")

else:
    st.error("Помилка завантаження маркет-даних.")

time.sleep(60)
st.rerun()
