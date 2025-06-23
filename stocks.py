import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
from datetime import datetime

st.set_page_config(page_title="📊 لوحة التحليل الفني للأسهم", layout="wide")

API_KEY = "892f28628ea14be189ae98c007587b3a"

@st.cache_data
def fetch_data(symbol, period="6mo"):
    interval = "1day"
    outputsize = "5000"
    url = f"https://api.twelvedata.com/time_series?symbol={symbol}&interval={interval}&outputsize={outputsize}&apikey={API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "values" not in data:
        return pd.DataFrame()

    df = pd.DataFrame(data["values"])
    df.columns = [col.lower() for col in df.columns]
    df['date'] = pd.to_datetime(df['datetime'])
    df.set_index('date', inplace=True)
    df = df.sort_index()

    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

def calculate_indicators(df):
    df['SMA_50'] = df['close'].rolling(window=50).mean()
    df['EMA_20'] = df['close'].ewm(span=20, adjust=False).mean()
    delta = df['close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(14).mean()
    avg_loss = loss.rolling(14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['close'].ewm(span=12, adjust=False).mean()
    exp2 = df['close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp1 - exp2
    df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
    return df.dropna()

def plot_advanced_chart(df, symbol):
    fig = go.Figure()

    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='السعر'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['EMA_20'],
        mode='lines',
        line=dict(color='blue', width=1.5),
        name='EMA 20'
    ))

    fig.add_trace(go.Scatter(
        x=df.index,
        y=df['SMA_50'],
        mode='lines',
        line=dict(color='orange', width=1.5, dash='dash'),
        name='SMA 50'
    ))

    fig.update_layout(
        title=f"📉 الشموع اليابانية والمؤشرات - {symbol}",
        xaxis_title="التاريخ",
        yaxis_title="السعر",
        xaxis_rangeslider_visible=False,
        template='plotly_dark',
        height=600
    )
    return fig

def plot_rsi(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='lightgreen')))
    fig.add_hline(y=70, line=dict(color='red', dash='dash'))
    fig.add_hline(y=30, line=dict(color='blue', dash='dash'))
    fig.update_layout(title='مؤشر القوة النسبية (RSI)', height=300, template='plotly_white')
    return fig

def plot_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD', line=dict(color='cyan')))
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal'], mode='lines', name='Signal', line=dict(color='orange')))
    fig.update_layout(title='مؤشر الماكد (MACD)', height=300, template='plotly_white')
    return fig

st.title("🚀 لوحة التحليل الفني المتقدمة")
symbol = st.text_input("📥 أدخل رمز السهم (مثال: AAPL أو TADAWUL:2280):", value="AAPL")
period = st.selectbox("🕒 اختر الفترة الزمنية", ["1mo", "3mo", "6mo", "1y"], index=2)

if st.button("📊 تحليل السهم"):
    df = fetch_data(symbol, period)
    if df.empty or df.shape[0] < 60:
        st.error("⚠️ لا توجد بيانات كافية لتحليل هذا السهم.")
    else:
        df = calculate_indicators(df)
        st.plotly_chart(plot_advanced_chart(df, symbol), use_container_width=True)

        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(plot_rsi(df), use_container_width=True)
        with col2:
            st.plotly_chart(plot_macd(df), use_container_width=True)
