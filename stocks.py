import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np
import requests
from datetime import datetime
import time
import threading
import telegram

st.set_page_config(page_title="\U0001F4CA مراقبة أداء الأسهم الذكية", layout="wide")

TIINGO_API_KEY = "16be092ddfdcb6e34f1de36875a3072e2c724afb"
TELEGRAM_BOT_TOKEN = "7955161282:AAG2udkomniL-9kEgwdVheYXI52wVR3wiVM"
TELEGRAM_CHAT_ID = "@D_Option"
DEFAULT_SYMBOLS = ["AAPL", "TSLA", "MSFT", "NVDA", "AMZN"]

bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)

def send_telegram_alert(message):
    try:
        bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)
        st.sidebar.success("\u2709\ufe0f تم إرسال تنبيه تيليجرام بنجاح")
    except Exception as e:
        st.sidebar.warning(f"\U0001F514 فشل إرسال تنبيه تيليجرام: {e}")

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
        return "\U0001F525 قوي", "green"
    elif change > 5:
        return "\u2705 جيد", "blue"
    elif change > 0:
        return "\ud83d\udd39 متوسط", "orange"
    else:
        return "\ud83d\udd3b ضعيف", "red"

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
        return "\U0001F7E2 راقب السهم — أداء قوي"
    elif score == 3:
        return "\U0001F535 جيد — راقبه عن قرب"
    elif score == 2:
        return "\U0001F7E1 متوسط — يحتاج تأكيد"
    else:
        return "\U0001F534 غير مناسب حاليًا"

st.title("\U0001F680 لوحة مراقبة الأسهم الذكية")
symbols_input = st.text_input("أدخل رموز الأسهم مفصولة بفواصل (أو اتركها فارغة للأفضل):", "")
symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()] or DEFAULT_SYMBOLS

refresh_button = st.button("\U0001F501 تحديث البيانات يدويًا")
auto_refresh = st.checkbox("تحليل تلقائي كل 5 دقائق")

if 'sent_alerts' not in st.session_state:
    st.session_state['sent_alerts'] = {}

run_analysis = False
if auto_refresh:
    last_run = st.session_state.get("last_run", None)
    now = time.time()
    if not last_run or now - last_run > 300:
        st.session_state["last_run"] = now
        run_analysis = True
else:
    run_analysis = refresh_button

st.sidebar.subheader("\U0001F514 تنبيهات تيليجرام المرسلة")
for sym, alerted in st.session_state['sent_alerts'].items():
    if alerted:
        st.sidebar.markdown(f"✅ **{sym}** تم الإرسال")

if st.sidebar.button("\U0001F504 اختبار إرسال تنبيه"):
    send_telegram_alert("✅ هذا تنبيه اختبار من لوحة مراقبة الأسهم")

if run_analysis:
    rising_stocks = []
    golden_cross_stocks = []
    breakout_stocks = []
    recommendations_list = []

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
            recommendation = generate_recommendation(change, rsi, volume, signals)
            if change > 5:
                rising_stocks.append(symbol)
            if signals.get('golden_cross'):
                golden_cross_stocks.append(symbol)
            if signals.get('breakout'):
                breakout_stocks.append(symbol)
            recommendations_list.append({
                "الرمز": symbol,
                "التغير %": round(change, 2),
                "RSI": round(rsi, 2),
                "الحجم": int(volume),
                "التوصية": recommendation
            })
            st.markdown(f"### \U0001F3F7️ {symbol} - {label}")
            st.markdown(f"{recommendation}")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.plotly_chart(gauge_chart("\U0001F4CA الأداء", round(change, 2), 20, "%", color), use_container_width=True)
            with col2:
                st.plotly_chart(gauge_chart("\U0001F4C8 RSI", round(rsi, 2), 100, "", "orange"), use_container_width=True)
            with col3:
                st.plotly_chart(gauge_chart("\U0001F4B0 السيولة", int(volume), 1_000_000, "", "purple"), use_container_width=True)

            is_strong = recommendation.startswith("\U0001F7E2")
            prev_alerted = st.session_state['sent_alerts'].get(symbol, False)
            if is_strong and not prev_alerted:
                send_telegram_alert(f"\U0001F4E2 سهم {symbol} يحقق أداء قوي الآن!\nالتغير: {round(change, 2)}%\nRSI: {round(rsi, 2)}\nحجم التداول: {int(volume)}")
                st.session_state['sent_alerts'][symbol] = True
            elif not is_strong:
                st.session_state['sent_alerts'][symbol] = False

        except Exception as e:
            st.warning(f"\u26A0\ufe0f حدث خطأ أثناء تحليل {symbol}: {e}")

    st.markdown("---")
    st.subheader("\U0001F4C8 الأسهم الأكثر ارتفاعًا")
    st.write(", ".join(rising_stocks) if rising_stocks else "لا توجد حالياً")
    st.subheader("\U0001F31F الأسهم ذات التقاطع الذهبي")
    st.write(", ".join(golden_cross_stocks) if golden_cross_stocks else "لا توجد حالياً")
    st.subheader("\U0001F680 الأسهم التي اخترقت المقاومة")
    st.write(", ".join(breakout_stocks) if breakout_stocks else "لا توجد حالياً")
    if recommendations_list:
        st.markdown("---")
        st.subheader("\U0001F4CB جدول التوصيات")
        df_recommendations = pd.DataFrame(recommendations_list)
        st.dataframe(df_recommendations, use_container_width=True)
       st.download_button("📥 تحميل التوصيات", df_recommendations.to_csv(index=False).encode("utf-8-sig"), file_name="stock_recommendations.csv", mime="text/csv")

