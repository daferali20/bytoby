# stock_dashboard.py

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import yfinance as yf

st.set_page_config(page_title="تحليل الأسهم", layout="wide")

# ========== التحليل ==========
@st.cache_data
def fetch_data(symbol, period="3mo"):
    data = yf.download(symbol, period=period)
    data.reset_index(inplace=True)
    data['date'] = pd.to_datetime(data['Date'])
    data.set_index('date', inplace=True)
    return data

def plot_performance(symbol, period="6mo"):
    data = fetch_data(symbol, period)
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(data['Close'], label=f"{symbol} سعر الإغلاق", color='blue')
    ax.set_title(f"أداء {symbol} خلال {period}")
    ax.set_xlabel("التاريخ")
    ax.set_ylabel("السعر")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)

def calc_liquidity(symbols):
    results = []
    for symbol in symbols:
        df = fetch_data(symbol)
        avg_volume = df['Volume'].mean()
        results.append({'الرمز': symbol, 'السيولة المتوسطة': avg_volume})
    return pd.DataFrame(results).sort_values('السيولة المتوسطة', ascending=False)

def top_gainers(symbols):
    results = []
    for symbol in symbols:
        df = fetch_data(symbol, period="5d")
        change = (df['Close'].iloc[-1] - df['Open'].iloc[-1]) / df['Open'].iloc[-1] * 100
        results.append({'الرمز': symbol, 'التغير (%)': round(change, 2)})
    return pd.DataFrame(results).sort_values('التغير (%)', ascending=False)

def compare_vs_index(symbol, index="^GSPC"):
    df_stock = fetch_data(symbol, period="1y")
    df_index = fetch_data(index, period="1y")
    r_stock = (df_stock['Close'].iloc[-1] - df_stock['Close'].iloc[0]) / df_stock['Close'].iloc[0] * 100
    r_index = (df_index['Close'].iloc[-1] - df_index['Close'].iloc[0]) / df_index['Close'].iloc[0] * 100
    return {
        'أداء السهم': round(r_stock, 2),
        'أداء المؤشر': round(r_index, 2),
        'تفوق السهم': round(r_stock - r_index, 2)
    }

# ========== الواجهة ==========
st.title("📊 نظام تحليل الأسهم الذكي")

symbols_default = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA"]
symbols = st.multiselect("اختر الأسهم المراد تحليلها:", options=symbols_default, default=symbols_default)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["📈 أداء السهم", "💧 السيولة", "🚀 الأعلى ارتفاعًا", "📊 مقارنة مع المؤشر", "🔍 التفاصيل"])

with tab1:
    selected = st.selectbox("اختر سهمًا للرسم:", symbols)
    period = st.selectbox("الفترة:", ["1mo", "3mo", "6mo", "1y"], index=2)
    plot_performance(selected, period)

with tab2:
    st.subheader("الأسهم الأكثر سيولة:")
    st.dataframe(calc_liquidity(symbols), use_container_width=True)

with tab3:
    st.subheader("الأسهم الأعلى ارتفاعًا:")
    st.dataframe(top_gainers(symbols), use_container_width=True)

with tab4:
    selected = st.selectbox("اختر سهمًا للمقارنة:", symbols, key="comp")
    results = compare_vs_index(selected)
    st.metric("📈 أداء السهم", f"{results['أداء السهم']}%")
    st.metric("📉 أداء المؤشر", f"{results['أداء المؤشر']}%")
    st.metric("📊 تفوق السهم", f"{results['تفوق السهم']}%")

with tab5:
    st.info("يمكنك تطوير تبويب تفاصيل لعرض مؤشرات RSI، MACD، متوسطات متحركة...")

