import streamlit as st
import requests
import pandas as pd
import time

# 1. Налаштування сторінки
st.set_page_config(page_title="PRO Screener v2.5", layout="wide")

# 2. Функція отримання даних з захистом від помилок
def fetch_binance_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data)
            # Фільтруємо лише USDT пари
            df = df[df['symbol'].endswith('USDT')]
            # Конвертуємо числа
            cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
            df[cols] = df[cols].astype(float)
            return df
        else:
            return None
    except:
        return None

# 3. Інтерфейс сайдбару
st.sidebar.title("💎 PRO Control")
search_coin = st.sidebar.text_input("🔍 Пошук (напр. SOL)", "").upper()
min_v = st.sidebar.number_input("Мін. Об'єм ($)", value=0)

# 4. Основна логіка
data_df = fetch_binance_data()

if data_df is not None:
    # Фільтрація
    filtered = data_df[data_df['quoteVolume'] >= min_v]
    if search_coin:
        filtered = filtered[filtered['symbol'].str.contains(search_coin)]

    col_main, col_stats = st.columns([3, 1])

    with col_main:
        if not filtered.empty:
            # Вибір монети для графіка
            all_list = filtered['symbol'].tolist()
            picked = st.selectbox("🎯 Оберіть монету", all_list, index=0)
            
            # Розрахунок Pivot рівнів
            c = filtered[filtered['symbol'] == picked].iloc[0]
            p = (c['highPrice'] + c['lowPrice'] + c['lastPrice']) / 3
            res = (2 * p) - c['lowPrice']
            sup = (2 * p) - c['highPrice']

            # Віджет TradingView зі свічками та малюванням
            st.markdown(f"""
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{picked}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false" 
                        width="100%" height="550" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            st.success(f"📍 **Рівні:** Опір: `{res:.4f}` | Підтримка: `{sup:.4f}`")
        else:
            st.warning("Монет не знайдено.")

    with col_stats:
        st.subheader("🔥 Top Gainers")
        top10 = filtered.sort_values(by="priceChangePercent", ascending=False).head(10)
        for _, r in top10.iterrows():
            st.write(f"**{r['symbol'].replace('USDT','')}**: `{r['priceChangePercent']:+.2f}%`")
        
        st.markdown("---")
        st.subheader("🧠 Психологія")
        st.info("Не входи в позицію на 'хайпі'. Чекай ретесту рівня підтримки.")

    # Повна таблиця знизу
    st.markdown("---")
    st.subheader("📋 Всі USDT монети")
    st.dataframe(filtered[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']].rename(columns={
        'symbol': 'Тікер', 'lastPrice': 'Ціна', 'priceChangePercent': '24г %', 'quoteVolume': 'Об\'єм'
    }), use_container_width=True)

else:
    st.error("⚠️ Помилка зв'язку з Binance. Зачекайте 30 секунд, сайт оновиться сам.")
    time.sleep(30)
    st.rerun()

# Авто-оновлення
time.sleep(60)
st.rerun()
