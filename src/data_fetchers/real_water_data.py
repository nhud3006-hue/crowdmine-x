import requests
import pandas as pd
from datetime import datetime, timedelta

class RealWaterFetcher:
    def __init__(self):
        # Sử dụng API của NOAA (miễn phí, không cần đăng ký)
        self.base_url = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"
    
    def fetch_water_level(self, station_id='9414290', start_date=None, end_date=None, days=30):
        """
        Lấy dữ liệu mực nước thực tế từ NOAA
        station_id: mã trạm (mặc định là San Francisco, em có thể thay sau)
        days: số ngày lấy dữ liệu
        """
        if start_date is None:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
        
        # Định dạng ngày theo yêu cầu của NOAA: YYYYMMDD
        start_str = start_date.strftime("%Y%m%d")
        end_str = end_date.strftime("%Y%m%d")
        
        params = {
            'station': station_id,
            'date': f'{start_str}%20{end_str}',
            'product': 'water_level',
            'datum': 'MSL',
            'units': 'metric',
            'time_zone': 'UTC',
            'format': 'json'
        }
        
        try:
            print(f"📡 Đang tải dữ liệu từ NOAA cho trạm {station_id}...")
            response = requests.get(self.base_url, params=params, timeout=15)
            data = response.json()
            
            records = data.get('data', [])
            if not records:
                print("⚠️ Không có dữ liệu. Thử dùng dữ liệu mẫu.")
                return self.get_mock_data(days)
            
            df = pd.DataFrame(records)
            df['t'] = pd.to_datetime(df['t'])
            df['v'] = pd.to_numeric(df['v'])
            df = df.rename(columns={'t': 'date', 'v': 'water_level'})
            
            # Chỉ lấy các cột cần thiết
            df = df[['date', 'water_level']]
            df = df.sort_values('date')
            print(f"✅ Đã lấy {len(df)} dòng dữ liệu từ NOAA")
            return df
            
        except Exception as e:
            print(f"❌ Lỗi khi lấy dữ liệu thật: {e}")
            print("🔄 Sử dụng dữ liệu mẫu để demo.")
            return self.get_mock_data(days)
    
    def get_mock_data(self, days=30):
        """Tạo dữ liệu giả lập khi không lấy được dữ liệu thật"""
        print("📊 Đang tạo dữ liệu mô phỏng...")
        dates = pd.date_range(end=datetime.now(), periods=days)
        # Mô phỏng mực nước theo chu kỳ thủy triều
        np = __import__('numpy')
        water_level = 3 + 0.8 * np.sin(np.arange(days) * 2 * np.pi / 12.4) + 0.2 * np.random.randn(days)
        water_level = np.maximum(water_level, 0.5)
        
        df = pd.DataFrame({
            'date': dates,
            'water_level': water_level
        })
        return df

# ===============================
# TEST THỬ
# ===============================
if __name__ == "__main__":
    fetcher = RealWaterFetcher()
    
    # Thử lấy dữ liệu 30 ngày gần nhất
    df = fetcher.fetch_water_level(days=30)
    print("\n📊 10 dòng đầu tiên:")
    print(df.head(10))
    print(f"\n📈 Mực nước trung bình: {df['water_level'].mean():.2f} m")
    print(f"📈 Mực nước cao nhất: {df['water_level'].max():.2f} m")
    print(f"📈 Mực nước thấp nhất: {df['water_level'].min():.2f} m")