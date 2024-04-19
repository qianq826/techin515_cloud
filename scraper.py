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
    # weather.gov API base URL
    url = f"https://api.weather.gov/points/{lat},{lon}"
    # First request to get the weather forecast URL
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        forecast_url = data['properties']['forecast']
        # Second request to get the actual forecast
        forecast_response = requests.get(forecast_url)
        if forecast_response.status_code == 200:
            forecast_data = forecast_response.json()
            return forecast_data['properties']['periods'][0]['detailedForecast']
    return "Weather information not available."

from flask import Flask, request, jsonify
app = Flask(__name__)

@app.route('/weather', methods=['GET'])
def get_weather():
    location = request.args.get('location')
    if location:
        lat, lon = geocode_location(location)
        if lat and lon:
            weather = fetch_weather(lat, lon)
            return jsonify({"location": location, "weather": weather})
        else:
            return jsonify({"error": "Location not found"}), 404
    return jsonify({"error": "No location provided"}), 400

if __name__ == '__main__':
    app.run(debug=True)
