# Import streamlit module for creating web user interface
import streamlit as st
# Import requests module for handling HTTP API requests
import requests

# Configure Streamlit browser page title, icon, and layout
st.set_page_config(page_title="Weather Forecast App", page_icon="🌤️", layout="centered")

# Set static base URL endpoint for OpenWeatherMap API
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
# Set API key credential string
API_KEY = "6feba6004f3d3a67e731eb1ca2875515"


# Define function to query weather data from OpenWeatherMap API
def get_weather(city: str, units: str = "metric"):
    # Define query parameters dictionary for API call
    params = {
        "q": city,            # Target city name parameter
        "appid": API_KEY,      # API key authorization parameter
        "units": units        # Units parameter ('metric' or 'imperial')
    }
    # Execute network call inside try block for error safety
    try:
        # Send HTTP GET request with 10 second timeout limit
        response = requests.get(BASE_URL, params=params, timeout=10)
        # Check HTTP status code and raise exception if non-200
        response.raise_for_status()
        # Parse JSON response body to dictionary and return
        return response.json()
    # Handle HTTP error status codes gracefully
    except requests.exceptions.HTTPError:
        # Check for 404 city not found status code
        if response.status_code == 404:
            # Display Streamlit error alert for city not found
            st.error(f"City '{city}' not found. Please check spelling.")
        # Check for 401 unauthorized status code
        elif response.status_code == 401:
            # Display Streamlit error alert for invalid key
            st.error("Invalid API Key provided.")
        # Handle all other non-200 HTTP codes
        else:
            # Display general HTTP error message code
            st.error(f"HTTP Error: {response.status_code}")
    # Handle network failure exceptions
    except requests.exceptions.RequestException as e:
        # Display Streamlit error alert for network failure
        st.error(f"Network error: {e}")
    # Return None if request failed
    return None


# Render web application main page header title
st.title("🌤️ Weather Forecast App")
# Render descriptive subheader text on webpage
st.write("Get real-time weather information for any city worldwide using OpenWeatherMap API.")

# Create two-column layout for input fields
col1, col2 = st.columns([3, 1])

# Assign text input field to first column
with col1:
    # Render text box for entering city name
    city_input = st.text_input("Enter City Name:", placeholder="e.g., London, Tokyo, New York")

# Assign select box field to second column
with col2:
    # Render dropdown box for selecting temperature unit system
    unit_system = st.selectbox("Units:", options=["Metric (°C)", "Imperial (°F)"])

# Determine internal units parameter string based on selection
units_param = "metric" if "Metric" in unit_system else "imperial"
# Determine temperature unit label symbol string
temp_unit = "°C" if units_param == "metric" else "°F"
# Determine wind speed unit label symbol string
speed_unit = "m/s" if units_param == "metric" else "mph"

# Render action button and check if clicked
if st.button("Get Weather", type="primary"):
    # Check if user submitted empty input string
    if not city_input.strip():
        # Render warning alert message for empty input
        st.warning("Please enter a city name.")
    # Proceed if valid text string was entered
    else:
        # Display loading spinner during API network call execution
        with st.spinner("Fetching weather data..."):
            # Call function to fetch weather data dictionary
            data = get_weather(city_input.strip(), units=units_param)
            # Check if API returned valid data payload
            if data:
                # Extract city name from JSON payload
                city_name = data.get("name")
                # Extract country code from nested 'sys' payload
                country = data.get("sys", {}).get("country")
                # Extract condition text description and apply title case
                desc = data.get("weather", [{}])[0].get("description", "").title()
                # Extract main temperature metrics dictionary
                main = data.get("main", {})
                # Extract wind speed metrics dictionary
                wind = data.get("wind", {})

                # Display success message header banner
                st.success(f"Weather for {city_name}, {country}")
                # Display general weather condition subheader text
                st.subheader(f"Condition: {desc}")

                # Create three-column container layout for primary metrics
                m1, m2, m3 = st.columns(3)
                # Render current temperature and feels-like metric widget
                m1.metric("Temperature", f"{main.get('temp')}{temp_unit}", f"Feels like: {main.get('feels_like')}{temp_unit}")
                # Render min and max temperature range metric widget
                m2.metric("Min / Max Temp", f"{main.get('temp_min')}{temp_unit} / {main.get('temp_max')}{temp_unit}")
                # Render relative humidity percentage metric widget
                m3.metric("Humidity", f"{main.get('humidity')}%")

                # Create two-column container layout for secondary metrics
                m4, m5 = st.columns(2)
                # Render atmospheric pressure metric widget
                m4.metric("Pressure", f"{main.get('pressure')} hPa")
                # Render wind speed metric widget
                m5.metric("Wind Speed", f"{wind.get('speed')} {speed_unit}")
