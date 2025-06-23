import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.stock_data = pd.DataFrame()
        
    def set_api_key(self, api_key):
        """وظيفة لربط مفتاح API"""
        self.api_key = api_key
        print("تم حفظ مفتاح API بنجاح")
        
    def fetch_data(self, symbol, period="1mo"):
        """جلب بيانات السهم من API"""
        if not self.api_key:
            raise ValueError("لم يتم تعيين مفتاح API")
            
        url = f"https://api.example.com/stocks/{symbol}?apikey={self.api_key}&period={period}"
        response = requests.get(url)
        
        if response.status_code == 200:
            data = response.json()
            df = pd.DataFrame(data['prices'])
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            return df
        else:
            raise ConnectionError("فشل في جلب البيانات")
    
    def best_liquidity(self, stocks):
        """الأفضل من حيث السيولة"""
        liquidity_data = []
        for symbol in stocks:
            data = self.fetch_data(symbol)
            avg_volume = data['volume'].mean()
            liquidity_data.append({'symbol': symbol, 'liquidity': avg_volume})
        
        df = pd.DataFrame(liquidity_data)
        return df.sort_values('liquidity', ascending=False).head(10)
    
    def top_gainers(self, stocks):
        """الأكثر ارتفاعًا"""
        gainers = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="1d")
            change = (data['close'].iloc[-1] - data['open'].iloc[-1]) / data['open'].iloc[-1] * 100
            gainers.append({'symbol': symbol, 'gain': change})
        
        df = pd.DataFrame(gainers)
        return df.sort_values('gain', ascending=False).head(10)
    
    def most_traded(self, stocks):
        """الأكثر تداولًا"""
        traded = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="1d")
            volume = data['volume'].iloc[-1]
            traded.append({'symbol': symbol, 'volume': volume})
        
        df = pd.DataFrame(traded)
        return df.sort_values('volume', ascending=False).head(10)
    
    def three_month_performance(self, stocks):
        """الأفضل أداءً لمدة 3 أشهر"""
        performance = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            start_price = data['close'].iloc[0]
            end_price = data['close'].iloc[-1]
            change = (end_price - start_price) / start_price * 100
            performance.append({'symbol': symbol, '3mo_change': change})
        
        df = pd.DataFrame(performance)
        return df.sort_values('3mo_change', ascending=False).head(10)
    
    def six_month_performance(self, stocks):
        """الأفضل أداءً لمدة 6 أشهر"""
        performance = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="6mo")
            start_price = data['close'].iloc[0]
            end_price = data['close'].iloc[-1]
            change = (end_price - start_price) / start_price * 100
            performance.append({'symbol': symbol, '6mo_change': change})
        
        df = pd.DataFrame(performance)
        return df.sort_values('6mo_change', ascending=False).head(10)
    
    def below_50ma(self, stocks):
        """الأسهم تحت متوسط 50 يوم"""
        below_50 = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            ma50 = data['close'].rolling(50).mean().iloc[-1]
            current_price = data['close'].iloc[-1]
            if current_price < ma50:
                below_50.append({'symbol': symbol, 'price': current_price, '50ma': ma50})
        
        return pd.DataFrame(below_50)
    
    def below_35ma(self, stocks):
        """الأسهم تحت متوسط 35 يوم"""
        below_35 = []
        for symbol in stocks:
            data = self.fetch_data(symbol, period="3mo")
            ma35 = data['close'].rolling(35).mean().iloc[-1]
            current_price = data['close'].iloc[-1]
            if current_price < ma35:
                below_35.append({'symbol': symbol, 'price': current_price, '35ma': ma35})
        
        return pd.DataFrame(below_35)
    
    def vs_market_index(self, symbol, market_index="^GSPC"):
        """قياس أداء السهم مقابل المؤشر العام"""
        stock_data = self.fetch_data(symbol, period="1y")
        index_data = self.fetch_data(market_index, period="1y")
        
        stock_return = (stock_data['close'].iloc[-1] - stock_data['close'].iloc[0]) / stock_data['close'].iloc[0] * 100
        index_return = (index_data['close'].iloc[-1] - index_data['close'].iloc[0]) / index_data['close'].iloc[0] * 100
        
        return {
            'symbol': symbol,
            'stock_return': stock_return,
            'index': market_index,
            'index_return': index_return,
            'outperformance': stock_return - index_return
        }
    
    def market_forecast(self):
        """الأداء المتوقع للسوق"""
        # نموذج مبسط للتنبؤ (في الواقع يحتاج لنموذج متقدم)
        sp500 = self.fetch_data("^GSPC", period="1y")
        last_month = sp500['close'].pct_change(21).iloc[-1] * 100
        
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
        """رسم بياني لأداء السهم"""
        data = self.fetch_data(symbol, period)
        data['close'].plot(title=f"أداء {symbol} خلال آخر {period}")
        plt.ylabel("السعر")
        plt.xlabel("التاريخ")
        plt.grid()
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
    10 - إدخال مفتاح API
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
            api_key = input("أدخل مفتاح API: ")
            analyzer.set_api_key(api_key)
            
        elif choice == "11":
            print("شكرًا لاستخدامك البرنامج. إلى اللقاء!")
            break
            
        else:
            print("اختيار غير صحيح، يرجى المحاولة مرة أخرى")

if __name__ == "__main__":
    main()
