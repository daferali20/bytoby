import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
from datetime import datetime
import time
import threading

st.set_page_config(page_title="📊 مراقبة أداء الأسهم الذكية", layout="wide")
NEWS_API_KEY = "f55929edb5ee471791a1e622332ff6d8"
TIINGO_API_KEY = "16be092ddfdcb6e34f1de36875a3072e2c724afb"
TELEGRAM_BOT_TOKEN = "7955161282:AAG2udkomniL-9kEgwdVheYXI52wVR3wiVM"
TELEGRAM_CHAT_ID = "@D_Option"


def fetch_top_gainers(limit=13):
    url = f"https://api.tiingo.com/iex/?token={TIINGO_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        df = pd.DataFrame(data)

        # حساب النسبة المئوية للتغير
        df['changePercent'] = df['last'] / df['prevClose'] - 1

        # تصفية الأسهم التي ارتفعت أكثر من 5% وأقل من 200%
        filtered = df[(df['changePercent'] >= 0.05) & (df['changePercent'] <= 2.0)]

        # ترتيبها من الأعلى إلى الأقل وأخذ أول 'limit' سهم
        top_gainers = filtered.sort_values(by='changePercent', ascending=False).head(limit)

        # إرجاع النتائج
        return top_gainers[['ticker', 'changePercent']]
    except Exception as e:
        print(f"Error fetching gainers: {e}")
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
def fetch_data_tiingo(symbol, start_date=None, end_date=None):
    if not end_date:
        end_date = str(datetime.now().date())
    if not start_date:
        start_date = (datetime.now() - pd.DateOffset(years=2)).strftime("%Y-%m-%d")  # قبل سنتين
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
    url = "https://newsapi.org/v2/top-headlines"
    params = {
        "country": "us",   # يمكن تغييره حسب الدولة أو حسب ما تريد
        "pageSize": 5,
        "apiKey": NEWS_API_KEY
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        # تحقق إذا كانت الاستجابة ناجحة
        if data.get("status") == "ok":
            return data.get("articles", [])
        else:
            return []
    except Exception as e:
        print(f"Error fetching news: {e}")
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


st.title("📊 تحليل الأسهم الذكية")

selected_symbol = st.selectbox("اختر سهمًا للتحليل", options=AUTO_SYMBOLS, index=0)

if selected_symbol:
    with st.spinner(f"جلب البيانات وتحليل السهم {selected_symbol}..."):
        df = fetch_data_tiingo(selected_symbol)
        if df.empty or len(df) < 2:
            st.warning("⚠️ لا توجد بيانات كافية لهذا السهم حالياً.")
        else:
            df = calculate_indicators(df)

            fig = go.Figure()
            fig.add_trace(go.Scatter(x=df.index, y=df['close'], mode='lines', name='سعر الإغلاق'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_50'], mode='lines', name='SMA 50'))
            fig.add_trace(go.Scatter(x=df.index, y=df['SMA_200'], mode='lines', name='SMA 200'))
            fig.update_layout(title=f"مخطط سعر سهم {selected_symbol}", xaxis_title="التاريخ", yaxis_title="السعر")
            st.plotly_chart(fig, use_container_width=True)

            latest = df.iloc[-1]
            previous = df.iloc[-2]
            change_percent = (latest['close'] / previous['close'] - 1) * 100

            performance, color = classify_performance(change_percent)

            col1, col2, col3, col4 = st.columns(4)
            col1.metric("التغير %", f"{change_percent:.2f}%", delta=f"{change_percent:.2f}%")
            col2.metric("مؤشر RSI", f"{latest['RSI']:.2f}")
            col3.metric("أعلى سعر خلال 52 أسبوع", f"{latest['52_week_high']:.2f}")
            col4.metric("أدنى سعر خلال 52 أسبوع", f"{latest['52_week_low']:.2f}")

            st.markdown(f"### التقييم الحالي: <span style='color:{color}; font-weight:bold'>{performance}</span>", unsafe_allow_html=True)
            st.markdown(f"### حجم التداول: {int(latest['volume']):,}")

            signals = detect_signals(df)
            st.markdown("### إشارات فنية")
            if signals.get('golden_cross'):
                st.success("✅ تقاطع ذهبي (Golden Cross) تم الكشف عنه.")
            if signals.get('breakout'):
                st.success("🚀 كسر المقاومة (Breakout) تم الكشف عنه.")
            if not signals:
                st.info("لا توجد إشارات فنية حالياً.")

            recommendation = generate_recommendation(change_percent, latest['RSI'], latest['volume'], signals)
            st.markdown(f"### التوصية: {recommendation}")

            if st.button("📩 إرسال تنبيه تيليجرام للتوصية"):
                message = (
                    f"توصية للسهم <b>{selected_symbol}</b>:\n"
                    f"التغير: {change_percent:.2f}%\n"
                    f"RSI: {latest['RSI']:.2f}\n"
                    f"حجم التداول: {int(latest['volume']):,}\n"
                    f"التقييم: {performance}\n"
                    f"التوصية: {recommendation}"
                )
                send_telegram_alert(message)
