import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="Crypto Intellect Ultimate", layout="wide")

# Функція з "м'яким" запитом
def fetch_data_ultra_safe():
    urls = ["https://api1.binance.com/api/v3/ticker/24hr", "https://api2.binance.com/api/v3/ticker/24hr"]
    try:
        # Додаємо випадковий хеш, щоб запит не кешувався
        r = requests.get(random.choice(urls), params={'refresh': random.random()}, timeout=10)
        if r.status_code == 200:
            df = pd.DataFrame(r.json())
            df = df[df['symbol'].endswith('USDT')]
            return df
        return None
    except:
        return None

# --- САЙДБАР ---
st.sidebar.title("🚀 Налаштування PRO")

# Ручне введення монет (якщо API лежить)
st.sidebar.subheader("📋 Мій Список (Watchlist)")
manual_list = st.sidebar.text_area("Введіть тикери через кому", "BTC,ETH,SOL,XRP,DOGE,PEPE").upper().replace(" ", "")
my_coins = [c + "USDT" if not c.endswith("USDT") else c for c in manual_list.split(",")]

# Спробуємо отримати дані для таблиці
df = fetch_data_ultra_safe()

# --- ОСНОВНА ПАНЕЛЬ ---
if df is not None:
    st.success("✅ Зв'язок з Binance встановлено! Всі 200+ індикаторів та монет доступні.")
    all_symbols = df['symbol'].tolist()
    target = st.selectbox("🎯 Оберіть монету зі списку", all_symbols, index=all_symbols.index("BTCUSDT") if "BTCUSDT" in all_symbols else 0)
else:
    st.warning("⚠️ API Binance тимчасово недоступне. Працюємо в режимі Watchlist.")
    target = st.selectbox("🎯 Ваші монети", my_coins)

# --- ГРАФІК (ЯКИЙ ЗАВЖДИ ПРАЦЮЄ) ---
col_left, col_right = st.columns([4, 1])

with col_left:
    st.markdown(f"### 📈 Графік {target}")
    # Повний функціонал TradingView: свічки, індикатори, малювання
    st.markdown(f"""
        <div style="height:650px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&details=true&hotlist=false&studies=[%22RSI@tv-basicstudies%22,%22MASimple@tv-basicstudies%22]" 
                    width="100%" height="650" frameborder="0" allowfullscreen></iframe>
        </div>
    """, unsafe_allow_html=True)

with col_right:
    st.subheader("🧠 Психологія")
    tips = [
        "Не додавай до збиткової позиції.",
        "Рівень — це зона, а не лінія.",
        "Тренд — твій друг.",
        "Забирай профіт частинами."
    ]
    st.info(random.choice(tips))
    
    if df is not None:
        st.subheader("📊 Топ 24г")
        top = df.sort_values('priceChangePercent', ascending=False).head(5)
        st.table(top[['symbol', 'priceChangePercent']])

# --- НИЖНЯ ПАНЕЛЬ (Кнопки швидкого доступу) ---
st.markdown("---")
st.subheader("🖱 Швидкий перехід")
cols = st.columns(len(my_coins[:8])) # показуємо перші 8 з вашого списку
for i, coin in enumerate(my_coins[:8]):
    if cols[i].button(coin.replace("USDT", "")):
        st.info(f"Натисніть на '{coin}' у випадаючому списку вище для оновлення графіка.")

# Пауза перед оновленням, щоб не дратувати API
time.sleep(120) 
st.rerun()
