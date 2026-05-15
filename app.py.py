import streamlit as st
import requests
import pandas as pd
import numpy as np
import time
import random

st.set_page_config(page_title="PRO Crypto Terminal", layout="wide")

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ (Ф'ючерси + Статистика) ---
@st.cache_data(ttl=30)
def get_market_data():
    url = "https://fapi.binance.com/fapi/v1/ticker/24hr"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            df = df[df['symbol'].endswith('USDT')]
            cols = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice', 'volume']
            df[cols] = df[cols].astype(float)
            # Форматуємо об'єм як у Digash (у мільярдах/мільйонах)
            df['vol_display'] = df['quoteVolume'].apply(lambda x: f"{x/1e9:.1f}B$" if x >= 1e9 else f"{x/1e6:.1f}M$")
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# --- ОСНОВНИЙ ІНТЕРФЕЙС ---
df = get_market_data()

if not df.empty:
    # Сортуємо за об'ємом як у Digash
    df_sorted = df.sort_values('quoteVolume', ascending=False)
    futures_list = df_sorted['symbol'].tolist()
    
    # Вибір монети
    target = st.sidebar.selectbox("🔍 Пошук монети", futures_list, index=0)
    coin_data = df[df['symbol'] == target].iloc[0]

    # ВЕРХНЯ ПАНЕЛЬ СТАТИСТИКИ (як зліва на Digash)
    col_stat1, col_stat2, col_stat3, col_stat4 = st.columns(4)
    with col_stat1:
        st.metric("Ціна", f"{coin_data['lastPrice']}", f"{coin_data['priceChangePercent']}%")
    with col_stat2:
        st.metric("Об'єм (24h)", coin_data['vol_display'])
    with col_stat3:
        volatility = ((coin_data['highPrice'] - coin_data['lowPrice']) / coin_data['lowPrice']) * 100
        st.metric("Волатильність", f"{volatility:.2f}%")
    with col_stat4:
        st.metric("High / Low", f"{coin_data['highPrice']} / {coin_data['lowPrice']}")

    st.markdown("---")

    # ОСНОВНИЙ БЛОК: ГРАФІК ТА ТАБЛИЦЯ
    col_left, col_right = st.columns([2.5, 1.2])

    with col_left:
        # Професійний графік
        st.markdown(f"""
            <div style="height:600px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                        width="100%" height="600" frameborder="0" allowfullscreen></iframe>
            </div>
        """, unsafe_allow_html=True)

    with col_right:
        st.subheader("📊 Топ Ф'ючерсів")
        # Таблиця як у правій частині Digash
        display_table = df_sorted[['symbol', 'vol_display', 'priceChangePercent']].head(20)
        display_table.columns = ['Монета', 'Об\'єм 24г', 'Зміна %']
        
        # Стилізація таблиці
        def color_change(val):
            color = 'green' if val > 0 else 'red'
            return f'color: {color}'

        st.dataframe(display_table.style.applymap(color_change, subset=['Зміна %']), 
                     height=550, use_container_width=True, hide_index=True)

    # НИЖНЯ ПАНЕЛЬ: АНАЛІЗ СТАНКА (Dihash Feature)
    st.markdown("---")
    st.subheader(f"🧱 Глибокий аналіз стакана: {target}")
    # Тут залишаємо твою функцію get_order_book, яку ми зробили раніше
    # (Додай її сюди зі свого попереднього коду)

else:
    st.error("Помилка підключення до API. Спробуйте оновити сторінку.")

time.sleep(30)
st.rerun()
