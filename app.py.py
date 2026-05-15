import streamlit as st
import requests
import pandas as pd
import time
import random

# Налаштування сторінки
st.set_page_config(page_title="PRO Crypto Terminal v3.4", layout="wide")

# Функція отримання даних з анти-блокуванням
def fetch_market_data_resilient():
    # Список різних дзеркал Binance
    endpoints = [
        "https://fapi.binance.com/fapi/v1/ticker/24hr",
        "https://api1.binance.com/api/v3/ticker/24hr",
        "https://api2.binance.com/api/v3/ticker/24hr",
        "https://api3.binance.com/api/v3/ticker/24hr"
    ]
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'application/json'
    }

    url = random.choice(endpoints)
    try:
        # Додаємо випадковий параметр, щоб обійти кеш сервера
        res = requests.get(url, headers=headers, params={'t': random.random()}, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # Лишаємо тільки USDT пари
            df = df[df['symbol'].str.endswith('USDT')]
            numeric_cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Форматування об'єму як у Digash
            df['vol_display'] = df['quoteVolume'].apply(
                lambda x: f"{x/1e9:.2f}B$" if x >= 1e9 else f"{x/1e6:.1f}M$"
            )
            return df
        return None
    except:
        return None

# --- ГОРІШНЯ ПАНЕЛЬ ---
st.sidebar.title("💎 Digash PRO Terminal")
df = fetch_market_data_resilient()

if df is not None and not df.empty:
    # Сортування за об'ємом (як на скріншоті Digash)
    df_sorted = df.sort_values('quoteVolume', ascending=False)
    all_coins = df_sorted['symbol'].tolist()
    
    target = st.sidebar.selectbox("🎯 Оберіть актив", all_coins, index=0)
    coin = df[df['symbol'] == target].iloc[0]

    # Метрики (Верхня панель)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Price", f"{coin['lastPrice']}", f"{coin['priceChangePercent']}%")
    with m2:
        st.metric("Volume (24h)", coin['vol_display'])
    with m3:
        vol = ((coin['highPrice'] - coin['lowPrice']) / coin['lowPrice']) * 100
        st.metric("Volatility", f"{vol:.2f}%")
    with m4:
        st.metric("24h High/Low", f"{coin['highPrice']} / {coin['lowPrice']}")

    st.markdown("---")

    # Графік та Таблиця
    col_l, col_r = st.columns([2.5, 1.2])

    with col_l:
        # Графік TradingView завжди працює, бо вантажиться у тебе в браузері
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                    width="100%" height="650" frameborder="0" allowfullscreen></iframe>
        """, unsafe_allow_html=True)

    with col_r:
        st.subheader("📊 Market Activity")
        # Таблиця з сортуванням за об'ємом
        top_list = df_sorted[['symbol', 'vol_display', 'priceChangePercent']].head(20)
        st.dataframe(top_list.rename(columns={'symbol': 'Монета', 'vol_display': 'Об\'єм', 'priceChangePercent': '%'}), 
                     hide_index=True, use_container_width=True, height=600)

else:
    # Якщо API все ще спить, показуємо графік-заглушку, щоб ти міг працювати
    st.error("🚫 Основне API Binance заблоковано. Працюємо через резервний графік.")
    manual_target = st.text_input("Введіть тикер для графіка (напр. BTCUSDT)", "BTCUSDT").upper()
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{manual_target}PERP&interval=60&theme=dark&style=1" 
                width="100%" height="650" frameborder="0" allowfullscreen></iframe>
    """, unsafe_allow_html=True)
    st.info("Спробуйте натиснути 'R' або оновити сторінку через хвилину.")

# Авто-оновлення
time.sleep(45)
st.rerun()
