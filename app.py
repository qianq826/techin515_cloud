import streamlit as st
import requests
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import pytz
from PIL import Image


# Setting up UI elements
def setup_ui():
    st.set_page_config(page_title='Circadian Weather App Dashboard', layout='wide', initial_sidebar_state='expanded')
    st.markdown("""
        <style>
        .stApp {
            background-image: url(https://wallpaperaccess.com/full/6418406.jpg);
            background-attachment: fixed;
            background-size: cover;
        }
        </style>
        """, unsafe_allow_html=True)
    logo = Image.open("img/icon.png")
    st.sidebar.image(logo.resize((60, 70)))

setup_ui()

# Function to geocode location using Nominatim API
def geocode_location(location):
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': location, 'format': 'json'}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None

# Function to fetch weather from weather.gov
def fetch_weather(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        forecast_url = data['properties']['forecast']
        forecast_response = requests.get(forecast_url)
        forecast_response.raise_for_status()
        forecast_data = forecast_response.json()
        return forecast_data['properties']['periods'][0]['shortForecast']
    except requests.RequestException:
        return "Weather information not available."

# Function to get local time based on latitude and longitude
def get_local_time(lat, lon):
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    if timezone_str:
        timezone = pytz.timezone(timezone_str)
        dt = datetime.now(timezone)
        return dt, dt.hour
    return None, None

# Function to determine circadian color based on the time of day and weather
def get_circadian_color(time_of_day, weather_condition):
    colors = {
        'morning': {
            'clear': 'rgb(255, 213, 128)',
            'cloudy': 'rgb(176, 196, 222)',
            'rainy': 'rgb(119, 136, 153)',
            'sunny': 'rgb(255, 239, 213)'  # Adding sunny color
        },
        'day': {
            'clear': 'rgb(135, 206, 235)',
            'cloudy': 'rgb(173, 216, 230)',
            'rainy': 'rgb(70, 130, 180)',
            'sunny': 'rgb(135, 206, 250)'  # Adding sunny color
        },
        'evening': {
            'clear': 'rgb(255, 99, 71)',
            'cloudy': 'rgb(205, 92, 92)',
            'rainy': 'rgb(128, 0, 0)',
            'sunny': 'rgb(255, 164, 96)'  # Adding sunny color
        },
        'night': {
            'clear': 'rgb(72, 61, 139)',
            'cloudy': 'rgb(47, 79, 79)',
            'rainy': 'rgb(0, 0, 128)',
            'sunny': 'rgb(0, 51, 102)'  # Adding sunny color, though less likely at night
        }
    }
    return colors.get(time_of_day, {}).get(weather_condition, 'rgb(255, 255, 255)')  # Default color if key not found


def get_time_of_day_and_weather(dt, weather_description, wake_up_time, bedtime):
    hour = dt.hour
    wake_hour = wake_up_time.hour
    bed_hour = bedtime.hour
    
    # Determine the time of day
    if wake_hour <= hour < wake_hour + 3:
        time_of_day = 'morning'
    elif wake_hour + 3 <= hour < bed_hour - 5:
        time_of_day = 'day'
    elif bed_hour - 5 <= hour < bed_hour:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    # Categorize weather condition
    weather_description = weather_description.lower()
    if 'rain' in weather_description:
        weather_condition = 'rainy'
    elif 'cloud' in weather_description or 'overcast' in weather_description:
        weather_condition = 'cloudy'
    elif 'clear' in weather_description or 'sun' in weather_description:
        weather_condition = 'sunny'
    else:
        weather_condition = 'clear'  # Default condition if none other matches

    return time_of_day, weather_condition

def calculate_gradient_color(dt, wake_up_time, bedtime):
    now = datetime.now(dt.tzinfo)
    wake_time_dt = datetime.combine(now.date(), wake_up_time, tzinfo=dt.tzinfo)
    bedtime_dt = datetime.combine(now.date(), bedtime, tzinfo=dt.tzinfo)

    # Correct for cases where the wake time or bedtime might have already passed
    if dt.time() > wake_time_dt.time():
        wake_time_dt += timedelta(days=1)
    if dt.time() > bedtime_dt.time():
        bedtime_dt -= timedelta(days=1)

    # Calculate time differences in seconds
    seconds_until_wake = (wake_time_dt - dt).total_seconds()
    seconds_until_bed = (bedtime_dt - dt).total_seconds()

    # Normalize these times to a scale from 0 to 1 for gradient calculation
    max_seconds = 12 * 3600  # Consider a half-day period for full gradient change
    wake_gradient = max(0, min(1, 1 - (seconds_until_wake / max_seconds)))
    bed_gradient = max(0, min(1, 1 - (seconds_until_bed / max_seconds)))

    # Colors for morning (wake up) and evening (going to bed)
    wake_color = interpolate_color((255, 255, 255), (255, 213, 128), wake_gradient)  # from white to morning color
    bed_color = interpolate_color((135, 206, 235), (72, 61, 139), bed_gradient)      # from day to night color

    return f'rgb{wake_color}', f'rgb{bed_color}'

def interpolate_color(start_color, end_color, gradient):
    return tuple(int(start_color[i] + (end_color[i] - start_color[i]) * gradient) for i in range(3))


def get_time_of_day_and_weather(dt, weather_description, wake_up_time, bedtime):
    hour = dt.hour
    wake_hour = wake_up_time.hour
    bed_hour = bedtime.hour
    
    if wake_hour <= hour < wake_hour + 3:
        time_of_day = 'morning'
    elif wake_hour + 3 <= hour < bed_hour - 5:
        time_of_day = 'day'
    elif bed_hour - 5 <= hour < bed_hour:
        time_of_day = 'evening'
    else:
        time_of_day = 'night'

    weather_condition = 'clear'
    if 'rain' in weather_description.lower():
        weather_condition = 'rainy'
    elif 'cloud' in weather_description.lower():
        weather_condition = 'cloudy'
    elif 'clear' in weather_description.lower() or 'sun' in weather_description.lower():
        weather_condition = 'sunny'

    return time_of_day, weather_condition

def main():
    st.markdown("""
        <style>
            h1, h2, h3, h4, h5, h6, p, div, span {
                color: #A1D3F2;  /* Cream color for all text */
            }
            .stTextInput>label, .stCheckbox>label, .stTimeInput>label {
                color: #A1D3F2;  /* Specific selectors for input labels */
            }
        </style>
        """, unsafe_allow_html=True)
    
    st.title('Circadian Hues')
    location = st.text_input('Enter location (e.g., New York, Tokyo, London):')
    sleep_mode = st.checkbox('Activate Sleep Mode')
    wake_up_time = st.time_input("Wake up time", value=datetime.strptime("06:00", '%H:%M').time())
    bedtime = st.time_input("Bedtime", value=datetime.strptime("22:00", '%H:%M').time())

    if st.button('Get Circadian Colour'):
        if location:
            lat, lon = geocode_location(location)
            if lat and lon:
                weather_description = fetch_weather(lat, lon)
                dt, _ = get_local_time(lat, lon)
                time_of_day, weather_condition = get_time_of_day_and_weather(dt, weather_description, wake_up_time, bedtime)
                
                if sleep_mode:
                    wake_color, bed_color = calculate_gradient_color(dt, wake_up_time, bedtime)
                    st.success(f"Weather forecast for {location}: {weather_description}")
                    st.success(f"Local time in {location}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"#### Wake-Up Gradient Color")
                    st.markdown(f'<div style="height: 20px; width: 100%; background: linear-gradient(to right, {wake_color}, {bed_color});"></div>', unsafe_allow_html=True)
                else:
                    circadian_color = get_circadian_color(time_of_day, weather_condition)
                    st.success(f"Weather forecast for {location}: {weather_description}")
                    st.success(f"Local time in {location}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"#### Circadian Color")
                    st.markdown(f'<div style="height: 20px; width: 100%; background-color: {circadian_color};"></div>', unsafe_allow_html=True)
            else:
                st.error("Could not find this location.")
        else:
            st.error("Please enter a location.")

if __name__ == "__main__":
    main()
