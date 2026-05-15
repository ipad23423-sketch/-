import streamlit as st
import requests
import pandas as pd
import time
import plotly.graph_objects as go

st.set_page_config(page_title="PRO Terminal + Scalp Levels", layout="wide")

# --- ОТРИМАННЯ ДАНИХ (CoinGecko) ---
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

# --- ЛОГІКА РІВНІВ (Pivot Points) ---
def calculate_levels(coin_data):
    # Використовуємо High, Low та Price для розрахунку рівнів Pivot
    H = coin_data['high_24h']
    L = coin_data['low_24h']
    C = coin_data['current_price']
    
    pivot = (H + L + C) / 3
    r1 = 2 * pivot - L
    s1 = 2 * pivot - H
    r2 = pivot + (H - L)
    s2 = pivot - (H - L)
    
    return {
        "R2 (Стіна 2)": r2, "R1 (Спротив)": r1,
        "Pivot": pivot,
        "S1 (Підтримка)": s1, "S2 (Стіна 2)": s2
    }

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 PRO Control")
df = get_global_data()

if df is not None and not df.empty:
    df_sorted = df.sort_values('total_volume', ascending=False)
    target_tv = st.sidebar.selectbox("🎯 Оберіть монету", df_sorted['tv_symbol'].tolist(), index=0)
    coin = df[df['tv_symbol'] == target_tv].iloc[0]

    # Вкладки
    tab_main, tab_scalp = st.tabs(["📊 Головний термінал", "🎯 Scalp Levels (Рівні)"])

    with tab_main:
        # Твоя основна сторінка як у Digash
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ціна", f"${coin['current_price']}", f"{coin['price_change_percentage_24h']:.2f}%")
        m2.metric("Об'єм 24г", f"{coin['total_volume']/1e6:.1f}M$")
        
        col_l, col_r = st.columns([2.5, 1.2])
        with col_l:
            st.markdown(f"""
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_tv}&interval=15&theme=dark&style=1" 
                        width="100%" height="600" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
        with col_r:
            st.subheader("Топ об'ємів")
            st.dataframe(df_sorted[['tv_symbol', 'total_volume']].head(15), hide_index=True)

    with tab_scalp:
        st.subheader(f"🎯 Авто-рівні для скальпінгу: {target_tv}")
        levels = calculate_levels(coin)
        
        # Малюємо графік з рівнями
        fig = go.Figure()
        
        # Поточна ціна
        fig.add_trace(go.Scatter(x=[0, 1], y=[coin['current_price'], coin['current_price']], 
                                 mode="lines+text", name="Поточна ціна", 
                                 line=dict(color="white", width=4, dash="dot")))
        
        # Малюємо рівні
        colors = {"R2": "red", "R1": "orange", "Pivot": "gray", "S1": "lightgreen", "S2": "green"}
        for name, val in levels.items():
            line_color = "red" if "R" in name else "green" if "S" in name else "gray"
            fig.add_trace(go.Scatter(x=[0, 1], y=[val, val], mode="lines+text", 
                                     text=[name], textposition="top right",
                                     name=name, line=dict(color=line_color, width=2)))

        fig.update_layout(height=600, template="plotly_dark", showlegend=False,
                          yaxis_title="Ціна USD", xaxis_visible=False)
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.info("💡 Рівні розраховані на основі волатильності за останні 24 години. R1/R2 — зони для фіксації лонгів або пошуку шортів. S1/S2 — зони для покупок.")

else:
    st.error("Помилка отримання даних.")

time.sleep(60)
st.rerun()
