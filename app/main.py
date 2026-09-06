import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import random
import os

# ===============================
# CẤU HÌNH PAGE
# ===============================
st.set_page_config(page_title="CrowdMine-X Pro", page_icon="🌍", layout="wide")

# Khởi tạo theme (mặc định light)
if "theme" not in st.session_state:
    st.session_state.theme = "light"

# Hàm toggle theme
def toggle_theme():
    st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"

# ===============================
# CSS TUỲ CHỈNH (Dark/Light)
# ===============================
def apply_css(theme):
    if theme == "dark":
        st.markdown("""
        <style>
            .stApp {
                background-color: #1a1a2e;
                color: #e0e0e0;
            }
            .sidebar .sidebar-content {
                background-color: #16213e;
            }
            .stMetric {
                background-color: #0f3460;
                padding: 10px;
                border-radius: 10px;
                color: white;
            }
            h1, h2, h3, h4, h5, h6 {
                color: #e0e0e0;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
            .stApp {
                background-color: #f5f7fa;
                color: #1a1a2e;
            }
            .sidebar .sidebar-content {
                background-color: #ffffff;
            }
            .stMetric {
                background-color: #e8f0fe;
                padding: 10px;
                border-radius: 10px;
                color: #1a1a2e;
            }
        </style>
        """, unsafe_allow_html=True)

apply_css(st.session_state.theme)

# ===============================
# CLASS LẤY DỮ LIỆU
# ===============================
class WeatherFetcher:
    def __init__(self):
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def get_current_weather(self, lat, lon):
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
            "timezone": "Asia/Ho_Chi_Minh",
            "forecast_days": 1
        }
        try:
            r = requests.get(self.base_url, params=params, timeout=10)
            data = r.json()
            current = data.get("current_weather", {})
            hourly = data.get("hourly", {})
            now = datetime.now().hour
            idx = min(now, len(hourly.get("temperature_2m", [])) - 1) if hourly else 0
            temp = hourly["temperature_2m"][idx] if "temperature_2m" in hourly else current.get("temperature")
            hum = hourly["relative_humidity_2m"][idx] if "relative_humidity_2m" in hourly else None
            rain = hourly["precipitation"][idx] if "precipitation" in hourly else 0
            wind = hourly["wind_speed_10m"][idx] if "wind_speed_10m" in hourly else current.get("windspeed")
            return {
                "temperature": temp,
                "precipitation": rain,
                "humidity": hum,
                "wind_speed": wind,
                "time": current.get("time", datetime.now().strftime("%Y-%m-%d %H:%M"))
            }
        except:
            return None

class USGSFetcher:
    def __init__(self):
        self.base_url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
    
    def fetch_earthquakes(self, days=7, min_mag=3.0):
        end = datetime.now()
        start = end - timedelta(days=days)
        params = {
            "format": "geojson",
            "starttime": start.strftime("%Y-%m-%d"),
            "endtime": end.strftime("%Y-%m-%d"),
            "minmagnitude": min_mag,
            "minlatitude": 8.0, "maxlatitude": 24.0,
            "minlongitude": 102.0, "maxlongitude": 110.0,
            "orderby": "time"
        }
        try:
            r = requests.get(self.base_url, params=params, timeout=10)
            data = r.json()
            events = []
            for f in data.get("features", []):
                props = f["properties"]
                geom = f["geometry"]
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

class EONETFetcher:
    def __init__(self):
        self.base_url = "https://eonet.gsfc.nasa.gov/api/v3/events"
    
    def fetch_events(self, limit=10):
        params = {"status": "open", "limit": limit}
        try:
            r = requests.get(self.base_url, params=params, timeout=10)
            data = r.json()
            events = []
            for ev in data.get("events", []):
                categories = ev.get("categories", [])
                cat = categories[0].get("title", "Unknown") if categories else "Unknown"
                geom = ev.get("geometry", [{}])[0]
                coords = geom.get("coordinates", [])
                date_str = geom.get("date", "")
                events.append({
                    "title": ev.get("title", "No title"),
                    "category": cat,
                    "status": ev.get("status", "unknown"),
                    "latitude": coords[1] if len(coords) > 1 else None,
                    "longitude": coords[0] if len(coords) > 0 else None,
                    "date": datetime.fromisoformat(date_str.replace("Z", "+00:00")) if date_str else None
                })
            return pd.DataFrame(events)
        except:
            return pd.DataFrame()

def get_mock_earthquakes():
    now = datetime.now()
    data = []
    places = ["Kon Tum", "Điện Biên", "Lào Cai", "Quảng Nam", "Nghệ An", "Thanh Hóa"]
    for i in range(5):
        data.append({
            "time": now - timedelta(hours=i*6),
            "place": f"Cách {random.choice(places)} {random.randint(10,50)} km",
            "magnitude": round(random.uniform(3.0, 5.5), 1),
            "depth_km": round(random.uniform(5, 30), 1),
            "latitude": 14 + random.uniform(-3, 5),
            "longitude": 108 + random.uniform(-3, 3)
        })
    return pd.DataFrame(data)

# ===============================
# TỌA ĐỘ TỈNH THÀNH
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
st.title("🌍 CrowdMine-X Pro")
st.subheader("Hệ thống Cảnh báo Thiên tai Dây chuyền Thông minh")

# ---- SIDEBAR ----
with st.sidebar:
    st.header("📍 Khu vực")
    region = st.selectbox("Chọn tỉnh/thành phố", list(CITY_COORDS.keys()))
    days = st.slider("📅 Số ngày lấy dữ liệu động đất", 1, 30, 7)
    min_mag = st.slider("📊 Độ lớn tối thiểu", 2.0, 6.0, 3.0, 0.5)
    
    st.divider()
    st.button("🌗 Chuyển chế độ sáng/tối", on_click=toggle_theme)
    st.caption(f"🔄 Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

coords = CITY_COORDS.get(region, {"lat": 21.0285, "lon": 105.8542})

# ---- THỜI TIẾT ----
weather_fetcher = WeatherFetcher()
weather = weather_fetcher.get_current_weather(coords["lat"], coords["lon"])
if weather:
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("🌡️ Nhiệt độ", f"{weather['temperature']}°C")
    c2.metric("💧 Độ ẩm", f"{weather['humidity']}%" if weather['humidity'] else "N/A")
    c3.metric("🌧️ Lượng mưa", f"{weather['precipitation']} mm")
    c4.metric("💨 Gió", f"{weather['wind_speed']} km/h" if weather['wind_speed'] else "N/A")
else:
    st.warning("⚠️ Không thể lấy dữ liệu thời tiết.")

# ---- TABS ----
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
        df_eq = fetcher.fetch_earthquakes(days=days, min_magnitude=min_mag)
    if df_eq.empty:
        st.info("ℹ️ Không có dữ liệu thật. Hiển thị dữ liệu mô phỏng.")
        df_eq = get_mock_earthquakes()
    st.dataframe(df_eq[["time", "place", "magnitude", "depth_km"]], use_container_width=True)
    col1, col2, col3 = st.columns(3)
    col1.metric("📌 Số trận", len(df_eq))
    col2.metric("📊 Độ lớn TB", f"{df_eq['magnitude'].mean():.1f}")
    col3.metric("🔝 Mạnh nhất", f"{df_eq['magnitude'].max():.1f}")
    st.bar_chart(df_eq["magnitude"])
    
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
    # Lấy dữ liệu động đất để vẽ map
    if df_eq is not None and not df_eq.empty:
        map_df = df_eq[["latitude", "longitude", "magnitude"]].copy()
        map_df.rename(columns={"magnitude": "size"}, inplace=True)
        # Thêm báo cáo cộng đồng nếu có
        try:
            reports = pd.read_csv("reports.csv")
            if not reports.empty and "latitude" in reports.columns and "longitude" in reports.columns:
                reports_map = reports.dropna(subset=["latitude", "longitude"])
                if not reports_map.empty:
                    reports_map["size"] = 10  # kích thước cố định cho báo cáo
                    map_df = pd.concat([map_df, reports_map[["latitude", "longitude", "size"]]], ignore_index=True)
        except:
            pass
        st.map(map_df, size="size", zoom=6)
    else:
        st.info("Không có dữ liệu động đất để hiển thị bản đồ.")
    
    st.divider()
    st.subheader("📋 Danh sách điểm rủi ro")
    try:
        reports = pd.read_csv("reports.csv")
        st.dataframe(reports[["time", "type", "location", "description"]].tail(10), use_container_width=True)
    except:
        st.info("Chưa có báo cáo nào từ cộng đồng.")

# ---- TAB 3 ----
with tab3:
    st.header("📢 Gửi báo cáo cộng đồng")
    with st.form("report_form"):
        report_type = st.selectbox("Loại báo cáo", ["An toàn", "Nguy hiểm", "Hiện tượng lạ", "Thiệt hại"])
        location = st.text_input("📍 Vị trí (tỉnh/thành phố)")
        description = st.text_area("📝 Mô tả chi tiết")
        lat = st.number_input("🧭 Vĩ độ (nếu biết)", value=0.0, format="%.4f")
        lon = st.number_input("🧭 Kinh độ (nếu biết)", value=0.0, format="%.4f")
        submitted = st.form_submit_button("📤 Gửi báo cáo")
        if submitted and location and description:
            new_report = {
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "type": report_type,
                "location": location,
                "description": description,
                "latitude": lat if lat != 0.0 else None,
                "longitude": lon if lon != 0.0 else None
            }
            try:
                df_reports = pd.read_csv("reports.csv")
                df_reports = pd.concat([df_reports, pd.DataFrame([new_report])], ignore_index=True)
            except:
                df_reports = pd.DataFrame([new_report])
            df_reports.to_csv("reports.csv", index=False)
            st.success("✅ Cảm ơn bạn đã gửi báo cáo!")
            st.balloons()
    
    st.divider()
    st.subheader("📋 Các báo cáo gần đây")
    try:
        df_reports = pd.read_csv("reports.csv")
        st.dataframe(df_reports.tail(10), use_container_width=True)
    except:
        st.info("Chưa có báo cáo nào. Hãy gửi báo cáo đầu tiên!")

# ---- TAB 4 ----
with tab4:
    st.header("⚠️ Phân tích rủi ro dây chuyền")
    if weather:
        rain = weather.get("precipitation", 0)
        wind = weather.get("wind_speed", 0)
        if rain > 50 or wind > 50:
            st.error("""
            🔴 **Cảnh báo Đỏ: Nguy cơ cao**
            - Mưa lớn / gió mạnh có thể gây lũ lụt, sạt lở.
            - **Tác động dây chuyền:** Lũ quét, sạt lở đất, vỡ đê.
            - **Khuyến nghị:** Sơ tán ngay các vùng trũng thấp!
            """)
        elif rain > 20 or wind > 30:
            st.warning("""
            🟡 **Cảnh báo Vàng: Nguy cơ trung bình**
            - Thời tiết xấu, có thể gây ngập cục bộ.
            - Theo dõi sát các bản tin thời tiết.
            """)
        else:
            st.info("🟢 **An toàn:** Không có nguy cơ đặc biệt.")
        
        if not df_eq.empty:
            latest = df_eq.iloc[0]
            if latest["magnitude"] > 5.0:
                st.warning(f"⚠️ Động đất {latest['magnitude']} tại {latest['place']} - Có thể gây dư chấn.")
            else:
                st.success(f"✅ Động đất nhẹ ({latest['magnitude']}) tại {latest['place']} - An toàn.")
    else:
        st.info("Không có dữ liệu thời tiết để phân tích.")