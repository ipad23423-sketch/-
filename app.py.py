import streamlit as st
import requests
import pandas as pd
import time

st.set_page_config(page_title="Scalp Sniper v7.0", layout="wide")

# --- СТАБІЛЬНИЙ СПИСОК МОНЕТ ---
def get_symbols():
    default = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "EDENUSDT", "HYPEUSDT", "SUIUSDT", "XRPUSDT"]
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/price", timeout=2)
        if res.status_code == 200:
            tickers = [s['symbol'] for s in res.json() if s['symbol'].endswith('USDT')]
            return sorted(list(set(tickers + default)))
        return default
    except:
        return default

# --- ІНТЕРФЕЙС ---
st.sidebar.title("🎯 Scalp Sniper v7.0")
symbols = get_symbols()

target = st.sidebar.selectbox("🎯 Оберіть актив", symbols, index=symbols.index("BTCUSDT") if "BTCUSDT" in symbols else 0)
tf_choice = st.sidebar.radio("Таймфрейм", ["1m", "5m", "15m", "1h", "4h", "1d"], index=2, horizontal=True)

# Мапінг таймфреймів
tf_map = {"1m":"1", "5m":"5", "15m":"15", "1h":"60", "4h":"240", "1d":"D"}

st.subheader(f"📊 Авто-аналіз структури: {target}")

# ВІДЖЕТ ІЗ АВТОМАТИЧНИМИ РІВНЯМИ ТА ФОРМАЦІЯМИ
# Ми використовуємо "Advanced Chart", який підтримує додавання індикаторів через скрипти
tradingview_html = f"""
    <div style="height: 800px;">
        <iframe 
            src="https://s.tradingview.com/widgetembed/?symbol=BINANCE:{target}PERP&interval={tf_map[tf_choice]}&theme=dark&style=1&timezone=Europe%2FKiev&withdateranges=true&hide_side_toolbar=false&allow_symbol_change=true&save_image=false&details=true&hotlist=true&calendar=true&studies=SupportResistanceLevels%40tv-basicstudies%7CTrianglePattern%40tv-basicstudies" 
            width="100%" 
            height="100%" 
            frameborder="0" 
            allowfullscreen>
        </iframe>
    </div>
"""

st.components.v1.html(tradingview_html, height=800)

# ІНСТРУКЦІЯ ДЛЯ АВТО-МАЛЮВАННЯ
with st.expander("🛠 Як увімкнути авто-рівні та формації на цьому графіку"):
    st.write("""
    1. Натисніть на кнопку **'Indicators'** (Індикатори) зверху графіка.
    2. У пошуку введіть **'Support and Resistance Levels with Breaks'** (для автоматичних рівнів та сломів структури).
    3. Для трикутників введіть **'Chart Patterns'** та оберіть потрібні формації.
    4. Тепер графік буде сам малювати лінії при кожному оновленні!
    """)

st.sidebar.info(f"Статус: Працює через дзеркало TradingView")
if st.sidebar.button("♻️ Перезавантажити"):
    st.rerun()
