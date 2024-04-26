import streamlit as st
import requests
from timezonefinder import TimezoneFinder
from datetime import datetime
import pytz

def geocode_location(location):
    """Geocode the location to latitude and longitude using Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location,
        'format': 'json'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            lat, lon = float(data[0]['lat']), float(data[0]['lon'])
            return lat, lon
    return None, None

def fetch_weather(lat, lon):
    """Fetch the weather for the given latitude and longitude using weather.gov API."""
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data['properties']['forecast']
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            return forecast_data['properties']['periods'][0]['shortForecast']
    return "Weather information not available."

def get_local_time(lat, lon):
    """Get the local time of the given latitude and longitude using timezonefinder and pytz."""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    if timezone_str:
        timezone = pytz.timezone(timezone_str)
        dt = datetime.now(timezone)
        return dt.strftime('%Y-%m-%d %H:%M:%S'), dt.hour
    return "Time information not available", None

def get_time_of_day_and_weather(hour, weather_description):
    """Determine the time of day and categorize weather to return the appropriate settings for color calculation."""
    time_of_day = get_time_of_day(hour)
    weather_condition = 'clear'  # default
    if 'rain' in weather_description.lower():
        weather_condition = 'rainy'
    elif 'cloud' in weather_description.lower():
        weather_condition = 'cloudy'
    elif 'clear' in weather_description.lower() or 'sun' in weather_description.lower():
        weather_condition = 'sunny'
    
    return time_of_day, weather_condition

def get_time_of_day(hour):
    """Simple categorization of time of day based on hour."""
    if 5 <= hour < 10:
        return 'morning'
    elif 10 <= hour < 17:
        return 'day'
    elif 17 <= hour < 20:
        return 'evening'
    else:
        return 'night'

def get_circadian_color(time_of_day, weather_condition):
    """Return a color in RGB format based on time of day and weather conditions."""
    colors = {
        'morning': {
            'clear': (255, 213, 128),  # soft orange
            'cloudy': (176, 196, 222),  # light steel blue
            'rainy': (119, 136, 153),  # light slate gray
        },
        'day': {
            'clear': (135, 206, 235),  # sky blue
            'cloudy': (173, 216, 230),  # light blue
            'rainy': (70, 130, 180),  # steel blue
        },
        'evening': {
            'clear': (255, 99, 71),  # tomato red
            'cloudy': (205, 92, 92),  # indian red
            'rainy': (128, 0, 0),  # maroon
        },
        'night': {
            'clear': (72, 61, 139),  # dark slate blue
            'cloudy': (47, 79, 79),  # dark slate gray
            'rainy': (0, 0, 128),  # navy
        }
    }
    rgb = colors.get(time_of_day, {}).get(weather_condition, (255, 255, 255))
    return f'rgb{rgb}'  # format as rgb(r, g, b)

# Streamlit interface
def main():
    st.title('Circadian Floor Lamp App')
    location = st.text_input('Enter location (e.g., New York, Tokyo, London):')

    if st.button('Get Circadian Colour'):
        if location:
            lat, lon = geocode_location(location)
            if lat is not None and lon is not None:
                weather = fetch_weather(lat, lon)
                local_time, hour = get_local_time(lat, lon)
                time_of_day, weather_condition = get_time_of_day_and_weather(hour, weather)
                circadian_color = get_circadian_color(time_of_day, weather_condition)

                st.success(f"Weather forecast for {location}: {weather}")
                st.success(f"Local time in {location}: {local_time}")
                st.markdown(f"#### Circadian Color")
                st.markdown(f'<div style="height: 150px; width: 150px; background-color: {circadian_color}; border: 2px solid grey; margin: 10px auto;"></div>', unsafe_allow_html=True)
            else:
                st.error("Could not find this location.")
        else:
            st.error("Please enter a location.")

if __name__ == "__main__":
    main()
