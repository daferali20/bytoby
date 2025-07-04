import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
from datetime import datetime
import time
import threading

st.set_page_config(page_title="📊 مراقبة أداء الأسهم الذكية", layout="wide")

TIINGO_API_KEY = "16be092ddfdcb6e34f1de36875a3072e2c724afb"
TELEGRAM_BOT_TOKEN = "7955161282:AAG2udkomniL-9kEgwdVheYXI52wVR3wiVM"
TELEGRAM_CHAT_ID = "@D_Option"


def fetch_top_gainers(limit=30):
    url = f"https://api.tiingo.com/iex/?token={TIINGO_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df['changePercent'] = df['last'] / df['prevClose'] - 1
        top_gainers = df.sort_values(by='changePercent', ascending=False).head(limit)
        return top_gainers[['ticker', 'changePercent']]
    except:
        return pd.DataFrame(columns=['ticker', 'changePercent'])


def send_telegram_alert(message: str):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            st.sidebar.success("✉️ تم إرسال تنبيه تيليجرام بنجاح")
        else:
            st.sidebar.error(f"❌ فشل الإرسال. الكود: {response.status_code} - {response.text}")
    except Exception as e:
        st.sidebar.error(f"❌ خطأ أثناء إرسال التنبيه: {e}")


@st.cache_data
def fetch_data_tiingo(symbol, start_date="2025-01-01", end_date=None):
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


def fetch_latest_news():
    url = "https://api.tiingo.com/tiingo/news"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Token {TIINGO_API_KEY}"
    }
    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        return data[:10] if isinstance(data, list) else []
    except:
        return []


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
    df['52_week_high'] = df['close'].rolling(window=252).max()
    df['52_week_low'] = df['close'].rolling(window=252).min()
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
        title={'text': title, 'font': {'size': 14}},
        number={'suffix': f" {unit}", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [None, max_val], 'tickwidth': 1, 'tickcolor': "darkgray"},
            'bar': {'color': color, 'thickness': 0.2},
            'bgcolor': "#f7f7f7",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, max_val * 0.3], 'color': "#f0f8ff"},
                {'range': [max_val * 0.3, max_val * 0.7], 'color': "#add8e6"},
                {'range': [max_val * 0.7, max_val], 'color': "#4682b4"},
            ]
        },
    )).update_layout(
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="#e8e8e8",
        height=160
    )


def detect_signals(df):
    signals = {}
    latest = df.iloc[-1]
    previous = df.iloc[-2]
    golden_cross = (df['SMA_50'].iloc[-2] < df['SMA_200'].iloc[-2]) and (df['SMA_50'].iloc[-1] > df['SMA_200'].iloc[-1])
    resistance = df['close'].iloc[-60:-1].max()
    breakout = latest['close'] > resistance
    if golden_cross:
        signals['golden_cross'] = True
    if breakout:
        signals['breakout'] = True
    return signals


def generate_recommendation(change, rsi, volume, signals):
    score = 0
    if change > 5:
        score += 1
    if 45 < rsi < 70:
        score += 1
    if volume > 200000:
        score += 1
    if signals.get("golden_cross"):
        score += 1
    if signals.get("breakout"):
        score += 1
    if score >= 4:
        return "🟢 راقب السهم — أداء قوي"
    elif score == 3:
        return "🔵 جيد — راقبه عن قرب"
    elif score == 2:
        return "🟡 متوسط — يحتاج تأكيد"
    else:
        return "🔴 غير مناسب حاليًا"

# Render news on sidebar
st.sidebar.title("📰 الأخبار العاجلة")
latest_news = fetch_latest_news()
if latest_news:
    for news in latest_news:
        title = news.get('title', 'عنوان غير متوفر')
        url = news.get('url', '#')
        source = news.get('source', '')
        published = news.get('publishedDate', '')
        st.sidebar.markdown(f"🔹 [{title}]({url})<br><sub>{source} | {published}</sub>", unsafe_allow_html=True)
else:
    st.sidebar.write("لا توجد أخبار حالياً.")

st.sidebar.markdown("---")
top_gainers_df = fetch_top_gainers()
AUTO_SYMBOLS = [
    "AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "NFLX", "BRK.B", "JPM", "V", "MA", "UNH", "XOM", "AVGO",
    "PEP", "KO", "LLY", "JNJ", "WMT", "PG", "ADBE", "CRM", "BAC", "PFE", "T", "DIS", "CSCO", "ORCL", "INTC", "AMD"
] + top_gainers_df['ticker'].tolist()

st.sidebar.markdown("✅ يتم تحليل الأسهم الأكثر ارتفاعًا بشكل تلقائي")
st.sidebar.markdown("---")
st.sidebar.markdown("📈 قائمة الأسهم الأكثر ارتفاعًا")
st.sidebar.dataframe(top_gainers_df.rename(columns={"ticker": "الرمز", "changePercent": "% التغير"}).round(3), use_container_width=True)

# التحليل الكامل للأسهم سيتم إضافته الآن...
# (يمكن إضافة الكود المتعلق بالتحليل وعرض النتائج هنا)
