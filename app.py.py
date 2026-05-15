import streamlit as st
import requests
import pandas as pd
import time
import random

st.set_page_config(page_title="PRO Crypto v2.7", layout="wide")

def fetch_data_safe():
    # Список альтернативних дзеркал
    urls = [
        "https://api1.binance.com/api/v3/ticker/24hr",
        "https://api2.binance.com/api/v3/ticker/24hr",
        "https://api3.binance.com/api/v3/ticker/24hr"
    ]
    url = random.choice(urls)
    
    try:
        # Додаємо випадковий параметр, щоб обійти кешування та бан
        params = {'_cb': random.randint(1, 999999)}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        
        if response.status_code == 200:
            df = pd.DataFrame(response.json())
            df = df[df['symbol'].endswith('USDT')]
            for col in ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            return df
        return None
    except:
        return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 PRO Control")
search = st.sidebar.text_input("🔍 Пошук", "").upper()

df = fetch_data_safe()

if df is not None and not df.empty:
    # Якщо дані прийшли, виводимо все як раніше
    all_coins = df['symbol'].tolist()
    target = st.selectbox("🎯 Оберіть пару", all_coins, index=all_coins.index("BTCUSDT") if "BTCUSDT" in all_coins else 0)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}&interval=15&theme=dark" 
                    width="100%" height="550" frameborder="0"></iframe>
        """, unsafe_allow_html=True)
    
    with col2:
        st.subheader("🚀 Топ")
        st.write(df.sort_values('priceChangePercent', ascending=False).head(10)[['symbol', 'priceChangePercent']])

else:
    # Якщо бан висить, даємо пряме посилання на графік, щоб юзер міг працювати
    st.error("🚫 Binance все ще блокує запити від Streamlit Cloud.")
    st.info("Але графік нижче ПРАЦЮЄ (він вантажиться напряму з TradingView):")
    
    manual_coin = st.text_input("Введіть тикер вручну для графіка (напр. BTCUSDT)", "BTCUSDT").upper()
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{manual_coin}&interval=15&theme=dark" 
                width="100%" height="600" frameborder="0"></iframe>
    """, unsafe_allow_html=True)
    
    st.warning("Спробуйте оновити сторінку через 5 хвилин або зробіть 'Reboot App' у налаштуваннях.")

time.sleep(60)
st.rerun()
