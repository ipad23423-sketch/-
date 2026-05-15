import streamlit as st
import requests
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import trendln
import time
import numpy as np

st.set_page_config(page_title="Scalp Sniper AI v6.0", layout="wide")

# --- 1. ЗАВАНТАЖЕННЯ ДАНИХ ---
@st.cache_data(ttl=60)
def get_bybit_ohlc(symbol, interval):
    tf_map = {"5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}
    url = f"https://api.bybit.com/v5/market/kline?category=linear&symbol={symbol}&interval={tf_map[interval]}&limit=200"
    try:
        res = requests.get(url, timeout=10)
        if res.status_code == 200:
            df = pd.DataFrame(res.json()['result']['list'], columns=['time', 'open', 'high', 'low', 'close', 'vol', 'turnover'])
            df['time'] = pd.to_datetime(df['time'].astype(float), unit='ms')
            for col in ['open', 'high', 'low', 'close', 'vol']: df[col] = df[col].astype(float)
            return df.iloc[::-1].reset_index(drop=True)
    except: return None

# --- 2. АНАЛІТИКА: РІВНІ (TRENDLN) ---
def find_levels(df, lookback_period=20):
    # trendln знаходить екстремуми
    extrema = trendln.get_extrema(df['close'].to_numpy(), method='maxmin', accuracy=lookback_period)
    # Розраховуємо рівні підтримки/спротиву
    sup_res = trendln.get_support_resistance(df['close'].to_numpy(), accuracy=lookback_period)
    return sup_res

# --- 3. АНАЛІТИКА: ТРИКУТНИК (CUSTOM) ---
def detect_triangle(df, period=50):
    subset = df.iloc[-period:]
    lows = subset['low'].values
    highs = subset['high'].values
    times = subset['time'].values
    
    # Спрощена логіка: шукаємо лінію підтримки та спротиву, що сходяться
    l_reg = np.polyfit(range(period), lows, 1)  # Пряма підтримки
    h_reg = np.polyfit(range(period), highs, 1) # Пряма спротиву
    
    slope_diff = l_reg[0] - h_reg[0]
    
    # Якщо підтримка росте, а спротив падає — це трикутник
    if l_reg[0] > 0.0001 and h_reg[0] < -0.0001:
        return {
            'l_slope': l_reg[0], 'l_intercept': l_reg[1],
            'h_slope': h_reg[0], 'h_intercept': h_reg[1],
            'subset_start': subset.index[0]
        }
    return None

# --- ІНТЕРФЕЙС ---
st.sidebar.title("💎 Scalp Sniper v6.0")

# Перелік основних ф'ючерсів (можна розширити)
default_symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EDENUSDT", "SUIUSDT", "HYPEUSDT"]
target_symbol = st.sidebar.selectbox("Оберіть актив (Bybit Data)", default_symbols)
target_tf = st.sidebar.radio("Таймфрейм", ["5m", "15m", "1h", "4h"], index=1, horizontal=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Налаштування ШІ")

# Налаштування для автоматичного пошуку рівнів
lookback = st.sidebar.slider("Глибина аналізу (свічок)", 10, 100, 50)
min_touches = st.sidebar.number_input("Мінімум торкань у рівень", min_value=1, value=2)

# Налаштування формацій
st.sidebar.markdown("---")
# has_triangle = st.sidebar.checkbox("Шукати Трикутник", value=True)
# has_break = st.sidebar.checkbox("Шукати Слом Структури (BOS)", value=False)

# ОСНОВНИЙ БЛОК
df = get_bybit_ohlc(target_symbol, target_tf)

if df is not None:
    st.header(f"📊 {target_symbol} - Таймфрейм {target_tf}")
    
    # 🕯️ СВІЧНИЙ ГРАФІК
    fig = go.Figure(data=[go.Candlestick(
        x=df['time'], open=df['open'], high=df['high'],
        low=df['low'], close=df['close'], name='Свічки'
    )])

    # --- ДОДАЄМО АВТО-РІВНІ (TRENDLN) ---
    st.spinner("Аналізуємо рівні...")
    try:
        sup_res = find_levels(df, lookback_period=lookback)
        
        # Спротив (Червоні лінії)
        for res in sup_res[1]: # sup_res[1] - це список ліній спротиву
            # Фільтр: додаємо тільки якщо лінія "стара" (має більше торкань)
            if len(res) >= min_touches: # res - це список свічок, що торкнулися
                level_value = res[-1][1] # Значення ціни останнього торкання
                fig.add_hline(y=level_value, line_dash="solid", line_color="rgba(255, 70, 70, 0.8)", annotation_text=f"R ({len(res)})")

        # Підтримка (Зелені лінії)
        for sup in sup_res[0]: # sup_res[0] - це список ліній підтримки
            if len(sup) >= min_touches:
                level_value = sup[-1][1]
                fig.add_hline(y=level_value, line_dash="solid", line_color="rgba(70, 255, 70, 0.8)", annotation_text=f"S ({len(sup)})")
        
        st.success("Рівні підтримки та спротиву розраховано!")
    except:
        st.info("💡 На цьому таймфреймі trendln не знайшов стабільних рівнів.")

    # --- ДОДАЄМО ТРИКУТНИК (CUSTOM DRAWING) ---
    triangle = detect_triangle(df, period=lookback)
    if triangle:
        # Розраховуємо кінцеві точки для ліній
        x_values = df.loc[triangle['subset_start']:, 'time'].tolist()
        t_values = list(range(len(x_values)))
        
        l_y = [t * triangle['l_slope'] + triangle['l_intercept'] for t in t_values]
        h_y = [t * triangle['h_slope'] + triangle['h_intercept'] for t in t_values]
        
        # Малюємо лінії
        fig.add_trace(go.Scatter(x=x_values, y=l_y, mode='lines', line=dict(color='green', width=3), name='Triangle Support'))
        fig.add_trace(go.Scatter(x=x_values, y=h_y, mode='lines', line=dict(color='red', width=3), name='Triangle Resistance'))
        
        # fig.add_annotation(x=x_values[-1], y=h_y[-1], text="Triangle", showarrow=True)
        st.warning("⚠️ Виявлено формацію 'Трикутник'. Готуйтеся до імпульсу!")
        
    # --- НАЛАШТУВАННЯ ВІДОБРАЖЕННЯ ---
    fig.update_layout(
        template="plotly_dark",
        height=750,
        xaxis_rangeslider_visible=False,
        yaxis_title="Ціна USD",
        margin=dict(l=0,r=0,t=40,b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.sidebar.markdown(f"✅ Монет: {len(default_symbols)} | ШІ активний")
else:
    st.error("Помилка завантаження даних свічок.")

time.sleep(60)
st.rerun()
