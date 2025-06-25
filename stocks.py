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

DEFAULT_SYMBOLS = [
    "AAPL", "TSLA", "MSFT", "NVDA", "AMZN", "GOOGL", "META", "NFLX", "BRK.B", "JPM",
    "V", "MA", "UNH", "XOM", "AVGO", "PEP", "KO", "LLY", "JNJ", "WMT", "PG", "ADBE",
    "CRM", "BAC", "PFE", "T", "DIS", "CSCO", "ORCL", "INTC", "AMD"
]

def fetch_top_gainers(limit=30):
    url = f"https://api.tiingo.com/iex/?token={TIINGO_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)
        df['changePercent'] = df['last'] / df['prevClose'] - 1
        top_gainers = df.sort_values(by='changePercent', ascending=False).head(limit)
        return top_gainers[['ticker', 'changePercent']].reset_index(drop=True)
    except:
        return pd.DataFrame(columns=['ticker', 'changePercent'])

top_gainers_df = fetch_top_gainers()
AUTO_SYMBOLS = list(set(DEFAULT_SYMBOLS + top_gainers_df['ticker'].tolist()))

st.sidebar.title("📰 الأخبار العاجلة")

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
st.sidebar.markdown("✅ يتم تحليل الأسهم الأكثر ارتفاعًا بشكل تلقائي")

# عرض جدول بسيط في الواجهة لعرض الأسهم الأكثر ارتفاعًا
st.markdown("## 📈 قائمة الأسهم الأكثر ارتفاعًا حاليًا")
if not top_gainers_df.empty:
    top_gainers_df['changePercent'] = (top_gainers_df['changePercent'] * 100).round(2)
    top_gainers_df.rename(columns={'ticker': 'الرمز', 'changePercent': 'نسبة التغير %'}, inplace=True)
    st.dataframe(top_gainers_df, use_container_width=True)
else:
    st.warning("⚠️ تعذر تحميل الأسهم الأكثر ارتفاعًا حالياً.")
