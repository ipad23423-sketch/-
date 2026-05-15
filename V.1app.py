import streamlit as st
import requests
import pandas as pd
import time

# Налаштування сторінки
st.set_page_config(page_title="Crypto Screener Live", layout="wide")

st.title("🚀 Crypto Screener (Binance USDT)")
st.write("Дані оновлюються автоматично")

# Бокова панель
st.sidebar.header("Налаштування")
min_vol = st.sidebar.number_input("Мінім. об'єм ($)", value=1000000, step=500000)
min_chg = st.sidebar.slider("Мінім. ріст (%)", -10.0, 10.0, 2.0)
refresh_rate = st.sidebar.slider("Оновлення (сек)", 5, 60, 10)

def get_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        res = requests.get(url).json()
        rows = []
        for coin in res:
            if coin['symbol'].endswith('USDT'):
                rows.append({
                    "Ticker": coin['symbol'].replace('USDT', ''),
                    "Price": float(coin['lastPrice']),
                    "Change": float(coin['priceChangePercent']),
                    "Volume": float(coin['quoteVolume'])
                })
        return pd.DataFrame(rows)
    except:
        return pd.DataFrame()

placeholder = st.empty()

while True:
    df = get_data()
    
    if not df.empty:
        # Фільтрація
        filtered_df = df[(df['Volume'] >= min_vol) & (df['Change'] >= min_chg)]
        filtered_df = filtered_df.sort_values(by="Change", ascending=False)

        with placeholder.container():
            col1, col2 = st.columns(2)
            col1.metric("Активів знайдено", len(filtered_df))
            if not filtered_df.empty:
                col2.metric("Лідер росту", filtered_df['Ticker'].iloc[0], f"{filtered_df['Change'].iloc[0]}%")

            # Відображення таблиці
            st.dataframe(
                filtered_df.rename(columns={
                    "Ticker": "Тикер",
                    "Price": "Ціна ($)",
                    "Change": "Зміна (%)",
                    "Volume": "Об'єм ($)"
                }).style.format({
                    "Ціна ($)": "{:.4f}",
                    "Зміна (%)": "{:+.2f}%",
                    "Об'єм ($)": "{:,.0f}"
                }).background_gradient(subset=["Зміна (%)"], cmap="RdYlGn"),
                height=600,
                use_container_width=True
            )
    
    time.sleep(refresh_rate)
import streamlit as st
import requests
import pandas as pd
import numpy as np
import time

st.set_page_config(page_title="Crypto Pro Screener", layout="wide")

# --- СТИЛІЗАЦІЯ ---
st.markdown("""
    <style>
    .metric-card {
        background-color: #1e2130;
        padding: 15px;
        border-radius: 10px;
        border: 1px solid #3e4251;
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- ФУНКЦІЇ ДАНИХ ---
@st.cache_data(ttl=5)
def get_all_data():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    res = requests.get(url).json()
    df = pd.DataFrame(res)
    df = df[df['symbol'].endswith('USDT')]
    df['lastPrice'] = df['lastPrice'].astype(float)
    df['priceChangePercent'] = df['priceChangePercent'].astype(float)
    df['quoteVolume'] = df['quoteVolume'].astype(float)
    return df

def calculate_correlation(df):
    # Спрощена логіка кореляції для швидкості (порівняння вектору зміни ціни)
    btc_change = df[df['symbol'] == 'BTCUSDT']['priceChangePercent'].values[0] if not df[df['symbol'] == 'BTCUSDT'].empty else 0
    df['Correlation'] = df['priceChangePercent'].apply(lambda x: round(np.corrcoef([x, btc_change])[0,1] if x != 0 else 0, 2))
    return df

# --- САЙДБАР (ФІЛЬТРИ) ---
st.sidebar.title("🛠 Налаштування PRO")

view_mode = st.sidebar.radio("Режим перегляду", ["Таблиця", "Сітка монет"])

vol_min, vol_max = st.sidebar.select_slider(
    "Фільтр об'єму ($)",
    options=[0, 100k, 1M, 5M, 10M, 50M, 100M, 500M, 1B],
    value=(1M, 100M),
    format_func=lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x}"
)

chg_range = st.sidebar.slider("Зміна ціни (%)", -20.0, 20.0, (-5.0, 5.0))
corr_filter = st.sidebar.slider("Кореляція до BTC", -1.0, 1.0, (-1.0, 1.0))

watchlist = st.sidebar.multiselect("Вибрані монети (Watchlist)", ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"])

# --- ОСНОВНА ЛОГІКА ---
st.title("📊 Crypto Intellect Screener")

placeholder = st.empty()

while True:
    raw_df = get_all_data()
    df = calculate_correlation(raw_df)
    
    # Фільтрація
    mask = (df['quoteVolume'] >= vol_min) & (df['quoteVolume'] <= vol_max) & \
           (df['priceChangePercent'] >= chg_range[0]) & (df['priceChangePercent'] <= chg_range[1]) & \
           (df['Correlation'] >= corr_filter[0]) & (df['Correlation'] <= corr_filter[1])
    
    if watchlist:
        mask = mask & (df['symbol'].str.replace('USDT','').isin(watchlist))
    
    filtered_df = df[mask].sort_values(by="priceChangePercent", ascending=False)

    with placeholder.container():
        # Секція психології (Рандомні поради)
        tips = ["Не торгуй на емоціях", "Дотримуйся ризик-менеджменту", "Щільність — це не гарантія розвороту"]
        st.info(f"🧠 Порада дня: {tips[int(time.time()%3)]}")

        if view_mode == "Таблиця":
            st.dataframe(filtered_df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume', 'Correlation']].style.format({
                'lastPrice': '{:.4f}',
                'priceChangePercent': '{:+.2f}%',
                'quoteVolume': '{:,.0f}',
                'Correlation': '{:.2f}'
            }).background_gradient(subset=['priceChangePercent'], cmap='RdYlGn'), use_container_width=True, height=500)
        
        else:
            # СІТКА МОНЕТ
            cols = st.columns(4)
            for i, (_, row) in enumerate(filtered_df.iterrows()):
                with cols[i % 4]:
                    color = "green" if row['priceChangePercent'] > 0 else "red"
                    st.markdown(f"""
                        <div class="metric-card">
                            <h4>{row['symbol'].replace('USDT','')}</h4>
                            <h2 style="color:{color}">{row['priceChangePercent']:+.2f}%</h2>
                            <p>Ціна: {row['lastPrice']:.4f}<br>Об'єм: {row['quoteVolume']/1e6:.1f}M</p>
                        </div>
                    """, unsafe_allow_html=True)

    time.sleep(10)