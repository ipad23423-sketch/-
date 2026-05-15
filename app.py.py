import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import random

# 1. Конфігурація
st.set_page_config(page_title="PRO Crypto Terminal", layout="wide")

# 2. Функція отримання монет Futures
@st.cache_data(ttl=3600)
def get_futures_symbols():
    try:
        url = "https://fapi.binance.com/fapi/v1/exchangeInfo"
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()
            symbols = [s['symbol'] for s in data['symbols'] if s['quoteAsset'] == 'USDT' and s['status'] == 'TRADING']
            return sorted(symbols)
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]
    except:
        return ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

# 3. Отримання ринкових даних 24г
def get_market_data():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df = df[df['symbol'].endswith('USDT')]
            for col in ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['vol_display'] = df['quoteVolume'].apply(lambda x: f"{x/1e9:.1f}B$" if x >= 1e9 else f"{x/1e6:.1f}M$")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 4. Аналіз стакана (Стінки)
def get_order_book(symbol):
    url = f"https://fapi.binance.com/fapi/v1/depth?symbol={symbol}&limit=50"
    try:
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            bids = pd.DataFrame(data['bids'], columns=['price', 'qty']).astype(float)
            asks = pd.DataFrame(data['asks'], columns=['price', 'qty']).astype(float)
            return bids, asks
        return None, None
    except:
        return None, None

# --- ГОРІШНЯ ПАНЕЛЬ (Sidebar) ---
st.sidebar.title("💎 Digash PRO")
futures_list = get_futures_symbols()
target = st.sidebar.selectbox("🎯 Оберіть актив", futures_list, index=futures_list.index("BTCUSDT") if "BTCUSDT" in futures_list else 0)

# 5. Робота з даними
df_full = get_market_data()

if not df_full.empty:
    coin_info = df_full[df_full['symbol'] == target].iloc[0]
    
    # ВІДЖЕТИ СТАТИСТИКИ (Top Bar)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Price", f"{coin_info['lastPrice']}", f"{coin_info['priceChangePercent']}%")
    with m2:
        st.metric("Volume 24h", coin_info['vol_display'])
    with m3:
        volat = ((coin_info['highPrice'] - coin_info['lowPrice']) / coin_info['lowPrice']) * 100
        st.metric("Volatility", f"{volat:.2f}%")
    with m4:
        st.metric("H/L Range", f"{coin_info['highPrice']} / {coin_info['lowPrice']}")

    st.markdown("---")

    # ОСНОВНИЙ КОНТЕНТ (Графік + Таблиця)
    col_l, col_r = st.columns([2.5, 1.2])

    with col_l:
        st.markdown(f"""
            <div style="height:650px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                        width="100%" height="650" frameborder="0" allowfullscreen></iframe>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.subheader("📊 Market List")
        top_df = df_full.sort_values('quoteVolume', ascending=False).head(25)
        st.dataframe(top_df[['symbol', 'vol_display', 'priceChangePercent']].rename(columns={
            'symbol': 'Монета', 'vol_display': 'Об\'єм', 'priceChangePercent': '%'
        }), height=600, use_container_width=True, hide_index=True)

    # НИЖНІЙ БЛОК: СТАНКАН
    st.markdown("---")
    st.subheader("🧱 Order Book Walls")
    b, a = get_order_book(target)
    if b is not None:
        c1, c2 = st.columns(2)
        with c1:
            st.success("Bids (Support)")
            st.table(b.sort_values('qty', ascending=False).head(5))
        with c2:
            st.error("Asks (Resistance)")
            st.table(a.sort_values('qty', ascending=False).head(5))
else:
    st.warning("⚠️ Чекаємо відповіді від Binance API... Оновлення через 10с.")

# Авто-рефреш
time.sleep(30)
st.rerun()
