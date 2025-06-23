# stock_dashboard.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np

st.set_page_config(page_title="تحليل الأسهم الفني", layout="wide")

@st.cache_data
def fetch_data(symbol, period="6mo"):
    df = yf.download(symbol, period=period)
    df.reset_index(inplace=True)
    df['date'] = pd.to_datetime(df['Date'])
    df.set_index('date', inplace=True)
    return df

def calculate_indicators(df):
    df['SMA_50'] = df['Close'].rolling(window=50).mean()
    df['EMA_20'] = df['Close'].ewm(span=20, adjust=False).mean()

    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df

def plot_chart(df, symbol):
    fig, ax = plt.subplots(3, 1, figsize=(12, 8), sharex=True)

    # السعر والمتوسطات
    ax[0].plot(df['Close'], label='السعر', color='black')
    ax[0].plot(df['SMA_50'], label='SMA 50', linestyle='--')
    ax[0].plot(df['EMA_20'], label='EMA 20', linestyle=':')
    ax[0].set_title(f"سعر {symbol}")
    ax[0].legend()
    ax[0].grid(True)

    # RSI
    ax[1].plot(df['RSI'], label='RSI', color='purple')
    ax[1].axhline(70, color='red', linestyle='--')
    ax[1].axhline(30, color='green', linestyle='--')
    ax[1].set_title('RSI')
    ax[1].legend()
    ax[1].grid(True)

    # MACD
    ax[2].plot(df['MACD'], label='MACD', color='blue')
    ax[2].plot(df['Signal'], label='Signal', color='orange')
    ax[2].axhline(0, color='gray', linestyle='--')
    ax[2].set_title('MACD')
    ax[2].legend()
    ax[2].grid(True)

    st.pyplot(fig)

def detect_signals(df):
    if len(df) < 30:
        return ["❌ لا توجد بيانات كافية للتحليل الفني"]

    df = df.dropna(subset=['RSI', 'MACD', 'Signal', 'SMA_50'])

    if len(df) < 2:
        return ["❌ المؤشرات غير كافية بعد حذف القيم الفارغة"]

    latest = df.iloc[-1]
    prev = df.iloc[-2]

    signals = []

    try:
        if latest['RSI'] > 70:
            signals.append("🔺 RSI يشير إلى تشبع شرائي")
        elif latest['RSI'] < 30:
            signals.append("🔻 RSI يشير إلى تشبع بيعي")
    except:
        signals.append("⚠️ لم يتم حساب RSI بشكل صحيح")

    try:
        if prev['MACD'] < prev['Signal'] and latest['MACD'] > latest['Signal']:
            signals.append("🔺 تقاطع MACD صعودي (إشارة شراء)")
        elif prev['MACD'] > prev['Signal'] and latest['MACD'] < latest['Signal']:
            signals.append("🔻 تقاطع MACD هبوطي (إشارة بيع)")
    except:
        signals.append("⚠️ لم يتم حساب MACD بشكل صحيح")

    try:
        if latest['Close'] > latest['SMA_50']:
            signals.append("✅ السعر أعلى من المتوسط 50 يوم (قوة)")
        else:
            signals.append("⚠️ السعر تحت المتوسط 50 يوم")
    except:
        signals.append("⚠️ لا يمكن تقييم وضع السعر مقابل المتوسط")

    return signals


# ========== واجهة Streamlit ==========

st.title("📈 نظام التحليل الفني للأسهم")

symbols = st.text_input("📥 أدخل رمز السهم (مثال: AAPL أو 2280.SR):", "AAPL")
period = st.selectbox("⏳ اختر المدة:", ["1mo", "3mo", "6mo", "1y"], index=2)

if st.button("🔍 تحليل"):
    df = fetch_data(symbols.upper(), period=period)
    df = calculate_indicators(df)

    st.subheader("📊 المخطط الفني:")
    plot_chart(df, symbols.upper())

    st.subheader("🚨 الإشارات والتحذيرات الفنية:")
    signals = detect_signals(df)
    for sig in signals:
        st.info(sig)
