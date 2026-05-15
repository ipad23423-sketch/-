import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="Crypto Whale Hunter v3.0", layout="wide")

# --- ФУНКЦІЯ АНАЛІЗУ СТАНКА ---
def get_order_book(symbol):
    urls = [f"https://api1.binance.com/api/v3/depth?symbol={symbol}&limit=100",
            f"https://api2.binance.com/api/v3/depth?symbol={symbol}&limit=100"]
    try:
        res = requests.get(random.choice(urls), timeout=5)
        if res.status_code == 200:
            data = res.json()
            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)
            return bids, asks
        return None, None
    except:
        return None, None

# --- ФУНКЦІЯ ПОШУКУ КИТОВИХ УГОД ---
def get_whale_trades(symbol, threshold_usd=50000):
    url = f"https://api.binance.com/api/v3/trades?symbol={symbol}&limit=50"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            trades = pd.DataFrame(res.json())
            trades['price'] = trades['price'].astype(float)
            trades['qty'] = trades['qty'].astype(float)
            trades['usd_val'] = trades['price'] * trades['qty']
            
            # Фільтруємо лише великі угоди
            whales = trades[trades['usd_val'] >= threshold_usd].copy()
            whales['time'] = pd.to_datetime(whales['time'], unit='ms').dt.strftime('%H:%M:%S')
            return whales
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- САЙДБАР ---
st.sidebar.title("🐳 Whale Hunter")
manual_list = st.sidebar.text_area("Список монет", "BTC,ETH,SOL,BNB,XRP,DOGE").upper().replace(" ", "")
my_coins = [c + "USDT" if not c.endswith("USDT") else c for c in manual_list.split(",")]
target = st.sidebar.selectbox("🎯 Активна монета", my_coins)
whale_limit = st.sidebar.slider("Поріг кита ($)", 10000, 500000, 50000, step=10000)

# --- ОСНОВНА ПАНЕЛЬ ---
col_chart, col_data = st.columns([2.5, 1.2])

with col_chart:
    st.subheader(f"📈 Аналіз {target}")
    st.markdown(f"""
        <div style="height:600px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                    width="100%" height="600" frameborder="0" allowfullscreen></iframe>
        </div>
    """, unsafe_allow_html=True)

with col_data:
    # БЛОК СТАНКА (Стінки)
    st.subheader("🧱 Стінки (Order Book)")
    bids, asks = get_order_book(target)
    if bids is not None:
        wall_b = bids['qty'].mean() * 4
        wall_a = asks['qty'].mean() * 4
        
        c1, c2 = st.columns(2)
        with c1:
            st.caption("🟢 Підтримка")
            st.dataframe(bids[bids['qty'] > wall_b].head(5)[['price', 'qty']], hide_index=True)
        with c2:
            st.caption("🔴 Опір")
            st.dataframe(asks[asks['qty'] > wall_a].head(5)[['price', 'qty']], hide_index=True)
    
    st.markdown("---")
    
    # БЛОК КИТІВ (Whale Trades)
    st.subheader("🐋 Стрічка китів")
    whale_trades = get_whale_trades(target, whale_limit)
    
    if not whale_trades.empty:
        for _, trade in whale_trades.iterrows():
            side = "🟢 BUY" if not trade['isBuyerMaker'] else "🔴 SELL"
            color = "green" if side == "🟢 BUY" else "red"
            st.markdown(f"**{trade['time']}** | <span style='color:{color}'>{side}</span> | **${trade['usd_val']:,.0f}**", unsafe_allow_html=True)
    else:
        st.write("Сьогодні кити тихі... Великих угод не знайдено.")

# Авто-оновлення кожні 15 секунд
time.sleep(15)
st.rerun()
