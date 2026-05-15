import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="PRO Terminal v3.6 (Resilient)", layout="wide")

# --- ФУНКЦІЯ ОТРИМАННЯ ДАНИХ З COINGECKO ---
def get_coingecko_data():
    # Отримуємо топ-150 монет за капіталізацією
    url = "https://api.coingecko.com/api/v3/coins/markets"
    params = {
        'vs_currency': 'usd',
        'order': 'market_cap_desc',
        'per_page': 150,
        'page': 1,
        'sparkline': False
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json())
            # Підганяємо назви під формат бірж
            df['symbol_trade'] = df['symbol'].str.upper() + "USDT"
            return df
        return None
    except:
        return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Global Crypto Monitor")
df = get_coingecko_data()

if df is not None and not df.empty:
    # Сортуємо за об'ємом торгів (total_volume)
    df_sorted = df.sort_values('total_volume', ascending=False)
    all_symbols = df_sorted['symbol_trade'].tolist()
    
    target = st.sidebar.selectbox("🎯 Оберіть монету", all_symbols, index=0)
    coin = df[df['symbol_trade'] == target].iloc[0]

    # Верхня панель метрик (Digash Style)
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.metric("Ціна (USD)", f"${coin['current_price']}", f"{coin['price_change_percentage_24h']:.2f}%")
    with m2:
        vol = coin['total_volume']
        vol_str = f"{vol/1e9:.2f}B$" if vol >= 1e9 else f"{vol/1e6:.2f}M$"
        st.metric("Об'єм 24г", vol_str)
    with m3:
        st.metric("Market Cap Rank", f"#{coin['market_cap_rank']}")
    with m4:
        st.metric("24h High/Low", f"${coin['high_24h']} / ${coin['low_24h']}")

    st.markdown("---")

    # Основний блок: Графік та Таблиця
    col_l, col_r = st.columns([2.5, 1.2])

    with col_l:
        # Графік Binance (TradingView) - він ПРАЦЮЄ, бо йде через твій IP
        st.markdown(f"""
            <div style="height:650px;">
                <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval=60&theme=dark&style=1&details=true&studies=[%22Volume@tv-basicstudies%22,%22VbPFixed@tv-basicstudies%22]" 
                        width="100%" height="650" frameborder="0" allowfullscreen></iframe>
            </div>
        """, unsafe_allow_html=True)

    with col_r:
        st.subheader("📊 Top by Volume (Global)")
        # Таблиця лідерів ринку
        top_list = df_sorted[['symbol_trade', 'total_volume', 'price_change_percentage_24h']].head(20)
        top_list['total_volume'] = top_list['total_volume'].apply(lambda x: f"{x/1e6:.1f}M$")
        
        st.dataframe(
            top_list.rename(columns={'symbol_trade': 'Монета', 'total_volume': 'Об\'єм', 'price_change_percentage_24h': '%'}), 
            hide_index=True, use_container_width=True, height=600
        )
else:
    # ОСТАННІЙ РУБІЖ: Якщо навіть агрегатор лежить, даємо чистий графік
    st.error("📡 Проблеми зі зв'язком. Режим автономного графіка активований.")
    manual = st.text_input("Введіть тикер вручну", "BTCUSDT").upper()
    st.markdown(f"""
        <iframe src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{manual}PERP&interval=60&theme=dark" 
                width="100%" height="700" frameborder="0"></iframe>
    """, unsafe_allow_html=True)

time.sleep(60)
st.rerun()
