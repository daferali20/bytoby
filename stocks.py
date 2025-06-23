import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf
import numpy as np

st.set_page_config(page_title="تحليل فني للأسهم", layout="wide")

@st.cache_data
def fetch_data(symbol, period="6mo"):
    df = yf.download(symbol, period=period)
    if df.empty:
        return pd.DataFrame()
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
    return df.dropna(subset=['SMA_50', 'EMA_20', 'RSI', 'MACD', 'Signal'])

def draw_gauge(label, value, min_value=0, max_value=100, color='green'):
    fig, ax = plt.subplots(figsize=(3.5, 2.3), subplot_kw={'projection': 'polar'})
    ax.set_theta_offset(np.pi / 2)
    ax.set_theta_direction(-1)
    ax.set_ylim(0, 10)
    angles = np.linspace(0, np.pi, 100)
    ax.plot(angles, [10]*100, lw=20, color='lightgray')
    angle = np.pi * (value - min_value) / (max_value - min_value)
    ax.arrow(angle, 0, 0, 8, width=0.05, head_width=0.2, head_length=1, fc=color, ec=color)
    ax.set_yticklabels([])
    ax.set_xticks([])
    ax.spines['polar'].set_visible(False)
    ax.text(0, -2, f"{label}\n{value:.1f}", ha='center', va='center', fontsize=12)
    plt.close()
    return fig

def performance_summary(df):
    required = ['RSI', 'MACD', 'Signal', 'SMA_50']
    for col in required:
        if col not in df.columns or df[col].isna().all():
            raise ValueError(f"البيانات تفتقد إلى العمود: {col}")

    summary = {}
    scores = 0

    rsi = df['RSI'].iloc[-1]
    if rsi > 70:
        summary['RSI'] = (rsi, 'red')
    elif rsi > 55:
        summary['RSI'] = (rsi, 'green'); scores += 1
    elif rsi > 45:
        summary['RSI'] = (rsi, 'blue')
    else:
        summary['RSI'] = (rsi, 'red')

    macd = df['MACD'].iloc[-1]
    signal = df['Signal'].iloc[-1]
    macd_strength = macd - signal
    if macd_strength > 0.5:
        summary['MACD'] = (macd_strength*10, 'green'); scores += 1
    elif macd_strength < -0.5:
        summary['MACD'] = (abs(macd_strength)*10, 'red')
    else:
        summary['MACD'] = (abs(macd_strength)*10, 'blue')

    price = df['Close'].iloc[-1]
    sma = df['SMA_50'].iloc[-1]
    sma_diff = price - sma
    if sma_diff > 0:
        summary['SMA'] = (sma_diff, 'green'); scores += 1
    else:
        summary['SMA'] = (abs(sma_diff), 'red')

    trend = df['Close'].rolling(5).mean().diff().iloc[-1]
    if trend > 0.5:
        summary['Trend'] = (trend*10, 'green'); scores += 1
    elif trend < -0.5:
        summary['Trend'] = (abs(trend)*10, 'red')
    else:
        summary['Trend'] = (abs(trend)*10, 'blue')

    summary['score'] = scores
    return summary

def plot_chart(df, symbol):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Close'], label='السعر', color='black')
    ax.plot(df['SMA_50'], label='SMA 50', linestyle='--')
    ax.plot(df['EMA_20'], label='EMA 20', linestyle=':')
    ax.set_title(f"سعر {symbol}")
    ax.legend()
    ax.grid(True)
    st.pyplot(fig)

# واجهة التطبيق
st.title("\ud83d\udcc8 نظام التحليل الفني للأسهم")
symbols_input = st.text_input("\ud83d\udce5 أدخل رموز الأسهم مفصولة بفواصل (مثال: AAPL,MSFT,2280.SR):", "AAPL,MSFT")
period = st.selectbox("\u23f3 اختر المدة الزمنية:", ["1mo", "3mo", "6mo", "1y"], index=2)
filter_strong = st.checkbox("\u2705 إظهار الأسهم ذات الأداء الفني القوي فقط", value=False)

if st.button("\ud83d\udd0d تحليل الأسهم"):
    symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
    for symbol in symbols:
        st.markdown(f"---\n## \ud83d\udd0e {symbol}")
        try:
            df = fetch_data(symbol, period)
            if df.empty:
                st.warning(f"\u26a0\ufe0f لا توجد بيانات للسهم {symbol}")
                continue

            df = calculate_indicators(df)
            summary = performance_summary(df)

            if filter_strong and summary['score'] < 3:
                continue

            col1, col2 = st.columns([2, 1])

            with col1:
                plot_chart(df, symbol)

            with col2:
                st.subheader("\ud83d\udcca مؤشرات القوة:")
                for label in ['RSI', 'MACD', 'SMA', 'Trend']:
                    value, color = summary[label]
                    fig = draw_gauge(label, value, 0, 100 if label == 'RSI' else 50, color)
                    st.pyplot(fig)

        except ValueError as ve:
            st.warning(f"\u26a0\ufe0f {symbol}: {ve}")
        except Exception as e:
            st.error(f"\u274c حدث خطأ أثناء تحليل {symbol}: {e}")
