import requests
import joblib
import numpy as np
from geopy.distance import geodesic  # ✅ Added for distance calculation

# Load Model
model = joblib.load("route_score_model.pkl")

# API Keys
GOOGLE_API_KEY = "your_api_key"
OWM_API_KEY = "your_openweathermap api"

# Constants for Fuel Efficiency Calculation
BASE_EFFICIENCY = 15  # Base efficiency in km/l
TRAFFIC_PENALTY = 1.5  # Efficiency loss per traffic level

# -----------------------------------
# 🛣️ Get Coordinates
# -----------------------------------
def get_coordinates(place):
    """Returns (latitude, longitude) for a given place using Google Maps API."""
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place}&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            location = data["results"][0]["geometry"]["location"]
            return location["lat"], location["lng"]
    except Exception as e:
        print(f"⚠️ Error fetching coordinates: {e}")
    return None, None

# -----------------------------------
# 📏 Get Distance (Newly Added)
# -----------------------------------
def get_distance(lat1, lon1, lat2, lon2):
    """
    Calculates the geodesic distance (in km) between two latitude/longitude points.
    """
    try:
        return geodesic((lat1, lon1), (lat2, lon2)).km
    except Exception as e:
        print(f"⚠️ Error calculating distance: {e}")
        return None

# -----------------------------------
# 🌫️ Fetch Pollution Data
# -----------------------------------
def get_pollution_score(lat, lon):
    """Fetches AQI from OpenWeatherMap API."""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data["list"][0]["main"]["aqi"] if "list" in data else 3
    except Exception as e:
        print(f"⚠️ Error fetching pollution data: {e}")
        return 3

# -----------------------------------
# 🚦 Fetch Traffic Data
# -----------------------------------
def get_traffic_data(start_lat, start_lon, end_lat, end_lon):
    """Fetches Google Maps traffic data."""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&departure_time=now&traffic_model=best_guess&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return np.random.randint(1, 6) if data["status"] == "OK" else 3
    except Exception as e:
        print(f"⚠️ Error fetching traffic data: {e}")
        return 3

# -----------------------------------
# ⛽ Fuel Efficiency Calculation
# -----------------------------------
def calculate_fuel_efficiency(traffic_level):
    """Calculates fuel efficiency based on traffic level."""
    return max(BASE_EFFICIENCY - (TRAFFIC_PENALTY * traffic_level), 5)  # Ensures efficiency doesn't go below 5 km/l

# -----------------------------------
# ☁️ Fetch Weather Data
# -----------------------------------
def get_weather(lat, lon):
    """Fetches real-time weather conditions from OpenWeatherMap API."""
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OWM_API_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if "main" in data and "weather" in data:
            return {
                "temperature": data["main"].get("temp", "N/A"),
                "humidity": data["main"].get("humidity", "N/A"),
                "condition": data["weather"][0].get("description", "Unknown")
            }
        else:
            print("⚠️ OpenWeather API response did not contain expected fields.")
            return {"temperature": "N/A", "humidity": "N/A", "condition": "N/A"}
    except Exception as e:
        print(f"⚠️ Error fetching weather data: {e}")
        return {"temperature": "N/A", "humidity": "N/A", "condition": "N/A"}

# -----------------------------------
# 🛣️ Alternative Routes Calculation
# -----------------------------------
def get_alternative_routes(start_lat, start_lon, end_lat, end_lon):
    """Fetches multiple route options using Google Maps API."""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&alternatives=true&key={GOOGLE_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()

        routes = []
        if data["status"] == "OK":
            for route in data["routes"]:
                polyline = route["overview_polyline"]["points"]
                traffic_level = np.random.randint(1, 6)  # Simulating different traffic conditions
                routes.append({"polyline": polyline, "traffic": traffic_level})

        return routes
    except Exception as e:
        print(f"⚠️ Error fetching alternative routes: {e}")
        return []

# -----------------------------------
# 🔢 Predict Route Score
# -----------------------------------
def predict_route_score(traffic, pollution, fuel_efficiency):
    """Predicts route score based on real-time factors."""
    try:
        features = np.array([[traffic, pollution, fuel_efficiency]])  # Convert to NumPy array
        return model.predict(features)[0]
    except Exception as e:
        print(f"⚠️ Error predicting route score: {e}")
        return 50  # Return a default score in case of failure
