import requests
import pandas as pd
import json
from datetime import datetime, timedelta

class StockAnalyzer:
    def __init__(self, api_key="CC2Q652M57ECE2UV"):  # هنا نضع مفتاح API الافتراضي
        self.api_key = api_key
        self.base_url = "https://www.alphavantage.co/query"
        self.stock_data = {}  # هذا يجب أن يكون قاموسًا فارغًا
        
    def set_api_key(self, api_key):
        """وظيفة لربط مفتاح API"""
        self.api_key = api_key
        print("تم حفظ مفتاح API بنجاح")
        
    def fetch_data(self, function, symbol):
        """جلب بيانات السهم من API"""
        if not self.api_key:
            raise ValueError("لم يتم تعيين مفتاح API")
            
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key,
            "outputsize": "compact",
            "datatype": "json"
        }
        
        response = requests.get(self.base_url, params=params)
        data = response.json()
        
        if "Error Message" in data:
            raise ValueError(f"خطأ في جلب البيانات: {data['Error Message']}")
            
        return data
    
    def get_time_series(self, symbol):
        """الحصول على السلاسل الزمنية للسهم"""
        if symbol not in self.stock_data:
            data = self.fetch_data("TIME_SERIES_DAILY", symbol)
            df = pd.DataFrame(data['Time Series (Daily)']).T
            df = df.rename(columns={
                '1. open': 'open',
                '2. high': 'high',
                '3. low': 'low',
                '4. close': 'close',
                '5. volume': 'volume'
            })
            df = df.apply(pd.to_numeric)
            self.stock_data[symbol] = df
        return self.stock_data[symbol]
    
    def best_liquidity(self, stocks):
        """الأفضل من حيث السيولة"""
        liquidity = []
        for symbol in stocks:
            try:
                df = self.get_time_series(symbol)
                avg_volume = df['volume'].mean()
                liquidity.append({'symbol': symbol, 'متوسط السيولة': f"{avg_volume:,.0f}"})
            except:
                continue
        
        return pd.DataFrame(liquidity).sort_values('متوسط السيولة', ascending=False).head(10)
    
    def top_gainers(self, stocks):
        """الأكثر ارتفاعًا"""
        gainers = []
        for symbol in stocks:
            try:
                df = self.get_time_series(symbol)
                last_day = df.iloc[0]
                prev_day = df.iloc[1]
                change = (last_day['close'] - prev_day['close']) / prev_day['close'] * 100
                gainers.append({'symbol': symbol, 'النسبة (%)': f"{change:.2f}%"})
            except:
                continue
        
        return pd.DataFrame(gainers).sort_values('النسبة (%)', ascending=False).head(10)
    
    def most_traded(self, stocks):
        """الأكثر تداولًا"""
        volumes = []
        for symbol in stocks:
            try:
                df = self.get_time_series(symbol)
                last_volume = df.iloc[0]['volume']
                volumes.append({'symbol': symbol, 'حجم التداول': f"{last_volume:,.0f}"})
            except:
                continue
        
        return pd.DataFrame(volumes).sort_values('حجم التداول', ascending=False).head(10)
    
    def n_month_performance(self, stocks, months):
        """الأفضل أداءً لعدد معين من الأشهر"""
        performances = []
        for symbol in stocks:
            try:
                # جلب البيانات التاريخية
                params = {
                    "function": "TIME_SERIES_MONTHLY",
                    "symbol": symbol,
                    "apikey": self.api_key,
                    "datatype": "json"
                }
                response = requests.get(self.base_url, params=params)
                data = response.json()['Monthly Time Series']
                
                # تحويل البيانات إلى DataFrame
                df = pd.DataFrame(data).T.iloc[:months+1]
                df = df.rename(columns={
                    '1. open': 'open',
                    '2. high': 'high',
                    '3. low': 'low',
                    '4. close': 'close',
                    '5. volume': 'volume'
                })
                df = df.apply(pd.to_numeric)
                
                # حساب الأداء
                start_price = df.iloc[-1]['close']
                end_price = df.iloc[0]['close']
                change = (end_price - start_price) / start_price * 100
                performances.append({'symbol': symbol, f'الأداء ({months} أشهر) (%)': f"{change:.2f}%"})
            except:
                continue
        
        return pd.DataFrame(performances).sort_values(f'الأداء ({months} أشهر) (%)', ascending=False).head(10)
    
    def below_moving_average(self, stocks, window):
        """الأسهم تحت المتوسط المتحرك"""
        below_ma = []
        for symbol in stocks:
            try:
                df = self.get_time_series(symbol)
                ma = df['close'].rolling(window=window).mean().iloc[0]
                current_price = df.iloc[0]['close']
                
                if current_price < ma:
                    below_ma.append({
                        'symbol': symbol,
                        'السعر الحالي': f"{current_price:.2f}",
                        f'متوسط {window} يوم': f"{ma:.2f}",
                        'الفرق (%)': f"{(ma - current_price)/current_price*100:.2f}%"
                    })
            except:
                continue
        
        return pd.DataFrame(below_ma)
    
    def vs_market_index(self, symbol, market_index="SPY"):
        """قياس أداء السهم مقابل المؤشر العام"""
        try:
            stock_data = self.get_time_series(symbol)
            index_data = self.get_time_series(market_index)
            
            stock_return = (stock_data.iloc[0]['close'] - stock_data.iloc[-1]['close']) / stock_data.iloc[-1]['close'] * 100
            index_return = (index_data.iloc[0]['close'] - index_data.iloc[-1]['close']) / index_data.iloc[-1]['close'] * 100
            
            return {
                'السهم': symbol,
                'أداء السهم (%)': f"{stock_return:.2f}%",
                'المؤشر': market_index,
                'أداء المؤشر (%)': f"{index_return:.2f}%",
                'المقارنة': "أفضل" if stock_return > index_return else "أضعف"
            }
        except:
            return {"خطأ": "لا يمكن إجراء المقارنة"}
    
    def market_forecast(self, market_index="SPY"):
        """الأداء المتوقع للسوق"""
        try:
            df = self.get_time_series(market_index)
            last_month = df.head(20)  # حوالي شهر تداول
            
            # تحليل بسيط للأداء
            last_close = last_month.iloc[0]['close']
            ma50 = last_month['close'].rolling(50).mean().iloc[0]
            ma20 = last_month['close'].rolling(20).mean().iloc[0]
            
            if last_close > ma50 and last_close > ma20:
                return "اتجاه صعودي قوي"
            elif last_close > ma50:
                return "اتجاه صعودي معتدل"
            elif last_close < ma50 and last_close < ma20:
                return "اتجاه هبوطي قوي"
            else:
                return "سوق متذبذب"
        except:
            return "لا يمكن التنبؤ بالسوق حالياً"
    
    def save_report(self, filename="stock_report.txt"):
        """حفظ التقرير في ملف"""
        report = "تقرير أداء الأسهم\n===================\n\n"
        
        report += "1. الأسهم الأفضل سيولة:\n"
        report += self.best_liquidity(self.stock_list).to_string(index=False) + "\n\n"
        
        report += "2. الأسهم الأكثر ارتفاعاً:\n"
        report += self.top_gainers(self.stock_list).to_string(index=False) + "\n\n"
        
        report += "3. الأسهم الأكثر تداولاً:\n"
        report += self.most_traded(self.stock_list).to_string(index=False) + "\n\n"
        
        report += "4. أفضل أداء لـ 3 أشهر:\n"
        report += self.n_month_performance(self.stock_list, 3).to_string(index=False) + "\n\n"
        
        report += "5. أفضل أداء لـ 6 أشهر:\n"
        report += self.n_month_performance(self.stock_list, 6).to_string(index=False) + "\n\n"
        
        report += "6. الأسهم تحت متوسط 50 يوم:\n"
        report += self.below_moving_average(self.stock_list, 50).to_string(index=False) + "\n\n"
        
        report += "7. الأسهم تحت متوسط 35 يوم:\n"
        report += self.below_moving_average(self.stock_list, 35).to_string(index=False) + "\n\n"
        
        report += "8. أداء السوق المتوقع:\n"
        report += self.market_forecast() + "\n"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report)
        
        return f"تم حفظ التقرير في {filename}"

# واجهة المستخدم
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
    11 - حفظ التقرير الكامل
    12 - الخروج
    """)
    
    analyzer = StockAnalyzer()
    analyzer.stock_list = ["AAPL", "MSFT", "GOOG", "AMZN", "META", "TSLA", "NVDA", "JPM", "JNJ", "V"]
    
    while True:
        choice = input("اختر رقم الوظيفة (1-12): ")
        
        if choice == "1":
            print("\nالأسهم الأفضل من حيث السيولة:")
            print(analyzer.best_liquidity(analyzer.stock_list))
            
        elif choice == "2":
            print("\nالأسهم الأكثر ارتفاعًا:")
            print(analyzer.top_gainers(analyzer.stock_list))
            
        elif choice == "3":
            print("\nالأسهم الأكثر تداولًا:")
            print(analyzer.most_traded(analyzer.stock_list))
            
        elif choice == "4":
            print("\nالأفضل أداءً لمدة 3 أشهر:")
            print(analyzer.n_month_performance(analyzer.stock_list, 3))
            
        elif choice == "5":
            print("\nالأفضل أداءً لمدة 6 أشهر:")
            print(analyzer.n_month_performance(analyzer.stock_list, 6))
            
        elif choice == "6":
            print("\nالأسهم تحت متوسط 50 يوم:")
            print(analyzer.below_moving_average(analyzer.stock_list, 50))
            
        elif choice == "7":
            print("\nالأسهم تحت متوسط 35 يوم:")
            print(analyzer.below_moving_average(analyzer.stock_list, 35))
            
        elif choice == "8":
            symbol = input("أدخل رمز السهم (افتراضي AAPL): ") or "AAPL"
            print(f"\nأداء {symbol} مقابل المؤشر:")
            print(analyzer.vs_market_index(symbol))
            
        elif choice == "9":
            print("\nالتوقعات العامة لأداء السوق:")
            print(analyzer.market_forecast())
            
        elif choice == "10":
            api_key = input("أدخل مفتاح Alpha Vantage API: ")
            analyzer.set_api_key(api_key)
            
        elif choice == "11":
            filename = input("أدخل اسم الملف (افتراضي stock_report.txt): ") or "stock_report.txt"
            print(analyzer.save_report(filename))
            
        elif choice == "12":
            print("شكرًا لاستخدامك البرنامج. إلى اللقاء!")
            break
            
        else:
            print("اختيار غير صحيح، يرجى المحاولة مرة أخرى")

if __name__ == "__main__":
    main()
