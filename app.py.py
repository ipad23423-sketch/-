import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="Crypto Whale Hunter PRO", layout="wide")

# --- ФУНКЦІЯ ОТРИМАННЯ ВСІХ Ф'ЮЧЕРСНИХ МОНЕТ ---
@st.cache_data(ttl=3600) # Оновлюємо список монет раз на годину
def get_futures_symbols():
    url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            # Беремо тільки USDT пари, які знаходяться в трейдингу (TRADING)
            symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
            return sorted(symbols)
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# --- АНАЛІЗ СТАНКА ---
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

# --- ПОШУК КИТОВИХ УГОД ---
def get_whale_trades(symbol, threshold_usd=50000):
    url = f"https://api.binance.com/api/v3/trades?symbol={symbol}&limit=50"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            trades = pd.DataFrame(res.json())
            trades['price'] = trades['price'].astype(float)
            trades['qty'] = trades['qty'].astype(float)
            trades['usd_val'] = trades['price'] * trades['qty']
            whales = trades[trades['usd_val'] >= threshold_usd].copy()
            whales['time'] = pd.to_datetime(whales['time'], unit='ms').dt.strftime('%H:%M:%S')
            return whales
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- САЙДБАР ---
st.sidebar.title("🐳 Whale Hunter PRO")

# Автоматичне завантаження всіх монет
futures_list = get_futures_symbols()
target = st.sidebar.selectbox("🎯 Оберіть ф'ючерсну пару", futures_list, index=futures_list.index("BTCUSDT") if "BTCUSDT" in futures_list else 0)

whale_limit = st.sidebar.slider("Поріг кита ($)", 10000, 500000, 50000, step=10000)

st.sidebar.markdown("---")
st.sidebar.write(f"✅ Всього знайдено монет: {len(futures_list)}")

# --- ОСНОВНА ПАНЕЛЬ ---
col_chart, col_data = st.columns([2.5, 1.2])

with col_chart:
    st.subheader(f"📈 LIVE: {target} (Futures)")
    st.markdown(f"""
        <div style="height:650px;">
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=15&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                    width="100%" height="650" frameborder="0" allowfullscreen></iframe>
        </div>
    """, unsafe_allow_html=True)

with col_data:
    # БЛОК СТАНКА
    st.subheader("🧱 Стінки")
    bids, asks = get_order_book(target)
    if bids is not None:
        wall_b = bids['qty'].mean() * 4
        wall_a = asks['qty'].mean() * 4
        
        c1, c2 = st.columns(2)
        with c1:
            st.caption("🟢 Support")
            st.dataframe(bids[bids['qty'] > wall_b].head(5)[['price', 'qty']], hide_index=True)
        with c2:
            st.caption("🔴 Resistance")
            st.dataframe(asks[asks['qty'] > wall_a].head(5)[['price', 'qty']], hide_index=True)
    
    st.markdown("---")
    
    # БЛОК КИТІВ
    st.subheader("🐋 Стрічка китів")
    whale_trades = get_whale_trades(target, whale_limit)
    
    if not whale_trades.empty:
        for _, trade in whale_trades.iterrows():
            side = "🟢 BUY" if not trade['isBuyerMaker'] else "🔴 SELL"
            color = "green" if side == "🟢 BUY" else "red"
            st.markdown(f"**{trade['time']}** | <span style='color:{color}'>{side}</span> | **${trade['usd_val']:,.0f}**", unsafe_allow_html=True)
    else:
        st.caption("Великих угод поки немає...")

# Авто-оновлення
time.sleep(20)
st.rerun()
