import streamlit as st
import requests

def geocode_location(location):
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': location,
        'format': 'json'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    return None, None

def fetch_weather(lat, lon):
    url = f"https://api.weather.gov/points/{lat},{lon}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data['properties']['forecast']
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            return forecast_data['properties']['periods'][0]['detailedForecast']
    return "Weather information not available."

# Streamlit interface
st.title('Weather Lookup App')

location = st.text_input('Enter location (e.g., New York, Tokyo, London):')

if st.button('Get Weather'):
    if location:
        lat, lon = geocode_location(location)
        if lat and lon:
            weather = fetch_weather(lat, lon)
            st.success(f"Weather forecast for {location}: {weather}")
        else:
            st.error("Could not find this location.")
    else:
        st.error("Please enter a location.")

