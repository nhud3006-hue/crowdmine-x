import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="CrowdMine-X", page_icon="🌍", layout="wide")

# ===============================
# TIÊU ĐỀ
# ===============================
st.title("🌍 CrowdMine-X")
st.subheader("Hệ thống Cảnh báo Thiên tai Dây chuyền với AI và Cộng đồng")

# ===============================
# HÀM LẤY DỮ LIỆU ĐỘNG ĐẤT THẬT
# ===============================
@st.cache_data(ttl=600)
def fetch_real_earthquakes(days=7, min_magnitude=4.0):
    """Lấy dữ liệu động đất thật từ USGS (toàn cầu, lọc khu vực Đông Nam Á)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Khu vực Đông Nam Á (mở rộng hơn)
    params = {
        "format": "geojson",
        "starttime": start_date.strftime("%Y-%m-%d"),
        "endtime": end_date.strftime("%Y-%m-%d"),
        "minmagnitude": min_magnitude,
        "minlatitude": -10.0,
        "maxlatitude": 30.0,
        "minlongitude": 90.0,
        "maxlongitude": 150.0,
        "orderby": "time"
    }
    
    try:
        response = requests.get(
            "https://earthquake.usgs.gov/fdsnws/event/1/query",
            params=params,
            timeout=15
        )
        data = response.json()
        events = []
        for feature in data.get("features", []):
            props = feature["properties"]
            geom = feature["geometry"]
            events.append({
                "Thời gian": datetime.fromtimestamp(props["time"] / 1000).strftime("%Y-%m-%d %H:%M"),
                "Vị trí": props.get("place", "Unknown"),
                "Độ lớn": props.get("mag", 0),
                "Độ sâu (km)": round(geom["coordinates"][2], 1),
                "Vĩ độ": geom["coordinates"][1],
                "Kinh độ": geom["coordinates"][0],
                "Tsunami": "Có" if props.get("tsunami", 0) == 1 else "Không"
            })
        return pd.DataFrame(events)
    except:
        return pd.DataFrame()

# ===============================
# HÀM LẤY THỜI TIẾT 7 NGÀY
# ===============================
@st.cache_data(ttl=600)
def fetch_weather_forecast(lat, lon, days=7):
    """Lấy dữ liệu dự báo thời tiết 7 ngày từ Open-Meteo"""
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "Asia/Ho_Chi_Minh",
        "forecast_days": days
    }
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        daily = data.get("daily", {})
        df = pd.DataFrame({
            "Ngày": pd.to_datetime(daily.get("time", [])),
            "Nhiệt độ max (°C)": daily.get("temperature_2m_max", []),
            "Nhiệt độ min (°C)": daily.get("temperature_2m_min", []),
            "Lượng mưa (mm)": daily.get("precipitation_sum", []),
            "Gió max (km/h)": daily.get("wind_speed_10m_max", [])
        })
        return df
    except:
        return pd.DataFrame()

# ===============================
# SIDEBAR
# ===============================
CITY_COORDS = {
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022},
    "TP.HCM": {"lat": 10.8231, "lon": 106.6297},
    "Huế": {"lat": 16.4637, "lon": 107.5909},
    "Kon Tum": {"lat": 14.3493, "lon": 108.0000},
    "Đà Lạt": {"lat": 11.9404, "lon": 108.4583},
}

with st.sidebar:
    st.header("📍 Khu vực")
    region = st.selectbox("Chọn thành phố", list(CITY_COORDS.keys()))
    days = st.slider("📅 Số ngày lấy động đất", 1, 30, 7)
    min_mag = st.slider("📊 Độ lớn tối thiểu", 2.0, 6.0, 4.0, 0.5)
    st.caption(f"🔄 Cập nhật: {datetime.now().strftime('%H:%M %d/%m/%Y')}")

coords = CITY_COORDS.get(region)

# ===============================
# TABS
# ===============================
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Bảng điều khiển",
    "🗺️ Bản đồ động đất",
    "📈 Dự báo thời tiết 7 ngày",
    "📢 Báo cáo cộng đồng"
])

# ===============================
# TAB 1: BẢNG ĐIỀU KHIỂN
# ===============================
with tab1:
    st.header("📋 Động đất thực tế gần đây (Đông Nam Á)")
    
    with st.spinner("📡 Đang tải dữ liệu từ USGS..."):
        df = fetch_real_earthquakes(days=days, min_magnitude=min_mag)
    
    if df.empty:
        st.warning("⚠️ Không có dữ liệu động đất thật trong khoảng thời gian này.")
        st.info("💡 Thử giảm 'Độ lớn tối thiểu' hoặc tăng số ngày.")
    else:
        # Bảng dữ liệu
        st.dataframe(df, use_container_width=True)
        
        # Thống kê
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Tổng số trận", len(df))
        with col2:
            st.metric("Độ lớn TB", f"{df['Độ lớn'].mean():.1f}")
        with col3:
            st.metric("Lớn nhất", f"{df['Độ lớn'].max():.1f}")
        
        # Biểu đồ phân bố độ lớn
        st.subheader("📊 Phân bố độ lớn")
        fig = px.histogram(df, x="Độ lớn", nbins=10, title="Biểu đồ tần suất động đất theo độ lớn")
        st.plotly_chart(fig, use_container_width=True)

# ===============================
# TAB 2: BẢN ĐỒ ĐỘNG ĐẤT
# ===============================
with tab2:
    st.header("🗺️ Bản đồ động đất thế giới (gần đây)")
    
    if not df.empty:
        fig = px.scatter_mapbox(
            df,
            lat="Vĩ độ",
            lon="Kinh độ",
            hover_name="Vị trí",
            hover_data={"Độ lớn": True, "Độ sâu (km)": True},
            color="Độ lớn",
            size="Độ lớn",
            color_continuous_scale="Viridis",
            mapbox_style="open-street-map",
            zoom=2,
            title="Các trận động đất trong khu vực Đông Nam Á"
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có dữ liệu để hiển thị bản đồ.")

# ===============================
# TAB 3: DỰ BÁO THỜI TIẾT 7 NGÀY
# ===============================
with tab3:
    st.header(f"📈 Dự báo thời tiết 7 ngày tại {region}")
    
    with st.spinner("Đang tải dữ liệu thời tiết..."):
        weather_df = fetch_weather_forecast(coords["lat"], coords["lon"], days=7)
    
    if weather_df.empty:
        st.warning("Không thể lấy dữ liệu thời tiết.")
    else:
        # Biểu đồ nhiệt độ
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=weather_df["Ngày"],
            y=weather_df["Nhiệt độ max (°C)"],
            mode="lines+markers",
            name="Max",
            line=dict(color="red")
        ))
        fig_temp.add_trace(go.Scatter(
            x=weather_df["Ngày"],
            y=weather_df["Nhiệt độ min (°C)"],
            mode="lines+markers",
            name="Min",
            line=dict(color="blue")
        ))
        fig_temp.update_layout(title="Nhiệt độ dự báo", xaxis_title="Ngày", yaxis_title="°C")
        st.plotly_chart(fig_temp, use_container_width=True)
        
        # Biểu đồ mưa
        fig_rain = px.bar(weather_df, x="Ngày", y="Lượng mưa (mm)", title="Lượng mưa dự báo")
        st.plotly_chart(fig_rain, use_container_width=True)
        
        # Bảng dữ liệu
        st.dataframe(weather_df, use_container_width=True)

# ===============================
# TAB 4: BÁO CÁO CỘNG ĐỒNG
# ===============================
with tab4:
    st.header("📢 Báo cáo cộng đồng")
    with st.form("report_form"):
        report_type = st.selectbox("Loại báo cáo", ["An toàn", "Nguy hiểm", "Hiện tượng lạ", "Thiệt hại"])
        location = st.text_input("📍 Vị trí")
        description = st.text_area("📝 Mô tả")
        submitted = st.form_submit_button("Gửi báo cáo")
        if submitted and location and description:
            st.success("✅ Cảm ơn bạn! Báo cáo đã được gửi.")
            st.balloons()