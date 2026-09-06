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
    """Lấy dữ liệu động đất thật từ USGS (khu vực Đông Nam Á)"""
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
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
                "time": datetime.fromtimestamp(props["time"] / 1000),
                "place": props.get("place", "Unknown"),
                "mag": props.get("mag", 0),
                "depth": round(geom["coordinates"][2], 1),
                "lat": geom["coordinates"][1],
                "lon": geom["coordinates"][0],
                "tsunami": "Có" if props.get("tsunami", 0) == 1 else "Không"
            })
        df = pd.DataFrame(events)
        if not df.empty:
            df = df.sort_values("time", ascending=False)
        return df
    except Exception as e:
        st.error(f"Lỗi khi lấy dữ liệu: {e}")
        return pd.DataFrame()

# ===============================
# HÀM LẤY THỜI TIẾT 7 NGÀY
# ===============================
@st.cache_data(ttl=600)
def fetch_weather_forecast(lat, lon, days=7):
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
            "date": pd.to_datetime(daily.get("time", [])),
            "temp_max": daily.get("temperature_2m_max", []),
            "temp_min": daily.get("temperature_2m_min", []),
            "precipitation": daily.get("precipitation_sum", []),
            "wind_max": daily.get("wind_speed_10m_max", [])
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
# TAB 1
# ===============================
with tab1:
    st.header("📋 Động đất thực tế gần đây (Đông Nam Á)")
    
    with st.spinner("📡 Đang tải dữ liệu từ USGS..."):
        df = fetch_real_earthquakes(days=days, min_magnitude=min_mag)
    
    if df.empty:
        st.warning("Không có dữ liệu động đất thật.")
    else:
        st.dataframe(df[["time", "place", "mag", "depth", "tsunami"]], use_container_width=True)
        col1, col2, col3 = st.columns(3)
        col1.metric("Tổng số trận", len(df))
        col2.metric("Độ lớn TB", f"{df['mag'].mean():.1f}")
        col3.metric("Lớn nhất", f"{df['mag'].max():.1f}")

# ===============================
# TAB 2
# ===============================
with tab2:
    st.header("🗺️ Bản đồ động đất")
    if not df.empty:
        fig = px.scatter_mapbox(
            df,
            lat="lat",
            lon="lon",
            hover_name="place",
            hover_data={"mag": True, "depth": True},
            color="mag",
            size="mag",
            color_continuous_scale="Viridis",
            mapbox_style="open-street-map",
            zoom=2,
            title="Vị trí các trận động đất"
        )
        fig.update_layout(margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Không có dữ liệu để hiển thị bản đồ.")

# ===============================
# TAB 3
# ===============================
with tab3:
    st.header(f"📈 Dự báo thời tiết 7 ngày tại {region}")
    with st.spinner("Đang tải..."):
        weather_df = fetch_weather_forecast(coords["lat"], coords["lon"], days=7)
    if weather_df.empty:
        st.warning("Không lấy được dữ liệu thời tiết.")
    else:
        fig_temp = go.Figure()
        fig_temp.add_trace(go.Scatter(
            x=weather_df["date"],
            y=weather_df["temp_max"],
            mode="lines+markers",
            name="Max",
            line=dict(color="red")
        ))
        fig_temp.add_trace(go.Scatter(
            x=weather_df["date"],
            y=weather_df["temp_min"],
            mode="lines+markers",
            name="Min",
            line=dict(color="blue")
        ))
        fig_temp.update_layout(title="Nhiệt độ dự báo", xaxis_title="Ngày", yaxis_title="°C")
        st.plotly_chart(fig_temp, use_container_width=True)

        fig_rain = px.bar(weather_df, x="date", y="precipitation", title="Lượng mưa dự báo")
        st.plotly_chart(fig_rain, use_container_width=True)

# ===============================
# TAB 4
# ===============================
with tab4:
    st.header("📢 Báo cáo cộng đồng")
    with st.form("report_form"):
        report_type = st.selectbox("Loại báo cáo", ["An toàn", "Nguy hiểm", "Hiện tượng lạ", "Thiệt hại"])
        location = st.text_input("📍 Vị trí")
        description = st.text_area("📝 Mô tả")
        submitted = st.form_submit_button("Gửi báo cáo")
        if submitted and location and description:
            st.success("✅ Cảm ơn bạn!")
            st.balloons()