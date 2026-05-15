import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Crypto Intellect Pro", layout="wide")

# Функція отримання даних з обробкою помилок
def get_crypto_data():
    # Пробуємо основний та резервний шлях
    urls = [
        "https://api.binance.com/api/v3/ticker/24hr",
        "https://api1.binance.com/api/v3/ticker/24hr"
    ]
    for url in urls:
        try:
            res = requests.get(url, timeout=5)
            if res.status_code == 200:
                df = pd.DataFrame(res.json())
                df = df[df['symbol'].endswith('USDT')]
                cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
                df[cols] = df[cols].astype(float)
                return df
        except:
            continue
    return pd.DataFrame()

# Сайдбар
st.sidebar.title("💎 Контроль")
search = st.sidebar.text_input("🔍 Пошук (напр. BTC)", "").upper()
min_vol = st.sidebar.number_input("Мін. Об'єм ($)", value=0)

# Основна логіка
df = get_crypto_data()

if not df.empty:
    # Фільтрація
    d_df = df[df['quoteVolume'] >= min_vol]
    if search:
        d_df = d_df[d_df['symbol'].str.contains(search)]

    all_symbols = d_df['symbol'].tolist()

    tab1, tab2 = st.tabs(["📊 Графік та Аналіз", "🆕 Нові Лістинги"])

    with tab1:
        col_c, col_s = st.columns([3, 1])
        
        with col_c:
            if all_symbols:
                target = st.selectbox("🎯 Оберіть актив", all_symbols)
                
                # Розрахунок рівнів
                c_info = df[df['symbol'] == target].iloc[0]
                pivot = (c_info['highPrice'] + c_info['lowPrice'] + c_info['lastPrice']) / 3
                res = 2 * pivot - c_info['lowPrice']
                sup = 2 * pivot - c_info['highPrice']

                # Графік
                st.markdown(f"""
                    <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark&style=1" 
                            width="100%" height="550" frameborder="0"></iframe>
                """, unsafe_allow_html=True)
                st.info(f"📍 **Авто-рівні:** Опір: `{res:.4f}` | Підтримка: `{sup:.4f}`")
            else:
                st.warning("Монет не знайдено.")

        with col_s:
            st.subheader("🚀 Топ 24г")
            top = d_df.sort_values(by="priceChangePercent", ascending=False).head(10)
            for _, r in top.iterrows():
                st.write(f"**{r['symbol'].replace('USDT','')}**: {r['priceChangePercent']:+.2f}%")

    with tab2:
        st.subheader("📅 Останні додані пари (Умовно)")
        # Сортуємо за найменшим об'ємом або специфічними тикерами для демонстрації
        st.write("Тут відображаються нові активи на біржі.")
        st.dataframe(d_df.tail(10)[['symbol', 'lastPrice', 'quoteVolume']])

    st.markdown("---")
    st.subheader("📋 Всі монети USDT")
    st.dataframe(d_df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']], use_container_width=True)

else:
    st.error("Тимчасова помилка зв'язку з Binance. Спробуйте оновити сторінку через 30 секунд.")

time.sleep(20)
