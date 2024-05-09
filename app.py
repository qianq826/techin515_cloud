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
    st.sidebar.image(logo.resize((400, 80)))

setup_ui()

def geocode_location(location):
    url = "https://nominatim.openstreetmap.org/search"
    headers = {'User-Agent': 'Your User Agent Name'}
    params = {'q': location, 'format': 'json'}
    try:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        if data:
            first_result = data[0]
            return float(first_result['lat']), float(first_result['lon'])
    except requests.exceptions.HTTPError as e:
        if response.status_code == 403:
            st.error("The request was forbidden by the server. Please try again later or provide a different location.")
        else:
            st.error(f"An error occurred while geocoding location: {e}")
    except Exception as e:
        st.error(f"An error occurred while geocoding location: {e}")
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
    except Exception as e:
        st.error(f"Error occurred while fetching weather data: {e}")
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

from datetime import datetime, timedelta

def calculate_all_gradient_colors(dt, wake_up_time, bedtime, weather_condition):
    colors = []
    max_seconds = 12 * 3600  # Considering half a day for a full gradient
    # Ensure datetime has the correct tzinfo
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=pytz.UTC)

    # Normalize wake_up_time and bedtime to datetime objects
    wake_time_dt = datetime.combine(dt.date(), wake_up_time, tzinfo=dt.tzinfo)
    bedtime_dt = datetime.combine(dt.date(), bedtime, tzinfo=dt.tzinfo)
    
    # Adjust bedtime_dt to the next day if it's before wake_time_dt
    if bedtime_dt <= wake_time_dt:
        bedtime_dt += timedelta(days=1)

    # Generate colors for each hour between wake_time_dt and bedtime_dt
    current_time = wake_time_dt
    while current_time <= bedtime_dt:
        # Calculate gradients based on the time until wake and bed
        seconds_until_wake = (wake_time_dt - current_time).total_seconds()
        seconds_until_bed = (bedtime_dt - current_time).total_seconds()

        wake_gradient = max(0, min(1, seconds_until_wake / max_seconds))
        bed_gradient = max(0, min(1, seconds_until_bed / max_seconds))

        # Adjust colors based on weather condition
        if weather_condition == 'sunny':
            wake_color = interpolate_color((255, 255, 255), (255, 239, 213), wake_gradient)
            bed_color = interpolate_color((135, 206, 250), (0, 51, 102), bed_gradient)
        elif weather_condition == 'cloudy':
            wake_color = interpolate_color((255, 255, 255), (176, 196, 222), wake_gradient)
            bed_color = interpolate_color((135, 206, 235), (47, 79, 79), bed_gradient)
        elif weather_condition == 'rainy':
            wake_color = interpolate_color((255, 255, 255), (119, 136, 153), wake_gradient)
            bed_color = interpolate_color((70, 130, 180), (0, 0, 128), bed_gradient)
        else:  # Default to clear weather
            wake_color = interpolate_color((255, 255, 255), (255, 213, 128), wake_gradient)
            bed_color = interpolate_color((135, 206, 235), (72, 61, 139), bed_gradient)

        colors.append((f"rgb{wake_color}", f"rgb{bed_color}"))
        current_time += timedelta(hours=1)

    return colors

def interpolate_color(start_color, end_color, factor):
    # Interpolate between two RGB colors
    return tuple(int(start_color[i] + (end_color[i] - start_color[i]) * factor) for i in range(3))

def calculate__gradient_colors(dt, wake_up_time, bedtime):
    colors = []
    # Calculate gradient colors for each hour between wake-up time and bedtime
    for hour in range(wake_up_time.hour, bedtime.hour + 1):
        time = datetime(dt.year, dt.month, dt.day, hour, 0, 0, tzinfo=dt.tzinfo)
        wake_color = calculate_all_gradient_colors(time, wake_up_time, bedtime)  # Change function name
        colors.append(wake_color)
    return colors

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
    location = st.text_input('Enter location in United Stated:')
    sleep_mode = st.checkbox('Activate Sleep Mode')
    wake_up_time = st.time_input("Wake up time", value=datetime.strptime("06:00", '%H:%M').time())
    bedtime = st.time_input("Bedtime", value=datetime.strptime("22:00", '%H:%M').time())

    if st.button('Get Circadian Colour'):
        if location:
            lat, lon = geocode_location(location)
            if lat is not None and lon is not None:
                weather_description = fetch_weather(lat, lon)
                dt, _ = get_local_time(lat, lon)
                time_of_day, weather_condition = get_time_of_day_and_weather(dt, weather_description, wake_up_time, bedtime)
                
                if sleep_mode:
                    colors = calculate_all_gradient_colors(dt, wake_up_time, bedtime, weather_condition)
                    st.success(f"Weather forecast for {location}: {weather_description}")
                    st.success(f"Local time in {location}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")

                    # Display the gradient color bar in the main page
                    gradient_css = ', '.join([f"linear-gradient(to right, {color[0]}, {color[1]})" for color in colors])
                    st.markdown(f"#### Wake-Up to Bedtime Gradient Colors")
                    st.markdown(f'<div style="height: 20px; width: 100%; background: {gradient_css};"></div>', unsafe_allow_html=True)

                    # Display single RGB colors in the sidebar with RGB values
                    st.sidebar.header("Hourly Colors")
                    for color in colors:
                        st.sidebar.markdown(f"**{color[1]}**")
                        st.sidebar.markdown(f"<div style='height: 20px; width: 100%; background-color: {color[1]}; margin-bottom: 5px;'></div>", unsafe_allow_html=True)
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
