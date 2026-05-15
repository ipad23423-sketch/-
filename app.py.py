import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="PRO Screener v2.6", layout="wide")

# Функція з ротацією посилань для обходу блокування
def fetch_binance_data():
    # Різні сервери Binance для стабільності
    endpoints = [
        "https://api1.binance.com/api/v3/ticker/24hr",
        "https://api2.binance.com/api/v3/ticker/24hr",
        "https://api3.binance.com/api/v3/ticker/24hr",
        "https://api.binance.com/api/v3/ticker/24hr"
    ]
    # Вибираємо випадковий сервер
    url = random.choice(endpoints)
    
    try:
        # Додаємо User-Agent, щоб виглядати як звичайний браузер
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df = df[df['symbol'].endswith('USDT')]
            cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
            df[cols] = df[cols].astype(float)
            return df
        elif response.status_code == 429:
            st.error("⚠️ Binance тимчасово обмежив доступ (Rate Limit).")
            return None
    except Exception as e:
        return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 PRO Control")
search_coin = st.sidebar.text_input("🔍 Пошук монети", "").upper()
min_v = st.sidebar.number_input("Мін. Об'єм ($)", value=0)

data_df = fetch_binance_data()

if data_df is not None:
    filtered = data_df[data_df['quoteVolume'] >= min_v]
    if search_coin:
        filtered = filtered[filtered['symbol'].str.contains(search_coin)]

    col_main, col_stats = st.columns([3, 1])

    with col_main:
        if not filtered.empty:
            all_symbols = filtered['symbol'].tolist()
            # Пріоритет на BTCUSDT
            idx = all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0
            picked = st.selectbox("🎯 Оберіть актив", all_symbols, index=idx)
            
            c = data_df[data_df['symbol'] == picked].iloc[0]
            p = (c['highPrice'] + c['lowPrice'] + c['lastPrice']) / 3
            res, sup = (2 * p) - c['lowPrice'], (2 * p) - c['highPrice']

            st.markdown(f"""
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{picked}&interval=15&theme=dark&style=1" 
                        width="100%" height="550" frameborder="0"></iframe>
            """, unsafe_allow_html=True)
            
            st.success(f"📍 **Pivot рівні:** Опір: `{res:.4f}` | Підтримка: `{sup:.4f}`")
        else:
            st.warning("Монет не знайдено.")

    with col_stats:
        st.subheader("🔥 Top Gainers")
        top10 = filtered.sort_values(by="priceChangePercent", ascending=False).head(10)
        for _, r in top10.iterrows():
            st.write(f"**{r['symbol'].replace('USDT','')}**: `{r['priceChangePercent']:+.2f}%`")

    st.markdown("---")
    st.dataframe(filtered[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume']], use_container_width=True)

else:
    st.warning("🔄 Перепідключення до Binance шлюзу... Зачекайте.")
    time.sleep(10) # Менша пауза перед повтором
    st.rerun()

# Важливо: не роби оновлення частіше ніж раз на 30-60 секунд
time.sleep(45)
st.rerun()
