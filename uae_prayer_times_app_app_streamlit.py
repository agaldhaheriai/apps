# Import core Streamlit UI library
import streamlit as st

# Import standard library for date and time calculations
import datetime

# Import requests for making HTTP calls to the AWQAF API
import requests

# Set page configuration for web browser tab title and icon
st.set_page_config(
    page_title="UAE Prayer Times - AWQAF",
    page_icon="🕌",
    layout="wide"
)

# API endpoint configuration
API_ENDPOINT = "https://api.gsb.government.ae/gateway/retrievePrayerTimeDetails_AWQAF/1.0"
GSB_SUBSCRIPTION_KEY = "YOUR_GSB_SUBSCRIPTION_KEY"

# Supported UAE Cities dictionary
UAE_CITIES = {
    "1": "Abu Dhabi",
    "2": "Dubai",
    "3": "Sharjah",
    "4": "Ajman",
    "5": "Umm Al Quwain",
    "6": "Ras Al Khaimah",
    "7": "Fujairah",
    "8": "Al Ain",
    "9": "Madinat Zayed (Dhafra)",
}

# Helper function to fetch prayer timings from AWQAF
def fetch_prayer_times(city_id: str, date_str: str):
    headers = {
        "Content-Type": "application/json",
        "Ocp-Apim-Subscription-Key": GSB_SUBSCRIPTION_KEY,
    }
    payload = {"cityId": city_id, "date": date_str}
    
    try:
        response = requests.post(API_ENDPOINT, headers=headers, json=payload, timeout=5)
        if response.status_code == 200:
            return response.json().get("prayerTimes", {})
    except Exception:
        pass
    return None

# App Title and Description Header
st.title("🕌 UAE Official Prayer Times")
st.caption("Powered by AWQAF (General Authority of Islamic Affairs & Endowments) API Gateway")

# Sidebar settings block
st.sidebar.header("⚙️ Configuration")

# Date Picker component
selected_date = st.sidebar.date_input("Select Date", datetime.date.today())
date_str = selected_date.strftime("%Y-%m-%d")

# View Mode selection
view_mode = st.sidebar.radio("View Mode", ["Single City", "All Cities Dashboard"])

# UI View Logic: Single City Mode
if view_mode == "Single City":
    selected_city_name = st.selectbox("Select Emirates / City", list(UAE_CITIES.values()))
    city_id = [k for k, v in UAE_CITIES.items() if v == selected_city_name][0]
    
    st.subheader(f"Prayer Times for {selected_city_name} on {date_str}")
    
    with st.spinner("Fetching prayer times..."):
        timings = fetch_prayer_times(city_id, date_str)
        
    if timings:
        cols = st.columns(6)
        prayers = [
            ("Fajr", timings.get("Fajr", "N/A"), "🌅"),
            ("Sunrise", timings.get("Sunrise", "N/A"), "☀️"),
            ("Dhuhr", timings.get("Dhuhr", "N/A"), "🌤️"),
            ("Asr", timings.get("Asr", "N/A"), "🌤️"),
            ("Maghrib", timings.get("Maghrib", "N/A"), "🌆"),
            ("Isha", timings.get("Isha", "N/A"), "🌙")
        ]
        
        for col, (name, time_val, icon) in zip(cols, prayers):
            with col:
                st.metric(label=f"{icon} {name}", value=time_val)
    else:
        st.warning("⚠️ Could not fetch real-time data from AWQAF Gateway. Please check your API Subscription Key.")
        st.info("Displaying static example layout:")
        cols = st.columns(6)
        cols[0].metric("🌅 Fajr", "05:12 AM")
        cols[1].metric("☀️ Sunrise", "06:30 AM")
        cols[2].metric("🌤️ Dhuhr", "12:25 PM")
        cols[3].metric("🌤️ Asr", "03:45 PM")
        cols[4].metric("🌆 Maghrib", "06:15 PM")
        cols[5].metric("🌙 Isha", "07:45 PM")

# UI View Logic: All Cities Dashboard Mode
else:
    st.subheader(f"Prayer Times Across All Emirates ({date_str})")
    
    table_data = []
    with st.spinner("Fetching data for all cities..."):
        for c_id, c_name in UAE_CITIES.items():
            t = fetch_prayer_times(c_id, date_str)
            if t:
                table_data.append({
                    "Emirate / City": c_name,
                    "Fajr": t.get("Fajr", "N/A"),
                    "Sunrise": t.get("Sunrise", "N/A"),
                    "Dhuhr": t.get("Dhuhr", "N/A"),
                    "Asr": t.get("Asr", "N/A"),
                    "Maghrib": t.get("Maghrib", "N/A"),
                    "Isha": t.get("Isha", "N/A"),
                })
            else:
                table_data.append({
                    "Emirate / City": c_name,
                    "Fajr": "N/A", "Sunrise": "N/A", "Dhuhr": "N/A",
                    "Asr": "N/A", "Maghrib": "N/A", "Isha": "N/A"
                })
                
    st.dataframe(table_data, use_container_width=True)
