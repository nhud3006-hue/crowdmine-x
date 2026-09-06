import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import random
import numpy as np
import matplotlib.pyplot as plt
import sys
import os

# Thêm đường dẫn để import module
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import model LSTM và class lấy dữ liệu thật
from src.models.lstm_flood_model import FloodLSTM
from src.data_fetchers.real_water_data import RealWaterFetcher

# ===============================
# CLASS LẤY DỮ LIỆU THỜI TIẾT
# ===============================
class WeatherFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_current_weather(self, latitude, longitude):
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current_weather": True,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "Asia/Ho_Chi_Minh",
            "forecast_days": 1
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            current = data.get("current_weather", {})
            hourly = data.get("hourly", {})
            now = datetime.now().hour
            idx = min(now, len(hourly.get("temperature_2m", [])) - 1) if hourly else 0
            temperature = hourly["temperature_2m"][idx] if "temperature_2m" in hourly else current.get("temperature")
            humidity = hourly["relative_humidity_2m"][idx] if "relative_humidity_2m" in hourly else None
            precipitation = hourly["precipitation"][idx] if "precipitation" in hourly else 0
            wind_speed = hourly["wind_speed_10m"][idx] if "wind_speed_10m" in hourly else current.get("windspeed")
            return {
                "temperature": temperature,
                "precipitation": precipitation,
                "humidity": humidity,
                "wind_speed": wind_speed,
                "time": current.get("time", datetime.now().strftime("%Y-%m-%d %H:%M"))
            }
        except:
            return None

# ===============================
# CLASS USGS
# ===============================
class USGSFetcher:
    def __init__(self):
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def fetch_earthquakes(self, days=7, min_magnitude=3.0):
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        params = {
            "format": "geojson",
            "starttime": start_date.strftime("%Y-%m-%d"),
            "endtime": end_date.strftime("%Y-%m-%d"),
            "minmagnitude": min_magnitude,
            "minlatitude": 8.0,
            "maxlatitude": 24.0,
            "minlongitude": 102.0,
            "maxlongitude": 110.0,
            "orderby": "time"
        }
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            events = []
            for feature in data.get("features", []):
                props = feature["properties"]
                geom = feature["geometry"]
                events.append({
                    "time": datetime.fromtimestamp(props["time"] / 1000),
                    "place": props.get("place", "Unknown"),
                    "magnitude": props.get("mag", 0),
                    "depth_km": geom["coordinates"][2],
                    "latitude": geom["coordinates"][1],
                    "longitude": geom["coordinates"][0]
                })
            return pd.DataFrame(events)
        except:
            return pd.DataFrame()

# ===============================
# CLASS NASA EONET
# ===============================
class EONETFetcher:
    def __init__(self):
        self.base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    
    def fetch_events(self, limit=10):
        params = {"status": "open", "limit": limit}
        try:
            response = requests.get(self.base_url, params=params, timeout=10)
            data = response.json()
            events = []
            for event in data.get("events", []):
                categories = event.get("categories", [])
                category = categories[0].get("title", "Unknown") if categories else "Unknown"
                geometry = event.get("geometry", [{}])[0]
                coords = geometry.get("coordinates", [])
                date_str = geometry.get("date", "")
                events.append({
                    "title": event.get("title", "No title"),
                    "category": category,
                    "status": event.get("status", "unknown"),
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "date": datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
                })
            return pd.DataFrame(events)
        except:
            return pd.DataFrame()

# ===============================
# MOCK EARTHQUAKES
# ===============================
def get_mock_earthquakes():
    now = datetime.now()
    data = []
    for i in range(5):
        data.append({
            "time": now - timedelta(hours=i*6),
            "place": f"Cách {random.choice(['Kon Tum', 'Điện Biên', 'Lào Cai', 'Quảng Nam'])} {random.randint(10,50)} km",
            "magnitude": round(random.uniform(3.0, 5.5), 1),
            "depth_km": round(random.uniform(5, 30), 1),
            "latitude": 14 + random.uniform(-3, 5),
            "longitude": 108 + random.uniform(-3, 3)
        })
    return pd.DataFrame(data)

# ===============================
# DANH SÁCH TỈNH THÀNH VIỆT NAM (63 TỈNH THÀNH) VỚI TỌA ĐỘ
# ===============================
CITY_COORDS = {
    "An Giang": {"lat": 10.5, "lon": 105.1},
    "Bà Rịa - Vũng Tàu": {"lat": 10.4, "lon": 107.1},
    "Bắc Giang": {"lat": 21.3, "lon": 106.2},
    "Bắc Kạn": {"lat": 22.1, "lon": 105.8},
    "Bạc Liêu": {"lat": 9.3, "lon": 105.7},
    "Bắc Ninh": {"lat": 21.2, "lon": 106.1},
    "Bến Tre": {"lat": 10.2, "lon": 106.4},
    "Bình Định": {"lat": 13.8, "lon": 109.1},
    "Bình Dương": {"lat": 11.1, "lon": 106.6},
    "Bình Phước": {"lat": 11.6, "lon": 106.9},
    "Bình Thuận": {"lat": 11.1, "lon": 108.1},
    "Cà Mau": {"lat": 9.2, "lon": 105.2},
    "Cần Thơ": {"lat": 10.0, "lon": 105.7},
    "Cao Bằng": {"lat": 22.7, "lon": 106.3},
    "Đà Nẵng": {"lat": 16.1, "lon": 108.2},
    "Đắk Lắk": {"lat": 12.7, "lon": 108.0},
    "Đắk Nông": {"lat": 12.0, "lon": 107.7},
    "Điện Biên": {"lat": 21.4, "lon": 103.0},
    "Đồng Nai": {"lat": 11.0, "lon": 107.2},
    "Đồng Tháp": {"lat": 10.5, "lon": 105.6},
    "Gia Lai": {"lat": 13.8, "lon": 108.2},
    "Hà Giang": {"lat": 22.8, "lon": 104.9},
    "Hà Nam": {"lat": 20.6, "lon": 105.9},
    "Hà Nội": {"lat": 21.0, "lon": 105.9},
    "Hà Tĩnh": {"lat": 18.3, "lon": 105.9},
    "Hải Dương": {"lat": 20.9, "lon": 106.3},
    "Hải Phòng": {"lat": 20.8, "lon": 106.7},
    "Hậu Giang": {"lat": 9.8, "lon": 105.6},
    "Hòa Bình": {"lat": 20.8, "lon": 105.3},
    "Hưng Yên": {"lat": 20.6, "lon": 106.1},
    "Khánh Hòa": {"lat": 12.2, "lon": 109.1},
    "Kiên Giang": {"lat": 10.0, "lon": 105.0},
    "Kon Tum": {"lat": 14.3, "lon": 108.0},
    "Lai Châu": {"lat": 22.4, "lon": 103.4},
    "Lâm Đồng": {"lat": 11.9, "lon": 108.4},
    "Lạng Sơn": {"lat": 21.8, "lon": 106.8},
    "Lào Cai": {"lat": 22.5, "lon": 103.9},
    "Long An": {"lat": 10.6, "lon": 106.4},
    "Nam Định": {"lat": 20.4, "lon": 106.2},
    "Nghệ An": {"lat": 19.2, "lon": 105.6},
    "Ninh Bình": {"lat": 20.2, "lon": 105.9},
    "Ninh Thuận": {"lat": 11.6, "lon": 108.9},
    "Phú Thọ": {"lat": 21.4, "lon": 105.2},
    "Phú Yên": {"lat": 13.1, "lon": 109.2},
    "Quảng Bình": {"lat": 17.5, "lon": 106.6},
    "Quảng Nam": {"lat": 15.6, "lon": 108.2},
    "Quảng Ngãi": {"lat": 15.1, "lon": 108.8},
    "Quảng Ninh": {"lat": 21.0, "lon": 107.3},
    "Quảng Trị": {"lat": 16.8, "lon": 107.1},
    "Sóc Trăng": {"lat": 9.6, "lon": 105.9},
    "Sơn La": {"lat": 21.3, "lon": 103.9},
    "Tây Ninh": {"lat": 11.3, "lon": 106.1},
    "Thái Bình": {"lat": 20.4, "lon": 106.3},
    "Thái Nguyên": {"lat": 21.6, "lon": 105.8},
    "Thanh Hóa": {"lat": 19.8, "lon": 105.8},
    "Thừa Thiên Huế": {"lat": 16.5, "lon": 107.6},
    "Tiền Giang": {"lat": 10.4, "lon": 106.2},
    "TP Hồ Chí Minh": {"lat": 10.8, "lon": 106.6},
    "Trà Vinh": {"lat": 9.9, "lon": 106.3},
    "Tuyên Quang": {"lat": 21.8, "lon": 105.2},
    "Vĩnh Long": {"lat": 10.3, "lon": 105.9},
    "Vĩnh Phúc": {"lat": 21.3, "lon": 105.6},
    "Yên Bái": {"lat": 21.7, "lon": 104.9}
}

# ===============================
# GIAO DIỆN STREAMLIT
# ===============================
st.set_page_config(page_title="CrowdMine-X", page_icon="🌍", layout="wide")
st.title("🌍 CrowdMine-X")
st.subheader("Hệ thống Cảnh báo Thiên tai Dây chuyền với AI và Cộng đồng")

with st.sidebar:
    st.header("📍 Khu vực")
    region = st.selectbox("Chọn tỉnh/thành phố", list(CITY_COORDS.keys()))
    days = st.slider("📅 Số ngày lấy dữ liệu động đất", 1, 30, 7)
    min_mag = st.slider("📊 Độ lớn tối thiểu", 2.0, 6.0, 3.0, 0.5)
    st.divider()
    st.caption(f"🔄 Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

coords = CITY_COORDS.get(region, {"lat": 21.0285, "lon": 105.8542})

# ---- Thời tiết ----
weather_fetcher = WeatherFetcher()
weather = weather_fetcher.get_current_weather(coords["lat"], coords["lon"])
if weather:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🌡️ Nhiệt độ", f"{weather['temperature']}°C")
    col2.metric("💧 Độ ẩm", f"{weather['humidity']}%" if weather['humidity'] else "N/A")
    col3.metric("🌧️ Lượng mưa", f"{weather['precipitation']} mm")
    col4.metric("💨 Gió", f"{weather['wind_speed']} km/h" if weather['wind_speed'] else "N/A")
else:
    st.warning("⚠️ Không thể lấy dữ liệu thời tiết.")

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Bảng điều khiển",
    "🗺️ Bản đồ rủi ro",
    "📢 Báo cáo cộng đồng",
    "⚠️ Cảnh báo dây chuyền",
    "🌊 Dự báo lũ LSTM"
])

# ---- TAB 1: Bảng điều khiển ----
with tab1:
    st.header("📋 Động đất gần đây")
    with st.spinner("📡 Đang tải dữ liệu từ USGS..."):
        fetcher = USGSFetcher()
        df = fetcher.fetch_earthquakes(days=days, min_magnitude=min_mag)
    if df.empty:
        st.info("ℹ️ Không có dữ liệu thật. Hiển thị dữ liệu mô phỏng.")
        df = get_mock_earthquakes()
    st.dataframe(df[["time", "place", "magnitude", "depth_km"]], use_container_width=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("Số trận", len(df))
    col2.metric("Độ lớn TB", f"{df['magnitude'].mean():.1f}")
    col3.metric("Mạnh nhất", f"{df['magnitude'].max():.1f}")
    st.bar_chart(df["magnitude"])
    st.divider()
    st.subheader("🛰️ Sự kiện từ NASA EONET")
    with st.spinner("Đang tải..."):
        eonet = EONETFetcher()
        events_df = eonet.fetch_events(limit=10)
    if not events_df.empty:
        st.dataframe(events_df[["title", "category", "status"]], use_container_width=True)
    else:
        st.info("Không có sự kiện nào.")

# ---- TAB 2: Bản đồ ----
with tab2:
    st.header("🗺️ Bản đồ rủi ro")
    # Sử dụng danh sách tỉnh thành đã có
    map_data = pd.DataFrame([
        {"city": "Hà Nội", "lat": 21.0, "lon": 105.9, "risk": 3},
        {"city": "Đà Nẵng", "lat": 16.1, "lon": 108.2, "risk": 4},
        {"city": "TP Hồ Chí Minh", "lat": 10.8, "lon": 106.6, "risk": 2},
        {"city": "Huế", "lat": 16.5, "lon": 107.6, "risk": 5},
        {"city": "Kon Tum", "lat": 14.3, "lon": 108.0, "risk": 4},
        {"city": "Đà Lạt", "lat": 11.9, "lon": 108.4, "risk": 2},
        {"city": "Hải Phòng", "lat": 20.8, "lon": 106.7, "risk": 3},
        {"city": "Cần Thơ", "lat": 10.0, "lon": 105.7, "risk": 2},
        {"city": "Quảng Nam", "lat": 15.6, "lon": 108.2, "risk": 4},
        {"city": "Thanh Hóa", "lat": 19.8, "lon": 105.8, "risk": 3}
    ])
    st.map(map_data, size="risk", zoom=6)
    st.dataframe(map_data, use_container_width=True)

# ---- TAB 3: Báo cáo cộng đồng ----
with tab3:
    st.header("📢 Báo cáo cộng đồng")
    with st.form("report_form"):
        report_type = st.selectbox("Loại báo cáo", ["An toàn", "Nguy hiểm", "Hiện tượng lạ", "Thiệt hại"])
        location = st.text_input("📍 Vị trí")
        description = st.text_area("📝 Mô tả")
        submitted = st.form_submit_button("Gửi báo cáo")
        if submitted and location and description:
            st.success("✅ Cảm ơn bạn!")
            st.balloons()

# ---- TAB 4: Cảnh báo dây chuyền ----
with tab4:
    st.header("⚠️ Dự báo dây chuyền")
    st.error("""
    🔴 **Cảnh báo Đỏ: Bão số 3**
    - Đổ bộ vào Đà Nẵng – Quảng Nam trong 24h tới.
    - **Tác động dây chuyền:**
        - Lũ lụt: 85%
        - Sạt lở: 70%
        - Vỡ đê: 60%
    - **Khuyến nghị:** Sơ tán khẩn cấp!
    """)
    st.warning("""
    🟡 **Cảnh báo Vàng: Động đất 4.2 tại Kon Tum**
    - Nguy cơ dư chấn: 40% trong 48h.
    """)

# ---- TAB 5: DỰ BÁO LŨ LSTM ----
with tab5:
    st.header("🌊 Dự báo mực nước sông bằng LSTM")
    st.markdown("Mô hình dự báo chuỗi thời gian dựa trên dữ liệu lịch sử (thật từ NOAA hoặc mô phỏng).")
    
    if st.button("🔄 Tải dữ liệu thật và huấn luyện mô hình"):
        with st.spinner("📡 Đang tải dữ liệu thủy văn từ NOAA..."):
            fetcher = RealWaterFetcher()
            df = fetcher.fetch_water_level(days=365)
            if df is not None and not df.empty:
                st.session_state['flood_data'] = df
                st.success(f"✅ Đã tải {len(df)} dòng dữ liệu (dữ liệu thật nếu có, hoặc mô phỏng)")
            else:
                st.error("❌ Không thể tải dữ liệu.")
                st.stop()
        
        with st.spinner("🧠 Đang huấn luyện mô hình LSTM..."):
            try:
                lstm = FloodLSTM(lookback=10, n_features=1)
                X, y = lstm.prepare_data(df, target_col='water_level')
                split = int(0.8 * len(X))
                X_train, X_val = X[:split], X[split:]
                y_train, y_val = y[:split], y[split:]
                lstm.build_model(input_shape=(lstm.lookback, 1))
                history = lstm.train(X_train, y_train, X_val, y_val, epochs=50, batch_size=32)
                st.session_state['lstm_model'] = lstm
                st.session_state['lstm_trained'] = True
                st.session_state['flood_data'] = df
                last_seq = X[-1]
                preds = lstm.predict_future(last_seq, steps=7)
                st.session_state['forecast_7d'] = preds
                st.success("✅ Huấn luyện hoàn tất! Xem kết quả dưới đây.")
            except Exception as e:
                st.error(f"❌ Lỗi huấn luyện: {e}")
                st.info("💡 Hãy đảm bảo đã cài đặt TensorFlow và các thư viện cần thiết.")
                st.stop()
    
    if st.session_state.get('lstm_trained', False):
        df_hist = st.session_state['flood_data']
        preds = st.session_state['forecast_7d']
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(df_hist['date'][-30:], df_hist['water_level'][-30:], label='Lịch sử (30 ngày gần nhất)', color='blue')
        last_date = df_hist['date'].iloc[-1]
        future_dates = [last_date + timedelta(days=i+1) for i in range(7)]
        ax.plot(future_dates, preds, label='Dự báo 7 ngày', color='red', marker='o', linestyle='--')
        ax.set_xlabel('Ngày')
        ax.set_ylabel('Mực nước (m)')
        ax.set_title('Dự báo mực nước sông (LSTM) - Dữ liệu từ NOAA')
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)
        forecast_df = pd.DataFrame({
            'Ngày': [d.strftime('%d/%m/%Y') for d in future_dates],
            'Mực nước dự báo (m)': [round(p, 2) for p in preds]
        })
        st.dataframe(forecast_df, use_container_width=True)
        max_level = max(preds)
        avg_level = np.mean(preds)
        st.subheader("📊 Đánh giá nguy cơ lũ")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📈 Mực nước cao nhất", f"{max_level:.2f} m")
            st.metric("📊 Mực nước trung bình", f"{avg_level:.2f} m")
        with col2:
            if max_level > 8.0:
                st.error("🔴 Cảnh báo: Nguy cơ lũ lớn!")
            elif max_level > 6.5:
                st.warning("🟡 Cảnh báo: Nguy cơ ngập lụt!")
            else:
                st.success("🟢 An toàn.")
    else:
        st.info("💡 Nhấn nút bên trên để tải dữ liệu thật và huấn luyện mô hình LSTM.")