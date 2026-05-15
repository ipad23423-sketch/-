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
    try:
        res = requests.get(url).json()
        df = pd.DataFrame(res)
        df = df[df['symbol'].endswith('USDT')]
        df['lastPrice'] = df['lastPrice'].astype(float)
        df['priceChangePercent'] = df['priceChangePercent'].astype(float)
        df['quoteVolume'] = df['quoteVolume'].astype(float)
        return df
    except:
        return pd.DataFrame()

def calculate_correlation(df):
    try:
        btc_row = df[df['symbol'] == 'BTCUSDT']
        if not btc_row.empty:
            btc_change = btc_row['priceChangePercent'].values[0]
            # Спрощена кореляція для швидкості
            df['Correlation'] = df['priceChangePercent'].apply(lambda x: round(x / btc_change if btc_change != 0 else 0, 2))
        else:
            df['Correlation'] = 0.0
        return df
    except:
        df['Correlation'] = 0.0
        return df

# --- САЙДБАР (ФІЛЬТРИ) ---
st.sidebar.title("🛠 Налаштування PRO")

view_mode = st.sidebar.radio("Режим перегляду", ["Таблиця", "Сітка монет"])

# Виправлені цифри (без k, M, B)
vol_options = [0, 100000, 1000000, 5000000, 10000000, 50000000, 100000000, 500000000, 1000000000]
vol_min, vol_max = st.sidebar.select_slider(
    "Фільтр об'єму ($)",
    options=vol_options,
    value=(1000000, 100000000),
    format_func=lambda x: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1000:.0f}k" if x > 0 else "0"
)

chg_range = st.sidebar.slider("Зміна ціни (%)", -20.0, 20.0, (-5.0, 10.0))
corr_filter = st.sidebar.slider("Кореляція до BTC", -2.0, 2.0, (-2.0, 2.0))

watchlist = st.sidebar.multiselect("Вибрані монети (Watchlist)", ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE"])

# --- ОСНОВНА ЛОГІКА ---
st.title("📊 Crypto Intellect Screener")

placeholder = st.empty()

while True:
    raw_df = get_all_data()
    if not raw_df.empty:
        df = calculate_correlation(raw_df)
        
        # Фільтрація
        mask = (df['quoteVolume'] >= vol_min) & (df['quoteVolume'] <= vol_max) & \
               (df['priceChangePercent'] >= chg_range[0]) & (df['priceChangePercent'] <= chg_range[1]) & \
               (df['Correlation'] >= corr_filter[0]) & (df['Correlation'] <= corr_filter[1])
        
        if watchlist:
            mask = mask & (df['symbol'].str.replace('USDT','').isin(watchlist))
        
        filtered_df = df[mask].sort_values(by="priceChangePercent", ascending=False)

        with placeholder.container():
            # Поради
            tips = ["Не торгуй на емоціях", "Дотримуйся ризик-менеджменту", "Щільність — це не гарантія розвороту"]
            st.info(f"🧠 Порада дня: {tips[int(time.time()%3)]}")

            if view_mode == "Таблиця":
                st.dataframe(filtered_df[['symbol', 'lastPrice', 'priceChangePercent', 'quoteVolume', 'Correlation']].rename(columns={
                    'symbol': 'Тикер', 'lastPrice': 'Ціна', 'priceChangePercent': 'Зміна %', 'quoteVolume': 'Об\'єм', 'Correlation': 'Корел. BTC'
                }).style.format({
                    'Ціна': '{:.4f}',
                    'Зміна %': '{:+.2f}%',
                    'Об\'єм': '{:,.0f}',
                    'Корел. BTC': '{:.2f}'
                }).background_gradient(subset=['Зміна %'], cmap='RdYlGn'), use_container_width=True, height=500)
            
            else:
                # СІТКА МОНЕТ
                cols = st.columns(4)
                for i, (_, row) in enumerate(filtered_df.iterrows()):
                    with cols[i % 4]:
                        color = "#22c55e" if row['priceChangePercent'] > 0 else "#ef4444"
                        st.markdown(f"""
                            <div class="metric-card">
                                <h4 style="margin:0">{row['symbol'].replace('USDT','')}</h4>
                                <h2 style="color:{color}; margin:10px 0">{row['priceChangePercent']:+.2f}%</h2>
                                <p style="font-size:12px; margin:0">Ціна: {row['lastPrice']:.4f}<br>Об'єм: {row['quoteVolume']/1e6:.1f}M</p>
                            </div>
                        """, unsafe_allow_html=True)

    time.sleep(10)