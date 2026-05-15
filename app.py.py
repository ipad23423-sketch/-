import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

# Налаштування широкого екрана
st.set_page_config(page_title="PRO Crypto Intellect", layout="wide")

# Оптимізоване отримання даних (з кешуванням на 20 секунд)
@st.cache_data(ttl=20)
def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df = df[df['symbol'].endswith('USDT')]
            # Перетворення числових даних
            num_cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
            df[num_cols] = df[num_cols].astype(float)
            return df
    except:
        return pd.DataFrame()

# Сайдбар
st.sidebar.title("💎 PRO Control")
search_query = st.sidebar.text_input("🔍 Пошук монети", "").upper()
min_volume = st.sidebar.number_input("Мін. Об'єм ($)", value=0, step=100000)

# Завантаження даних
df = get_data()

if not df.empty:
    # Фільтрація за пошуком та об'ємом
    filtered_df = df[df['quoteVolume'] >= min_volume]
    if search_query:
        filtered_df = filtered_df[filtered_df['symbol'].str.contains(search_query)]

    # Створюємо дві колонки: графік та список
    col_chart, col_stats = st.columns([3, 1])

    with col_chart:
        if not filtered_df.empty:
            all_symbols = filtered_df['symbol'].tolist()
            # По замовчуванню вибираємо BTC або першу зі списку
            default_index = all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0
            selected_symbol = st.selectbox("🎯 Оберіть пару для аналізу", all_symbols, index=default_index)
            
            # Розрахунок рівнів підтримки/опору (Pivot Points)
            c = df[df['symbol'] == selected_symbol].iloc[0]
            pp = (c['highPrice'] + c['lowPrice'] + c['lastPrice']) / 3
            r1 = (2 * pp) - c['lowPrice']
            s1 = (2 * pp) - c['highPrice']

            st.subheader(f"📊 Свічковий графік {selected_symbol}")
            
            # Вставка професійного графіка TradingView зі свічками
            st.markdown(f"""
                <div style="height:600px;">
                    <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{selected_symbol}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&details=true&hotlist=false&calendar=false" 
                            width="100%" height="600" frameborder="0" allowfullscreen></iframe>
                </div>
            """, unsafe_allow_html=True)
            
            # Вивід рівнів
            st.success(f"📍 **Авто-рівні:** Опір: `{r1:.4f}` | Підтримка: `{s1:.4f}`")
        else:
            st.error("За вашим запитом монет не знайдено.")

    with col_stats:
        st.subheader("🚀 Top 10 Gainers")
        top_10 = filtered_df.sort_values(by="priceChangePercent", ascending=False).head(10)
        for _, row in top_10.iterrows():
            st.write(f"**{row['symbol'].replace('USDT','')}**: `{row['priceChangePercent']:+.2f}%`")
        
        st.markdown("---")
        st.subheader("🧠 Психологія")
        st.info("Ціна часто розвертається біля рівнів Pivot. Шукай підтвердження на свічках!")

    # Повна таблиця монет знизу
    st.markdown("---")
    st.subheader("📋 Скринер всіх USDT пар")
    st.dataframe(filtered_df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']].rename(columns={
        'symbol': 'Пара', 'lastPrice': 'Ціна', 'priceChangePercent': 'Зміна 24г', 'quoteVolume': 'Об\'єм'
    }), use_container_width=True)

else:
    st.error("Помилка зв'язку з Binance API. Сервер перевантажений, спробуйте через 1 хвилину.")
    if st.button("🔄 Оновити дані вручну"):
        st.rerun()

# Автоматичне оновлення кожні 30 секунд
time.sleep(30)
st.rerun()
