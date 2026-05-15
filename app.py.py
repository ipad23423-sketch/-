import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="PRO Scalp Terminal", layout="wide")

# --- ОТРИМАННЯ ДАНИХ ---
@st.cache_data(ttl=60)
def get_global_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 100, 'page': 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df['tv_symbol'] = df['symbol'].str.upper() + "USDT"
            return df
        return None
    except:
        return None

# --- РОЗРАХУНОК РІВНІВ ---
def calculate_levels(coin):
    h, l, c = coin['high_24h'], coin['low_24h'], coin['current_price']
    pivot = (h + l + c) / 3
    return {
        "Resistance 2": pivot + (h - l),
        "Resistance 1": (2 * pivot) - l,
        "Pivot Point": pivot,
        "Support 1": (2 * pivot) - h,
        "Support 2": pivot - (h - l)
    }

# --- ІНТЕРФЕЙС ---
df = get_global_data()

if df is not None:
    st.sidebar.title("💎 Scalp PRO")
    target = st.sidebar.selectbox("Оберіть актив", df['tv_symbol'].tolist())
    coin_data = df[df['tv_symbol'] == target].iloc[0]

    tab1, tab2 = st.tabs(["📊 Головна", "🎯 Скальпінг рівні"])

    with tab1:
        col_main, col_list = st.columns([3, 1])
        with col_main:
            st.markdown(f"""
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark" 
                width="100%" height="600" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
        with col_list:
            st.write("🔥 Топ за об'ємом")
            st.dataframe(df[['symbol', 'total_volume']].head(20), hide_index=True)

    with tab2:
        levels = calculate_levels(coin_data)
        fig = go.Figure()
        
        # Поточна ціна
        curr_p = coin_data['current_price']
        fig.add_trace(go.Scatter(x=[0, 1], y=[curr_p, curr_p], name="Ціна", line=dict(color='white', dash='dot')))
        
        # Малюємо рівні
        for name, val in levels.items():
            color = "red" if "Resistance" in name else "green" if "Support" in name else "gray"
            fig.add_trace(go.Scatter(x=[0, 1], y=[val, val], mode="lines+text", 
                                     text=[name], textposition="top center",
                                     line=dict(color=color, width=2)))

        fig.update_layout(template="plotly_dark", height=600, showlegend=False, xaxis_visible=False)
        st.plotly_chart(fig, use_container_width=True)
        st.success(f"Рівні для {target} оновлено. Використовуй S1/S2 для відскоку вгору!")

else:
    st.error("Помилка завантаження. Перевір інтернет або requirements.txt")

time.sleep(60)
st.rerun()
