import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Crypto Intellect Pro", layout="wide")

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ ---
@st.cache_data(ttl=10)
def get_crypto_data():
    try:
        url = "https://api.binance.com/api/v3/ticker/24hr"
        res = requests.get(url).json()
        df = pd.DataFrame(res)
        df = df[df['symbol'].endswith('USDT')]
        # Конвертація типів
        cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice', 'openPrice']
        df[cols] = df[cols].astype(float)
        return df
    except:
        return pd.DataFrame()

# --- САЙДБАР ---
st.sidebar.title("🛠 Налаштування")
search = st.sidebar.text_input("🔍 Пошук монети", "").upper()
min_vol = st.sidebar.number_input("Мін. Об'єм ($)", value=0)

# --- ЛОГІКА РІВНІВ ---
def get_levels(row):
    # Класичні Pivot Points для визначення рівнів
    pivot = (row['highPrice'] + row['lowPrice'] + row['lastPrice']) / 3
    r1 = 2 * pivot - row['lowPrice']
    s1 = 2 * pivot - row['highPrice']
    return round(s1, 4), round(r1, 4)

df = get_crypto_data()

if not df.empty:
    # Фільтрація за об'ємом та пошуком
    display_df = df[df['quoteVolume'] >= min_vol]
    if search:
        display_df = display_df[display_df['symbol'].str.contains(search)]

    # Вибір монети
    all_coins = display_df['symbol'].tolist()
    
    col_chart, col_list = st.columns([3, 1])

    with col_chart:
        if all_coins:
            selected = st.selectbox("🎯 Оберіть актив для аналізу", all_coins)
            coin_info = df[df['symbol'] == selected].iloc[0]
            
            # Розрахунок рівнів
            sup, res = get_levels(coin_info)

            st.subheader(f"📊 Графік {selected}")
            # Професійний віджет зі свічками та малюванням
            st.markdown(f"""
                <div style="height:550px;">
                    <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{selected}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&details=true&hotlist=false" 
                            width="100%" height="550" frameborder="0" allowfullscreen></iframe>
                </div>
            """, unsafe_allow_html=True)
            
            st.info(f"📍 **Авто-рівні (Pivot):** Підтримка: `{sup}` | Опір: `{res}`")
        else:
            st.warning("Монет не знайдено за вашим запитом.")

    with col_list:
        st.subheader("🚀 Топ Росту")
        top_gain = display_df.sort_values(by="priceChangePercent", ascending=False).head(8)
        for _, r in top_gain.iterrows():
            st.success(f"**{r['symbol'].replace('USDT','')}**: {r['priceChangePercent']:+.2f}%")
        
        st.markdown("---")
        st.subheader("🧠 Психологія")
        st.caption("Ціна часто тестує рівні Pivot. Якщо закріпились вище Опору — це лонг.")

    # Таблиця всіх монет
    st.markdown("---")
    st.subheader("📋 Списки всіх USDT пар")
    st.dataframe(display_df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']].rename(columns={
        'symbol': 'Тикер', 'lastPrice': 'Ціна', 'priceChangePercent': '24г %', 'quoteVolume': 'Об\'єм ($)'
    }), use_container_width=True)

else:
    st.error("Помилка отримання даних з Binance API.")

time.sleep(15)
