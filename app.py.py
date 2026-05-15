import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="Ultimate Dihash LITE", layout="wide")

# Функція аналізу стакана з ротацією серверів
def get_order_book_pro(symbol):
    # Використовуємо різні шлюзи
    gateways = [
        f"https://api1.binance.com/api/v3/depth?symbol={symbol}&limit=100",
        f"https://api2.binance.com/api/v3/depth?symbol={symbol}&limit=100",
        f"https://api3.binance.com/api/v3/depth?symbol={symbol}&limit=100",
        f"https://data-api.binance.vision/api/v3/depth?symbol={symbol}&limit=100"
    ]
    
    url = random.choice(gateways)
    try:
        # Додаємо випадковий хедер, щоб не пізнали в нас бота
        headers = {'User-Agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) {random.random()}'}
        res = requests.get(url, headers=headers, timeout=5)
        
        if res.status_code == 200:
            data = res.json()
            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)
            return bids, asks
        return None, None
    except:
        return None, None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("🧱 Dihash Monitor")
manual_list = st.sidebar.text_area("Мій список", "BTC,ETH,SOL,BNB,XRP").upper().replace(" ", "")
my_coins = [c + "USDT" if not c.endswith("USDT") else c for c in manual_list.split(",")]
target = st.sidebar.selectbox("🎯 Актив для аналізу", my_coins)

# Основна панель
col_chart, col_data = st.columns([3, 1])

with col_chart:
    st.subheader(f"📊 Live Chart: {target}")
    # Графік з вбудованим профілем об'єму (VPVR)
    st.markdown(f"""
        <div style="height:650px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                    width="100%" height="650" frameborder="0" allowfullscreen></iframe>
        </div>
    """, unsafe_allow_html=True)

with col_data:
    st.subheader("🧱 Великі лімітки")
    
    # Спроба отримати стакан
    bids, asks = get_order_book_pro(target)
    
    if bids is not None and asks is not None:
        # Розрахунок аномальних об'ємів (як у Dihash)
        # Стінкою вважаємо ордер, що більший за середній у 4 рази
        wall_threshold_bid = bids['qty'].mean() * 4
        wall_threshold_ask = asks['qty'].mean() * 4
        
        st.markdown("🔴 **Стінки Опору (Asks):**")
        big_asks = asks[asks['qty'] > wall_threshold_ask].sort_values('qty', ascending=False)
        if not big_asks.empty:
            for _, row in big_asks.head(5).iterrows():
                st.error(f"💲 {row['price']} | 🧱 {row['qty']:.1f}")
        else:
            st.caption("Чисто (великих ліміток немає)")

        st.markdown("🟢 **Стінки Підтримки (Bids):**")
        big_bids = bids[bids['qty'] > wall_threshold_bid].sort_values('qty', ascending=False)
        if not big_bids.empty:
            for _, row in big_bids.head(5).iterrows():
                st.success(f"💲 {row['price']} | 🧱 {row['qty']:.1f}")
        else:
            st.caption("Чисто (великих ліміток немає)")

        # Market Power
        st.markdown("---")
        power = bids['qty'].sum() / (bids['qty'].sum() + asks['qty'].sum())
        st.write(f"⚖️ Сила стакана: **{power*100:.1f}%**")
        st.progress(power)
        
    else:
        st.error("🔌 Помилка шлюзу Binance.")
        st.info("Binance часто блокує хмарні сервери. Спробуйте змінити монету або зачекайте 10 секунд — скрипт змінить сервер автоматично.")

# Авто-оновлення кожні 20 секунд
time.sleep(20)
st.rerun()
