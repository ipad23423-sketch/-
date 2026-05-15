import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="PRO Terminal (Bybit Data)", layout="wide")

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ З BYBIT ---
def get_bybit_data():
    # Ендпоінт Bybit для ф'ючерсів (Linear Perpetual)
    url = "https://api.bybit.com/v5/market/tickers?category=linear"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            data = res.json()['result']['list']
            df = pd.DataFrame(data)
            # Фільтруємо тільки USDT пари
            df = df[df['symbol'].str.endswith('USDT')]
            
            # Конвертуємо типи даних
            cols = ['lastPrice', 'price24hPcnt', 'turnover24h', 'highPrice24h', 'lowPrice24h']
            for col in cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Рахуємо зміну у відсотках (Bybit дає в частках, напр. 0.02)
            df['change_pct'] = df['price24hPcnt'] * 100
            
            # Форматуємо об'єм (turnover24h - це об'єм у USDT)
            df['vol_display'] = df['turnover24h'].apply(
                lambda x: f"{x/1e9:.2f}B$" if x >= 1e9 else f"{x/1e6:.1f}M$"
            )
            return df
        return None
    except:
        return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Digash Bybit Edition")
df = get_bybit_data()

if df is not None and not df.empty:
    # Сортування за об'ємом (як у Digash)
    df_sorted = df.sort_values('turnover24h', ascending=False)
    all_symbols = df_sorted['symbol'].tolist()
    
    target = st.sidebar.selectbox("🎯 Оберіть пару (Bybit List)", all_symbols, index=0)
    coin = df[df['symbol'] == target].iloc[0]

    # Верхня панель метрик
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Ціна", f"{coin['lastPrice']}", f"{coin['change_pct']:.2f}%")
    with m2:
        st.metric("Об'єм 24г", coin['vol_display'])
    with m3:
        # Розрахунок волатильності
        volat = ((coin['highPrice24h'] - coin['lowPrice24h']) / coin['lowPrice24h']) * 100
        st.metric("Волатильність", f"{volat:.2f}%")
    with m4:
        st.metric("24h High/Low", f"{coin['highPrice24h']} / {coin['lowPrice24h']}")

    st.markdown("---")

    # Графік та Таблиця
    col_left, col_right = st.columns([2.5, 1.2])

    with col_left:
        # Використовуємо графік Binance через TradingView (він стабільний)
        st.markdown(f"""
            <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                    width="100%" height="650" frameborder="0" allowfullscreen></iframe>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader("📊 Market List (Bybit)")
        # Таблиця як у правій частині Digash
        top_list = df_sorted[['symbol', 'vol_display', 'change_pct']].head(25)
        st.dataframe(
            top_list.rename(columns={'symbol': 'Монета', 'vol_display': 'Об\'єм', 'change_pct': '%'}), 
            hide_index=True, use_container_width=True, height=600
        )
else:
    st.error("🔌 Навіть Bybit не відповідає. Спробуйте оновити сторінку через 10 секунд.")
    time.sleep(10)
    st.rerun()

# Оновлення даних кожні 30 секунд
time.sleep(30)
st.rerun()
