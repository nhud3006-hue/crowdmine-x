import streamlit as st
import pandas as pd

# Cấu hình trang
st.set_page_config(
    page_title="CrowdMine-X",
    page_icon="🌍",
    layout="wide"
)

# Tiêu đề
st.title("🌍 CrowdMine-X")
st.subheader("Hệ thống Cảnh báo Thiên tai Dây chuyền với AI và Cộng đồng")

# Sidebar
st.sidebar.header("📍 Chọn khu vực")
region = st.sidebar.selectbox(
    "Tỉnh/Thành phố",
    ["Hà Nội", "Đà Nẵng", "TP.HCM", "Huế", "Kon Tum"]
)

# Hiển thị khu vực được chọn
st.write(f"📍 Bạn đang xem thông tin tại: **{region}**")

# Các tab chức năng
tab1, tab2, tab3 = st.tabs(["📊 Bảng điều khiển", "🗺️ Bản đồ rủi ro", "📢 Báo cáo cộng đồng"])

with tab1:
    st.header("Tổng quan rủi ro hôm nay")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🌋 Động đất", "2", "▲ 1")
    with col2:
        st.metric("🌀 Bão", "0", "➡️ Bình thường")
    with col3:
        st.metric("🌊 Lũ lụt", "1", "▲ 25%")
    with col4:
        st.metric("🔥 Cháy rừng", "0", "➡️ Bình thường")
    
    st.success("✅ Hệ thống đang hoạt động. Dữ liệu sẽ được cập nhật từ USGS và NASA.")

with tab2:
    st.header("🗺️ Bản đồ rủi ro tại Việt Nam")
    map_data = pd.DataFrame({
        "lat": [21.0285, 16.0544, 10.8231, 16.4637, 14.3493],
        "lon": [105.8542, 108.2022, 106.6297, 107.5909, 108.0000],
        "city": ["Hà Nội", "Đà Nẵng", "TP.HCM", "Huế", "Kon Tum"],
        "risk": [3, 4, 2, 5, 4]
    })
    st.map(map_data, size="risk", zoom=6)

with tab3:
    st.header("📢 Báo cáo từ cộng đồng")
    with st.form("report_form"):
        st.subheader("Gửi báo cáo tình hình")
        report_type = st.selectbox(
            "Loại báo cáo",
            ["An toàn", "Nguy hiểm", "Hiện tượng lạ"]
        )
        location = st.text_input("Vị trí cụ thể")
        description = st.text_area("Mô tả chi tiết")
        submitted = st.form_submit_button("Gửi báo cáo")
        
        if submitted:
            st.success("✅ Cảm ơn bạn! Báo cáo đã được gửi đến hệ thống AI để xác thực.")