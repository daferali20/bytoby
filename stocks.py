import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="📊 مراقبة أداء الأسهم الذكية", layout="wide")

TIINGO_API_KEY = "16be092ddfdcb6e34f1de36875a3072e2c724afb"
DEFAULT_SYMBOLS = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN"]

@st.cache_data
def fetch_data_tiingo(symbol, start_date="2023-01-01", end_date=None):
    if not end_date:
        end_date = str(datetime.now().date())
    url = f"https://api.tiingo.com/tiingo/daily/{symbol}/prices"
    params = {
        "startDate": start_date,
        "endDate": end_date
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TIINGO_API_KEY}"
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()

    if not data or not isinstance(data, list):
        return pd.DataFrame()

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df = df.sort_index()

    for col in ['open', 'high', 'low', 'close', 'volume']: 
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df

def calculate_indicators(df):
    df['SMA_20'] = df['close'].rolling(window=20).mean()
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['SMA_200'] = df['close'].rolling(window=200).mean()
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df.dropna()

def classify_performance(change):
    if change > 10:
        return "🔥 قوي", "green"
    elif change > 5:
        return "✅ جيد", "blue"
    elif change > 0:
        return "🔹 متوسط", "orange"
    else:
        return "🔻 ضعيف", "red"

def gauge_chart(title, value, max_val, unit="", color="blue"):
    return go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        number={'suffix': f" {unit}"},
        gauge={
            'axis': {'range': [None, max_val]},
            'bar': {'color': color},
            'bgcolor': "white",
            'steps': [
                {'range': [0, max_val * 0.3], 'color': "#d0f0fd"},
                {'range': [max_val * 0.3, max_val * 0.7], 'color': "#90c9f8"},
                {'range': [max_val * 0.7, max_val], 'color': "#2a79d5"},
            ]
        }
    ))

def detect_signals(df):
    signals = {}
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    # تقاطع ذهبي
    golden_cross = (df['SMA_50'].iloc[-2] < df['SMA_200'].iloc[-2]) and (df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1])

    # اختراق مقاومة (أعلى إغلاق خلال 3 أشهر)
    resistance = df['close'].iloc[-60:-1].max()
    breakout = latest['close'] > resistance

    if golden_cross:
        signals['golden_cross'] = True
    if breakout:
        signals['breakout'] = True

    return signals

st.title("🚀 لوحة مراقبة الأسهم الذكية")
symbols_input = st.text_input("أدخل رموز الأسهم مفصولة بفواصل (أو اتركها فارغة للأفضل):", "")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()] or DEFAULT_SYMBOLS

rising_stocks = []
golden_cross_stocks = []
breakout_stocks = []

for symbol in symbols:
    try:
        df = fetch_data_tiingo(symbol)
        df = calculate_indicators(df)

        latest = df.iloc[-1]
        change = ((df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]) * 100
        rsi = latest['RSI']
        volume = latest['volume']

        label, color = classify_performance(change)
        signals = detect_signals(df)

        if change > 5:
            rising_stocks.append(symbol)
        if signals.get('golden_cross'):
            golden_cross_stocks.append(symbol)
        if signals.get('breakout'):
            breakout_stocks.append(symbol)

        st.markdown(f"### 🏷️ {symbol} - {label}")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.plotly_chart(gauge_chart("📊 الأداء", round(change, 2), 20, "%", color), use_container_width=True)
        with col2:
            st.plotly_chart(gauge_chart("📈 RSI", round(rsi, 2), 100, "", "orange"), use_container_width=True)
        with col3:
            st.plotly_chart(gauge_chart("💰 السيولة", int(volume), 1_000_000, "", "purple"), use_container_width=True)

    except Exception as e:
        st.warning(f"⚠️ حدث خطأ أثناء تحليل {symbol}: {e}")

st.markdown("---")
st.subheader("📈 الأسهم الأكثر ارتفاعًا")
st.write(", ".join(rising_stocks) if rising_stocks else "لا توجد حالياً")

st.subheader("🌟 الأسهم ذات التقاطع الذهبي")
st.write(", ".join(golden_cross_stocks) if golden_cross_stocks else "لا توجد حالياً")

st.subheader("🚀 الأسهم التي اخترقت المقاومة")
st.write(", ".join(breakout_stocks) if breakout_stocks else "لا توجد حالياً")
