import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="Crypto Intellect LITE Dihash", layout="wide")

# --- ФУНКЦІЯ АНАЛІЗУ СТАНКА ---
def get_order_book_analysis(symbol):
    url = f"https://api.binance.com/api/v3/depth"
    try:
        res = requests.get(url, params={'symbol': symbol, 'limit': 100}, timeout=5)
        if res.status_code == 200:
            data = res.json()
            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)
            
            # Шукаємо стінки (ордери, що в 3 рази більші за середні)
            avg_bid = bids['qty'].mean()
            avg_ask = asks['qty'].mean()
            
            big_bids = bids[bids['qty'] > avg_bid * 3]
            big_asks = asks[asks['qty'] > avg_ask * 3]
            
            return big_bids, big_asks
        return None, None
    except:
        return None, None

# --- САЙДБАР ---
st.sidebar.title("🕵️‍♂️ Аналізатор Стінок")
manual_list = st.sidebar.text_area("Список монет", "BTC,ETH,SOL,XRP,DOGE").upper().replace(" ", "")
my_coins = [c + "USDT" if not c.endswith("USDT") else c for c in manual_list.split(",")]
target = st.sidebar.selectbox("🎯 Активна монета", my_coins)

# --- ОСНОВНА ЧАСТИНА ---
col_chart, col_orderbook = st.columns([3, 1])

with col_chart:
    st.subheader(f"📊 Графік {target} (Pro Volume)")
    # TradingView з профілем об'єму та RSI
    st.markdown(f"""
        <div style="height:600px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22,%22RSI@tv-basicstudies%22]" 
                    width="100%" height="600" frameborder="0" allowfullscreen></iframe>
        </div>
    """, unsafe_allow_html=True)

with col_orderbook:
    st.subheader("🧱 Аналіз стінок (Dihash style)")
    bids, asks = get_order_book_analysis(target)
    
    if bids is not None and asks is not None:
        st.write("📈 **Стінки зверху (Опір):**")
        if not asks.empty:
            for _, row in asks.head(5).iterrows():
                st.error(f"Ціна: {row['price']} | Об'єм: {row['qty']:.2f}")
        else:
            st.write("Великих стінок не знайдено")
            
        st.write("📉 **Стінки знизу (Підтримка):**")
        if not bids.empty:
            for _, row in bids.head(5).iterrows():
                st.success(f"Ціна: {row['price']} | Об'єм: {row['qty']:.2f}")
        else:
            st.write("Великих стінок не знайдено")
            
        # Сила ринку
        total_bids = bids['qty'].sum()
        total_asks = asks['qty'].sum()
        ratio = total_bids / (total_bids + total_asks)
        st.write("---")
        st.write(f"📊 **Сила покупців:** {ratio*100:.1f}%")
        st.progress(ratio)
    else:
        st.warning("Не вдалося підключитися до ордербуку Binance.")

# Авто-оновлення аналізу стінок
time.sleep(15)
st.rerun()
