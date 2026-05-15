Python 3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)] on win32
Enter "help" below or click "Help" above for more information.
import streamlit as st
import requests
import pandas as pd
import time

# Налаштування сторінки
st.set_page_config(page_title="Crypto Screener Live", layout="wide")

st.title("🚀 Crypto Screener (Binance USDT)")
st.write("Дані оновлюються в реальному часі")

# Бокова панель з фільтрами
st.sidebar.header("Налаштування фільтрів")
min_vol = st.sidebar.number_input("Мінім. об'єм ($)", value=1000000, step=500000)
min_chg = st.sidebar.slider("Мінім. ріст (%)", -10.0, 10.0, 2.0)
refresh_rate = st.sidebar.slider("Оновлення (сек)", 5, 60, 10)

def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    res = requests.get(url).json()
    
    rows = []
    for coin in res:
        if coin['symbol'].endswith('USDT'):
            rows.append({
...                 "Тикер": coin['symbol'].replace('USDT', ''),
...                 "Ціна ($)": float(coin['lastPrice']),
...                 "Зміна (%)": float(coin['priceChangePercent']),
...                 "Об'єм ($)": float(coin['quoteVolume'])
...             })
...     return pd.DataFrame(rows)
... 
... # Основний цикл оновлення
... placeholder = st.empty()
... 
... while True:
...     df = get_data()
...     
...     
...     # Фільтрація
...     filtered_df = df[(df['Об'єм ($)'] >= min_vol) & (df['Зміна (%)'] >= min_chg)]
...     filtered_df = filtered_df.sort_values(by="Зміна (%)", ascending=False)
... 
...     with placeholder.container():
...         # Метрики
...         col1, col2 = st.columns(2)
...         col1.metric("Активів знайдено", len(filtered_df))
...         col2.metric("Найбільший ріст", 
...                   f"{filtered_df['Тикер'].iloc[0] if not filtered_df.empty else 'N/A'}", 
...                   f"{filtered_df['Зміна (%)'].iloc[0] if not filtered_df.empty else 0}%")
... 
...         # Таблиця з підсвіткою
...         st.dataframe(
...             filtered_df.style.format({
...                 "Ціна ($)": "{:.4f}",
...                 "Зміна (%)": "{:+.2f}%",
...                 "Об'єм ($)": "{:,.0f}"
...             }).background_gradient(subset=["Зміна (%)"], cmap="RdYlGn"),
...             height=600,
...             use_container_width=True
...         )
...         
