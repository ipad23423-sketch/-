import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="PRO Terminal v3.7", layout="wide")

# --- ОТРИМАННЯ ДАНИХ (CoinGecko) ---
def get_global_data():
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {'vs_currency': 'usd', 'order': 'market_cap_desc', 'per_page': 100, 'page': 1}
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # Виправляємо символ для графіка (напр. btc -> BTCUSDT)
            df['tv_symbol'] = df['symbol'].str.upper() + "USDT"
            return df
        return None
    except:
        return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Global PRO Terminal")
df = get_global_data()

if df is not None and not df.empty:
    # Сортуємо за об'ємом (як у Digash)
    df_sorted = df.sort_values('total_volume', ascending=False)
    
    # Вибір монети
    target_tv = st.sidebar.selectbox("🎯 Оберіть монету", df_sorted['tv_symbol'].tolist(), index=0)
    coin = df[df['tv_symbol'] == target_tv].iloc[0]

    # Панель метрик
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Ціна", f"${coin['current_price']}", f"{coin['price_change_percentage_24h']:.2f}%")
    with m2:
        vol = coin['total_volume']
        st.metric("Об'єм 24г", f"{vol/1e9:.2f}B$" if vol >= 1e9 else f"{vol/1e6:.2f}M$")
    with m3:
        volat = ((coin['high_24h'] - coin['low_24h']) / coin['low_24h']) * 100
        st.metric("Волатильність", f"{volat:.2f}%")
    with m4:
        st.metric("Rank", f"#{coin['market_cap_rank']}")

    st.markdown("---")

    # Графік та Таблиця
    col_l, col_r = st.columns([2.5, 1.2])

    with col_l:
        # ТЕПЕР ТУТ ПРАВИЛЬНИЙ ТИКЕР
        st.markdown(f"""
            <div style="height:650px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target_tv}&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                        width="100%" height="650" frameborder="0" allowfullscreen></iframe>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.subheader("📊 Market Leaders")
        top_list = df_sorted[['tv_symbol', 'total_volume', 'price_change_percentage_24h']].head(25)
        # Форматуємо для красивої таблиці
        top_list['total_volume'] = top_list['total_volume'].apply(lambda x: f"{x/1e6:.1f}M$")
        st.dataframe(
            top_list.rename(columns={'tv_symbol': 'Монета', 'total_volume': 'Об\'єм', 'price_change_percentage_24h': '%'}), 
            hide_index=True, use_container_width=True, height=600
        )
else:
    st.error("Помилка зв'язку. Спробуйте оновити сторінку через 30 секунд.")

time.sleep(60)
st.rerun()
