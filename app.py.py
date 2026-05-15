import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta
import time

st.set_page_config(page_title="Crypto AI Screener Pro", layout="wide", initial_sidebar_state="expanded")

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ ---
@st.cache_data(ttl=10)
def get_all_pairs():
    url = "https://api.binance.com/api/v3/ticker/24hr"
    try:
        data = requests.get(url).json()
        df = pd.DataFrame(data)
        df = df[df['symbol'].endswith('USDT')]
        # Чистимо назви від USDT для зручності
        df['coin'] = df['symbol'].str.replace('USDT', '')
        cols_to_fix = ['lastPrice', 'priceChangePercent', 'quoteVolume', 'highPrice', 'lowPrice']
        df[cols_to_fix] = df[cols_to_fix].astype(float)
        return df
    except:
        return pd.DataFrame()

# --- САЙДБАР ---
st.sidebar.title("💎 PRO Control Panel")
search_coin = st.sidebar.text_input("🔍 Швидкий пошук монети", "").upper()

vol_min = st.sidebar.number_input("Мін. Об'єм ($)", value=0)
chg_filter = st.sidebar.slider("Зміна ціни (%)", -30.0, 30.0, (-30.0, 30.0))

# --- ОСНОВНИЙ БЛОК ---
df = get_all_pairs()

if not df.empty:
    # Фільтрація
    filtered_df = df[(df['quoteVolume'] >= vol_min) & 
                    (df['priceChangePercent'] >= chg_filter[0]) & 
                    (df['priceChangePercent'] <= chg_filter[1])]
    
    if search_coin:
        filtered_df = filtered_df[filtered_df['coin'].str.contains(search_coin)]

    # Вибір монети
    coin_list = filtered_df['symbol'].tolist()
    
    col_main, col_side = st.columns([3, 1])

    with col_main:
        if coin_list:
            selected_symbol = st.selectbox("🎯 Оберіть монету для аналізу та рівнів", coin_list)
            
            # Розрахунок рівнів (спрощений Pivot Points)
            coin_data = df[df['symbol'] == selected_symbol].iloc[0]
            r1 = round(coin_data['lastPrice'] * 1.02, 4) # Опір +2%
            s1 = round(coin_data['lastPrice'] * 0.98, 4) # Підтримка -2%
            
            st.subheader(f"📊 Графік {selected_symbol}")
            
            # Вставка графіка TradingView (Свічки + Інструменти)
            st.markdown(f"""
                <div style="height:600px;">
                    <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{selected_symbol}&interval=15&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&details=true&hotlist=true&calendar=true" 
                            width="100%" height="600" frameborder="0" allowfullscreen></iframe>
                </div>
            """, unsafe_allow_html=True)
            
            st.write(f"📍 **Авто-рівні (найближчі):** Опір: `{r1}` | Підтримка: `{s1}`")
        else:
            st.error("Монет не знайдено. Скиньте фільтри.")

    with col_side:
        st.subheader("🔥 Top Gainers")
        top_df = filtered_df.sort_values(by="priceChangePercent", ascending=False).head(10)
        for _, row in top_df.iterrows():
            st.success(f"**{row['coin']}**: {row['priceChangePercent']:+.2f}%")
        
        st.subheader("💡 Психологія")
        st.caption("Рівні — це зони, де товпа приймає рішення. Не поспішай входити перед рівнем, чекай реакції.")

    # Таблиця внизу
    st.markdown("---")
    st.subheader("📋 Всі доступні пари (USDT)")
    st.dataframe(filtered_df[['coin', 'lastPrice', 'priceChangePercent', 'quoteVolume']].rename(columns={
        'coin': 'Монета', 'lastPrice': 'Ціна', 'priceChangePercent': '24h %', 'quoteVolume': 'Об\'єм'
    }), use_container_width=True)

else:
    st.warning("Завантаження даних з Binance...")
    time.sleep(2)
    st.rerun()