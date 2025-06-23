import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import yfinance as yf


class StockAnalyzer:
    def __init__(self):
        self.stock_data = pd.DataFrame()

    def fetch_data(self, symbol, period="1mo"):
        """جلب بيانات السهم من yfinance"""
        data = yf.download(symbol, period=period)
        data.reset_index(inplace=True)
        data['date'] = pd.to_datetime(data['Date'])
        data.set_index('date', inplace=True)
        return data

    def best_liquidity(self, stocks):
        liquidity_data = []
        for symbol in stocks:
            data = self.fetch_data(symbol)
            avg_volume = data['Volume'].mean()
            liquidity_data.append({'symbol': symbol, 'liquidity': avg_volume})
        df = pd.DataFrame(liquidity_data)
        return df.sort_values('liquidity', ascending=False).head(10)

    def top_gainers(self, stocks):
        gainers = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="1d")
            change = (data['Close'].iloc[-1] - data['Open'].iloc[-1]) / data['Open'].iloc[-1] * 100
            gainers.append({'symbol': symbol, 'gain': change})
        df = pd.DataFrame(gainers)
        return df.sort_values('gain', ascending=False).head(10)

    def most_traded(self, stocks):
        traded = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="1d")
            volume = data['Volume'].iloc[-1]
            traded.append({'symbol': symbol, 'volume': volume})
        df = pd.DataFrame(traded)
        return df.sort_values('volume', ascending=False).head(10)

    def three_month_performance(self, stocks):
        performance = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            change = (end_price - start_price) / start_price * 100
            performance.append({'symbol': symbol, '3mo_change': change})
        df = pd.DataFrame(performance)
        return df.sort_values('3mo_change', ascending=False).head(10)

    def six_month_performance(self, stocks):
        performance = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="6mo")
            start_price = data['Close'].iloc[0]
            end_price = data['Close'].iloc[-1]
            change = (end_price - start_price) / start_price * 100
            performance.append({'symbol': symbol, '6mo_change': change})
        df = pd.DataFrame(performance)
        return df.sort_values('6mo_change', ascending=False).head(10)

    def below_50ma(self, stocks):
        below_50 = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            ma50 = data['Close'].rolling(50).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            if current_price < ma50:
                below_50.append({'symbol': symbol, 'price': current_price, '50ma': ma50})
        return pd.DataFrame(below_50)

    def below_35ma(self, stocks):
        below_35 = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            ma35 = data['Close'].rolling(35).mean().iloc[-1]
            current_price = data['Close'].iloc[-1]
            if current_price < ma35:
                below_35.append({'symbol': symbol, 'price': current_price, '35ma': ma35})
        return pd.DataFrame(below_35)

    def vs_market_index(self, symbol, market_index="^GSPC"):
        stock_data = self.fetch_data(symbol, period="1y")
        index_data = self.fetch_data(market_index, period="1y")
        stock_return = (stock_data['Close'].iloc[-1] - stock_data['Close'].iloc[0]) / stock_data['Close'].iloc[0] * 100
        index_return = (index_data['Close'].iloc[-1] - index_data['Close'].iloc[0]) / index_data['Close'].iloc[0] * 100
        return {
            'symbol': symbol,
            'stock_return': stock_return,
            'index': market_index,
            'index_return': index_return,
            'outperformance': stock_return - index_return
        }

    def market_forecast(self):
        sp500 = self.fetch_data("^GSPC", period="1y")
        last_month = sp500['Close'].pct_change(21).iloc[-1] * 100
        if last_month > 5:
            return "اتجاه صعودي قوي"
        elif last_month > 2:
            return "اتجاه صعودي معتدل"
        elif last_month < -5:
            return "اتجاه هبوطي قوي"
        elif last_month < -2:
            return "اتجاه هبوطي معتدل"
        else:
            return "سوق متذبذب بدون اتجاه واضح"

    def plot_performance(self, symbol, period="6mo"):
        data = self.fetch_data(symbol, period)
        plt.figure(figsize=(10,5))
        plt.plot(data['Close'], label=f"{symbol} سعر الإغلاق", color='blue')
        plt.title(f"أداء {symbol} خلال آخر {period}")
        plt.xlabel("التاريخ")
        plt.ylabel("السعر")
        plt.grid(True)
        plt.legend()
        plt.tight_layout()
        plt.show()

# واجهة المستخدم البسيطة
def main():
    print("""
    نظام تحليل أداء الأسهم
    --------------------------
    1 - الأسهم الأفضل من حيث السيولة
    2 - الأسهم الأكثر ارتفاعًا
    3 - الأسهم الأكثر تداولًا
    4 - الأفضل أداءً لمدة 3 أشهر
    5 - الأفضل أداءً لمدة 6 أشهر
    6 - الأسهم تحت متوسط 50 يوم
    7 - الأسهم تحت متوسط 35 يوم
    8 - قياس أداء السهم مقابل المؤشر
    9 - الأداء المتوقع للسوق
    10 - رسم أداء سهم
    11 - الخروج
    """)
    
    analyzer = StockAnalyzer()
    stocks_list = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "TSLA", "NVDA", "PYPL", "ADBE", "NFLX"]
    
    while True:
        choice = input("اختر رقم الوظيفة (1-11): ")
        
        if choice == "1":
            print("\nالأسهم الأفضل من حيث السيولة:")
            print(analyzer.best_liquidity(stocks_list))
            
        elif choice == "2":
            print("\nالأسهم الأكثر ارتفاعًا:")
            print(analyzer.top_gainers(stocks_list))
            
        elif choice == "3":
            print("\nالأسهم الأكثر تداولًا:")
            print(analyzer.most_traded(stocks_list))
            
        elif choice == "4":
            print("\nالأفضل أداءً لمدة 3 أشهر:")
            print(analyzer.three_month_performance(stocks_list))
            
        elif choice == "5":
            print("\nالأفضل أداءً لمدة 6 أشهر:")
            print(analyzer.six_month_performance(stocks_list))
            
        elif choice == "6":
            print("\nالأسهم تحت متوسط 50 يوم:")
            print(analyzer.below_50ma(stocks_list))
            
        elif choice == "7":
            print("\nالأسهم تحت متوسط 35 يوم:")
            print(analyzer.below_35ma(stocks_list))
            
        elif choice == "8":
            symbol = input("أدخل رمز السهم: ").upper()
            print(f"\nأداء {symbol} مقابل المؤشر:")
            print(analyzer.vs_market_index(symbol))
            
        elif choice == "9":
            print("\nالتوقعات العامة لأداء السوق:")
            print(analyzer.market_forecast())
        
        elif choice == "10":
            symbol = input("أدخل رمز السهم لرسم أدائه: ").upper()
            analyzer.plot_performance(symbol)
            
        elif choice == "11":
            print("شكرًا لاستخدامك البرنامج. إلى اللقاء!")
            break
            
        else:
            print("اختيار غير صحيح، يرجى المحاولة مرة أخرى")

if __name__ == "__main__":
    main()
