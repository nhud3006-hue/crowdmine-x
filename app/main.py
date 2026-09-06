import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import random

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
# CLASS LẤY DỮ LIỆU ĐỘNG ĐẤT USGS
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
# CLASS LẤY DỮ LIỆU NASA EONET
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
# TỌA ĐỘ TỈNH THÀNH (MỞ RỘNG 44 TỈNH)
# ===============================
CITY_COORDS = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542},
    "Hải Phòng": {"lat": 20.8449, "lon": 106.6881},
    "Hải Dương": {"lat": 20.9409, "lon": 106.3133},
    "Hưng Yên": {"lat": 20.6464, "lon": 106.0511},
    "Nam Định": {"lat": 20.4333, "lon": 106.1667},
    "Thái Bình": {"lat": 20.4461, "lon": 106.3369},
    "Ninh Bình": {"lat": 20.2500, "lon": 105.9667},
    "Điện Biên": {"lat": 21.3833, "lon": 103.0167},
    "Sơn La": {"lat": 21.3167, "lon": 103.9167},
    "Lào Cai": {"lat": 22.4833, "lon": 103.9667},
    "Yên Bái": {"lat": 21.7000, "lon": 104.8667},
    "Thái Nguyên": {"lat": 21.5944, "lon": 105.8483},
    "Bắc Giang": {"lat": 21.2667, "lon": 106.2000},
    "Quảng Ninh": {"lat": 20.9500, "lon": 107.0833},
    "Thanh Hóa": {"lat": 19.8000, "lon": 105.7667},
    "Nghệ An": {"lat": 18.6667, "lon": 105.6667},
    "Hà Tĩnh": {"lat": 18.3333, "lon": 105.9000},
    "Quảng Bình": {"lat": 17.4667, "lon": 106.6000},
    "Quảng Trị": {"lat": 16.7500, "lon": 107.1833},
    "Huế": {"lat": 16.4637, "lon": 107.5909},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022},
    "Quảng Nam": {"lat": 15.5394, "lon": 108.0190},
    "Quảng Ngãi": {"lat": 15.1167, "lon": 108.8000},
    "Bình Định": {"lat": 13.7667, "lon": 109.2333},
    "Phú Yên": {"lat": 13.0833, "lon": 109.3000},
    "Nha Trang": {"lat": 12.2388, "lon": 109.1967},
    "Ninh Thuận": {"lat": 11.5667, "lon": 108.9833},
    "Bình Thuận": {"lat": 10.9333, "lon": 108.1000},
    "Kon Tum": {"lat": 14.3493, "lon": 108.0000},
    "Gia Lai": {"lat": 13.9833, "lon": 108.0000},
    "Đắk Lắk": {"lat": 12.6667, "lon": 108.0500},
    "Đắk Nông": {"lat": 12.0000, "lon": 107.7000},
    "Lâm Đồng (Đà Lạt)": {"lat": 11.9404, "lon": 108.4583},
    "TP.HCM": {"lat": 10.8231, "lon": 106.6297},
    "Bà Rịa - Vũng Tàu": {"lat": 10.3500, "lon": 107.0667},
    "Bình Dương": {"lat": 11.0333, "lon": 106.6667},
    "Đồng Nai": {"lat": 10.9500, "lon": 107.0833},
    "Tây Ninh": {"lat": 11.3167, "lon": 106.1333},
    "Cần Thơ": {"lat": 10.0452, "lon": 105.7469},
    "Long An": {"lat": 10.5333, "lon": 106.4167},
    "Tiền Giang": {"lat": 10.3667, "lon": 106.3667},
    "Bến Tre": {"lat": 10.2333, "lon": 106.3833},
    "Vĩnh Long": {"lat": 10.2500, "lon": 106.0000},
    "Đồng Tháp": {"lat": 10.4500, "lon": 105.6333},
    "An Giang": {"lat": 10.3833, "lon": 105.4167},
    "Kiên Giang": {"lat": 10.0167, "lon": 105.0833},
    "Sóc Trăng": {"lat": 9.6000, "lon": 105.9667},
    "Bạc Liêu": {"lat": 9.2833, "lon": 105.7167},
    "Cà Mau": {"lat": 9.1833, "lon": 105.1500},
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
# TABS (Không LSTM)
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Bảng điều khiển",
    "🗺️ Bản đồ rủi ro",
    "📢 Báo cáo cộng đồng",
    "⚠️ Cảnh báo dây chuyền"
])

# ---- TAB 1 ----
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

# ---- TAB 2 ----
with tab2:
    st.header("🗺️ Bản đồ rủi ro")
    map_data = pd.DataFrame({
        "lat": [21.0285, 16.0544, 10.8231, 16.4637, 14.3493],
        "lon": [105.8542, 108.2022, 106.6297, 107.5909, 108.0000],
        "city": ["Hà Nội", "Đà Nẵng", "TP.HCM", "Huế", "Kon Tum"],
        "risk": [3, 4, 2, 5, 4]
    })
    st.map(map_data, size="risk", zoom=6)
    st.dataframe(map_data, use_container_width=True)

# ---- TAB 3 ----
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

# ---- TAB 4 ----
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
    st.info("🟢 Các khu vực khác: An toàn.")