# Import standard libraries for time and system operations
import datetime
import requests
# Import Streamlit for web dashboard framework
import streamlit as st
# Import Pandas for data manipulation
import pandas as pd
# Import Plotly graph objects for interactive gauge and metric charts
import plotly.graph_objects as go
# Import Folium and Streamlit-Folium for interactive map drill-down
import folium
from streamlit_folium import st_folium

# Configure Streamlit page layout and theme
st.set_page_config(
    page_title="Global Weather Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# OpenWeatherMap API Base Endpoint
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
API_KEY = "6feba6004f3d3a67e731eb1ca2875515"

# Sample Country and City hierarchy dataset for drill-down navigation
COUNTRY_CITY_DATA = {
    "United Kingdom": {
        "London": {"lat": 51.5074, "lon": -0.1278},
        "Manchester": {"lat": 53.4808, "lon": -2.2426},
        "Edinburgh": {"lat": 55.9533, "lon": -3.1883},
        "Birmingham": {"lat": 52.4862, "lon": -1.8904}
    },
    "United States": {
        "New York": {"lat": 40.7128, "lon": -74.0060},
        "Los Angeles": {"lat": 34.0522, "lon": -118.2437},
        "Chicago": {"lat": 41.8781, "lon": -87.6298},
        "Miami": {"lat": 25.7617, "lon": -80.1918}
    },
    "United Arab Emirates": {
        "Abu Dhabi": {"lat": 24.4539, "lon": 54.3773},
        "Dubai": {"lat": 25.2048, "lon": 55.2708},
        "Sharjah": {"lat": 25.3463, "lon": 55.4209}
    },
    "Japan": {
        "Tokyo": {"lat": 35.6762, "lon": 139.6503},
        "Osaka": {"lat": 34.6937, "lon": 135.5023},
        "Kyoto": {"lat": 35.0116, "lon": 135.7681}
    },
    "France": {
        "Paris": {"lat": 48.8566, "lon": 2.3522},
        "Marseille": {"lat": 43.2965, "lon": 5.3698},
        "Lyon": {"lat": 45.7640, "lon": 4.8357}
    }
}


# Function to fetch weather by city string or latitude/longitude coordinates
def fetch_weather_data(query_type: str, query_val, units: str = "metric"):
    # Build query parameter dictionary dynamically based on query type
    if query_type == "city":
        params = {"q": query_val, "appid": API_KEY, "units": units}
    elif query_type == "coords":
        params = {"lat": query_val[0], "lon": query_val[1], "appid": API_KEY, "units": units}
    else:
        return None

    # Execute request wrapped in error handling
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError:
        if response.status_code == 404:
            st.error("Location not found. Please select or search another region.")
        elif response.status_code == 401:
            st.error("Invalid API key configured.")
        else:
            st.error(f"HTTP Error code: {response.status_code}")
    except requests.exceptions.RequestException as e:
        st.error(f"Network error encountered: {e}")
    return None


# Helper function to convert Unix timestamps to readable time string
def format_time(unix_ts, timezone_offset):
    # Adjust UTC timestamp with city local timezone offset
    local_time = datetime.datetime.utcfromtimestamp(unix_ts + timezone_offset)
    return local_time.strftime('%I:%M %p')


# Helper function to create interactive gauge chart for temperature
def create_temperature_gauge(temp, feels_like, temp_min, temp_max, unit_symbol):
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=temp,
        number={'suffix': f" {unit_symbol}"},
        delta={'reference': feels_like, 'relative': False, 'valueformat': '.1f'},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': "Temperature vs Feels Like", 'font': {'size': 16}},
        gauge={
            'axis': {'range': [temp_min - 10, temp_max + 10], 'tickwidth': 1},
            'bar': {'color': "#FF4B4B"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [temp_min - 10, temp_min], 'color': '#E0F7FA'},
                {'range': [temp_min, temp_max], 'color': '#FFF9C4'},
                {'range': [temp_max, temp_max + 10], 'color': '#FFCCBC'}
            ],
        }
    ))
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# Helper function to create interactive gauge chart for humidity and clouds
def create_metric_gauge(value, title, max_val=100, suffix="%"):
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=value,
        number={'suffix': suffix},
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title, 'font': {'size': 16}},
        gauge={
            'axis': {'range': [0, max_val]},
            'bar': {'color': "#0083B0"},
            'steps': [{'range': [0, max_val], 'color': '#E1F5FE'}]
        }
    ))
    fig.update_layout(height=200, margin=dict(l=20, r=20, t=40, b=20))
    return fig


# --- SIDEBAR: Navigation and Drill-down Options ---
st.sidebar.title("🧭 Drill-Down Navigation")
st.sidebar.markdown("Filter weather metrics by Country, City, map click, or search input.")

# Select unit measurement system
unit_system = st.sidebar.radio("Unit System:", ["Metric (°C, m/s)", "Imperial (°F, mph)"])
units_param = "metric" if "Metric" in unit_system else "imperial"
temp_unit = "°C" if units_param == "metric" else "°F"
speed_unit = "m/s" if units_param == "metric" else "mph"

# Navigation mode selector
nav_mode = st.sidebar.selectbox(
    "Drill-Down Method:",
    ["Hierarchy (Country -> City)", "Search City Name", "Interactive Map Click"]
)

# Initialize session variables for coordinate selection tracking
if "selected_lat" not in st.session_state:
    st.session_state["selected_lat"] = 51.5074
if "selected_lon" not in st.session_state:
    st.session_state["selected_lon"] = -0.1278
if "selected_city_name" not in st.session_state:
    st.session_state["selected_city_name"] = "London"

# Handle Hierarchy selection
if nav_mode == "Hierarchy (Country -> City)":
    selected_country = st.sidebar.selectbox("1. Select Country:", list(COUNTRY_CITY_DATA.keys()))
    cities_in_country = list(COUNTRY_CITY_DATA[selected_country].keys())
    selected_city = st.sidebar.selectbox("2. Select City / Area:", cities_in_country)
    
    # Update active target coordinate values
    city_coords = COUNTRY_CITY_DATA[selected_country][selected_city]
    st.session_state["selected_lat"] = city_coords["lat"]
    st.session_state["selected_lon"] = city_coords["lon"]
    st.session_state["selected_city_name"] = selected_city

# Handle Manual City Search input
elif nav_mode == "Search City Name":
    search_query = st.sidebar.text_input("Enter City / Area Name:", value="Tokyo")
    if st.sidebar.button("Search Area"):
        st.session_state["selected_city_name"] = search_query

# Mode info for Interactive Map Click
elif nav_mode == "Interactive Map Click":
    st.sidebar.info("👉 Click anywhere on the map in the main dashboard panel to fetch live weather data for that exact location!")


# --- FETCH WEATHER DATA ---
with st.spinner("Fetching live weather metrics..."):
    if nav_mode == "Search City Name":
        weather_data = fetch_weather_data("city", st.session_state["selected_city_name"], units=units_param)
    else:
        weather_data = fetch_weather_data("coords", (st.session_state["selected_lat"], st.session_state["selected_lon"]), units=units_param)


# --- MAIN DASHBOARD INTERFACE ---
st.title("🌍 Interactive Weather Analytics Dashboard")

if weather_data:
    # Extract response values
    city_name = weather_data.get("name", "Selected Location")
    country_code = weather_data.get("sys", {}).get("country", "")
    coord_lat = weather_data.get("coord", {}).get("lat", st.session_state["selected_lat"])
    coord_lon = weather_data.get("coord", {}).get("lon", st.session_state["selected_lon"])
    
    main_metrics = weather_data.get("main", {})
    wind_metrics = weather_data.get("wind", {})
    weather_desc = weather_data.get("weather", [{}])[0].get("description", "").title()
    weather_icon = weather_data.get("weather", [{}])[0].get("icon", "01d")
    clouds = weather_data.get("clouds", {}).get("all", 0)
    visibility_km = weather_data.get("visibility", 0) / 1000
    
    timezone_offset = weather_data.get("timezone", 0)
    sunrise_time = format_time(weather_data.get("sys", {}).get("sunrise", 0), timezone_offset)
    sunset_time = format_time(weather_data.get("sys", {}).get("sunset", 0), timezone_offset)

    # Top Location Banner
    banner_col1, banner_col2 = st.columns([3, 1])
    with banner_col1:
        st.header(f"📍 {city_name}, {country_code}")
        st.subheader(f"Condition: {weather_desc}")
    with banner_col2:
        icon_url = f"http://openweathermap.org/img/wn/{weather_icon}@2x.png"
        st.image(icon_url, width=100)

    st.markdown("---")

    # Row 1: Key Metric Cards
    m_col1, m_col2, m_col3, m_col4, m_col5 = st.columns(5)
    m_col1.metric("Temperature", f"{main_metrics.get('temp')}{temp_unit}", f"Feels {main_metrics.get('feels_like')}{temp_unit}")
    m_col2.metric("Min / Max Temp", f"{main_metrics.get('temp_min')}{temp_unit} / {main_metrics.get('temp_max')}{temp_unit}")
    m_col3.metric("Humidity", f"{main_metrics.get('humidity')}%")
    m_col4.metric("Wind Speed", f"{wind_metrics.get('speed')} {speed_unit}")
    m_col5.metric("Pressure", f"{main_metrics.get('pressure')} hPa")

    st.markdown("---")

    # Row 2: Drill-down Map & Primary Gauge Visualizations
    col_map, col_gauges = st.columns([2, 2])

    with col_map:
        st.markdown("### 🗺️ Interactive Map Drill-Down")
        st.write("Click anywhere on the map to query exact geographical weather metrics.")
        
        # Initialize Folium Map centered at selected coordinates
        m = folium.Map(location=[coord_lat, coord_lon], zoom_start=6, tiles="OpenStreetMap")
        folium.Marker(
            [coord_lat, coord_lon],
            popup=f"<b>{city_name}</b><br>Temp: {main_metrics.get('temp')}{temp_unit}",
            tooltip=city_name,
            icon=folium.Icon(color="red", icon="cloud")
        ).add_to(m)

        # Render Folium map in Streamlit and capture map click event
        map_data = st_folium(m, height=350, width=None)

        # Update coordinates when user clicks map in 'Interactive Map Click' mode
        if map_data and map_data.get("last_clicked"):
            clicked_lat = map_data["last_clicked"]["lat"]
            clicked_lon = map_data["last_clicked"]["lng"]
            if clicked_lat != st.session_state["selected_lat"] or clicked_lon != st.session_state["selected_lon"]:
                st.session_state["selected_lat"] = clicked_lat
                st.session_state["selected_lon"] = clicked_lon
                st.rerun()

    with col_gauges:
        st.markdown("### 📊 Live Analytics & Gauges")
        # Render temperature vs feels like gauge chart
        temp_fig = create_temperature_gauge(
            main_metrics.get('temp', 0),
            main_metrics.get('feels_like', 0),
            main_metrics.get('temp_min', 0),
            main_metrics.get('temp_max', 0),
            temp_unit
        )
        st.plotly_chart(temp_fig, use_container_width=True)

    # Row 3: Environmental Gauges & Astronomical Data
    st.markdown("---")
    st.markdown("### 🔍 Advanced Weather Metrics")

    detail_col1, detail_col2, detail_col3 = st.columns(3)

    with detail_col1:
        humidity_fig = create_metric_gauge(main_metrics.get('humidity', 0), "Relative Humidity")
        st.plotly_chart(humidity_fig, use_container_width=True)

    with detail_col2:
        cloud_fig = create_metric_gauge(clouds, "Cloud Coverage", suffix="%")
        st.plotly_chart(cloud_fig, use_container_width=True)

    with detail_col3:
        st.markdown("#### 🌅 Sun & Atmospheric Details")
        st.info(f"**Sunrise:** {sunrise_time}")
        st.info(f"**Sunset:** {sunset_time}")
        st.info(f"**Visibility:** {visibility_km:.1f} km")
        st.info(f"**Wind Direction:** {wind_metrics.get('deg', 0)}°")

else:
    st.warning("Unable to retrieve weather data for the selected location.")
