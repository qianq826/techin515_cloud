import streamlit as st
import requests
from timezonefinder import TimezoneFinder
from datetime import datetime, timedelta
import pytz

def geocode_location(location):
    """Geocode the location to latitude and longitude using Nominatim API."""
    url = "https://nominatim.openstreetmap.org/search"
    params = {'q': location, 'format': 'json'}
    response = requests.get(url, params=params)
    if response.status_code == 200 and response.json():
        data = response.json()[0]
        return float(data['lat']), float(data['lon'])
    return None, None

def fetch_weather(lat, lon):
    """Fetch the weather for the given latitude and longitude using weather.gov API."""
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

def get_local_time(lat, lon):
    """Get the local time of the given latitude and longitude using timezonefinder and pytz."""
    tf = TimezoneFinder()
    timezone_str = tf.timezone_at(lat=lat, lng=lon)
    if timezone_str:
        timezone = pytz.timezone(timezone_str)
        dt = datetime.now(timezone)
        return dt, dt.hour
    return None, None

def get_time_of_day_and_weather(dt, weather_description, wake_up_time, bedtime):
    """Determine the time of day based on current hour and adjust for sleep schedule."""
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

    weather_condition = 'clear'  # default
    if 'rain' in weather_description.lower():
        weather_condition = 'rainy'
    elif 'cloud' in weather_description.lower():
        weather_condition = 'cloudy'
    elif 'clear' in weather_description.lower() or 'sun' in weather_description.lower():
        weather_condition = 'sunny'

    return time_of_day, weather_condition

def get_circadian_color(time_of_day, weather_condition):
    """Return a color in RGB format based on time of day and weather conditions."""
    colors = {
        'morning': {
            'clear': (255, 213, 128),
            'cloudy': (176, 196, 222),
            'rainy': (119, 136, 153),
        },
        'day': {
            'clear': (135, 206, 235),
            'cloudy': (173, 216, 230),
            'rainy': (70, 130, 180),
        },
        'evening': {
            'clear': (255, 99, 71),
            'cloudy': (205, 92, 92),
            'rainy': (128, 0, 0),
        },
        'night': {
            'clear': (72, 61, 139),
            'cloudy': (47, 79, 79),
            'rainy': (0, 0, 128),
        }
    }
    return colors.get(time_of_day, {}).get(weather_condition, (255, 255, 255))

def calculate_gradient_color(circadian_color, dt, wake_up_time, bedtime):
    """Calculate gradient colors based on the time until wake-up and bedtime."""
    # Prepare datetime objects with timezone for comparisons
    wake_time_dt = datetime.combine(dt.date(), wake_up_time, tzinfo=dt.tzinfo)
    bedtime_dt = datetime.combine(dt.date(), bedtime, tzinfo=dt.tzinfo)

    # Adjust wake_time_dt to next day if it's already past wake-up time
    if dt > wake_time_dt:
        wake_time_dt += timedelta(days=1)

    # Calculate time until wake-up and bedtime
    minutes_until_wake = (wake_time_dt - dt).total_seconds() / 60
    minutes_until_bed = (bedtime_dt - dt).total_seconds() / 60

    # Set colors for wake-up (bright to less bright) and bedtime (less bright to dark)
    wake_color_base = (255, 235, 200)  # Bright yellowish
    bed_color_base = (135, 206, 235)   # Calm blue
    dark_color = (72, 61, 139)         # Dark blue

    # Interpolation function to calculate gradient
    def interpolate_color(base_color, target_color, ratio):
        return tuple(int(base_color[i] * ratio + target_color[i] * (1 - ratio)) for i in range(3))

    # Calculate gradient colors
    wake_color = interpolate_color(wake_color_base, bed_color_base, min(1, max(0, minutes_until_wake / 30)))
    bed_color = interpolate_color(bed_color_base, dark_color, min(1, max(0, minutes_until_bed / 30)))

    return f'rgb{wake_color}', f'rgb{bed_color}'

def main():
    st.title('Circadian Floor Lamp App')
    location = st.text_input('Enter location (e.g., New York, Tokyo, London):')
    sleep_mode = st.checkbox('Activate Sleep Mode')
    wake_up_time = st.time_input("Wake up time", value=datetime.strptime("06:00", '%H:%M').time())
    bedtime = st.time_input("Bedtime", value=datetime.strptime("22:00", '%H:%M').time())

    if st.button('Get Circadian Colour'):
        if location:
            lat, lon = geocode_location(location)
            if lat is not None and lon is not None:
                weather = fetch_weather(lat, lon)
                dt, hour = get_local_time(lat, lon)
                time_of_day, weather_condition = get_time_of_day_and_weather(dt, weather, wake_up_time, bedtime)
                circadian_color = get_circadian_color(time_of_day, weather_condition)

                if sleep_mode and dt:
                    wake_color, bed_color = calculate_gradient_color(circadian_color, dt, wake_up_time, bedtime)

                    st.success(f"Weather forecast for {location}: {weather}")
                    st.success(f"Local time in {location}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"#### Wake-Up Gradient Color")
                    st.markdown(f'<div style="height: 20px; width: 300px; background-color: {wake_color}; margin: 10px auto;"></div>', unsafe_allow_html=True)
                    st.markdown(f"#### Bedtime Gradient Color")
                    st.markdown(f'<div style="height: 20px; width: 300px; background-color: {bed_color}; margin: 10px auto;"></div>', unsafe_allow_html=True)
                else:
                    st.success(f"Weather forecast for {location}: {weather}")
                    st.success(f"Local time in {location}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    st.markdown(f"#### Circadian Color")
                    st.markdown(f'<div style="height: 150px; width: 150px; background-color: {circadian_color}; border: 2px solid grey; margin: 10px auto;"></div>', unsafe_allow_html=True)
            else:
                st.error("Could not find this location.")
        else:
            st.error("Please enter a location.")

if __name__ == "__main__":
    main()
