import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import requests
from utils import get_coordinates, get_distance  # ✅ Import missing functions

# API Keys (Replace with your actual keys)
GOOGLE_API_KEY = "your_api_key"
OWM_API_KEY = "your_api_key"

# -----------------------------------
# Fetch Real-Time Data
# -----------------------------------
def get_pollution_score(lat, lon):
    """Fetches AQI from OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={OWM_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return data["list"][0]["main"]["aqi"] if "list" in data else None
    except:
        return None

def get_traffic_data(start_lat, start_lon, end_lat, end_lon):
    """Fetches traffic congestion data from Google Maps."""
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={start_lat},{start_lon}&destination={end_lat},{end_lon}&departure_time=now&traffic_model=best_guess&key={GOOGLE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        return np.random.randint(1, 6) if data["status"] == "OK" else None
    except:
        return None

def calculate_fuel_efficiency(distance, traffic_level, avg_speed):
    """
    Calculate fuel efficiency (km/l) based on traffic and speed.
    """
    BASE_EFFICIENCY = 20  
    TRAFFIC_PENALTY = 1.5  
    SPEED_BENEFIT = 0.05  
    
    efficiency = BASE_EFFICIENCY - (TRAFFIC_PENALTY * traffic_level)
    
    if avg_speed < 20:
        efficiency -= 4  
    elif 20 <= avg_speed < 40:
        efficiency += SPEED_BENEFIT * avg_speed
    elif 40 <= avg_speed < 60:
        efficiency += SPEED_BENEFIT * avg_speed * 1.2  
    else:
        efficiency -= 2  

    return max(efficiency, 5)  

# -----------------------------------
# Generate Dataset
# -----------------------------------
locations = [
    # 🇮🇳 India
    {"start": "Coimbatore", "end": "Chennai"},
    {"start": "Mumbai", "end": "Pune"},
    {"start": "Delhi", "end": "Jaipur"},
    {"start": "Bangalore", "end": "Hyderabad"},
    {"start": "Kolkata", "end": "Bhubaneswar"},
    
    # 🇺🇸 United States
    {"start": "New York", "end": "Washington DC"},
    {"start": "Los Angeles", "end": "San Francisco"},
    {"start": "Chicago", "end": "Detroit"},
    {"start": "Dallas", "end": "Houston"},
    {"start": "Miami", "end": "Orlando"},

    # 🇪🇺 Europe
    {"start": "London", "end": "Paris"},
    {"start": "Berlin", "end": "Amsterdam"},
    {"start": "Madrid", "end": "Barcelona"},
    {"start": "Rome", "end": "Milan"},
    {"start": "Vienna", "end": "Prague"},

    # 🇦🇺 Australia
    {"start": "Sydney", "end": "Melbourne"},
    {"start": "Perth", "end": "Adelaide"},
    
    # 🇨🇦 Canada
    {"start": "Toronto", "end": "Montreal"},
    {"start": "Vancouver", "end": "Calgary"},

    # 🇯🇵 Japan
    {"start": "Tokyo", "end": "Osaka"},
    {"start": "Kyoto", "end": "Hiroshima"},
    
    # 🇧🇷 Brazil
    {"start": "São Paulo", "end": "Rio de Janeiro"},
    {"start": "Brasilia", "end": "Salvador"},
    
    # 🇿🇦 South Africa
    {"start": "Johannesburg", "end": "Cape Town"},
    
    # 🇷🇺 Russia
    {"start": "Moscow", "end": "Saint Petersburg"},
    
    # 🇨🇳 China
    {"start": "Beijing", "end": "Shanghai"},
    {"start": "Guangzhou", "end": "Shenzhen"},
    
    # 🇲🇽 Mexico
    {"start": "Mexico City", "end": "Guadalajara"},
    
    # 🇦🇪 UAE
    {"start": "Dubai", "end": "Abu Dhabi"}
]

data = []

for loc in locations:
    start_lat, start_lon = get_coordinates(loc["start"])
    end_lat, end_lon = get_coordinates(loc["end"])

    pollution = get_pollution_score(end_lat, end_lon) or 3
    traffic = get_traffic_data(start_lat, start_lon, end_lat, end_lon) or 3
    distance = get_distance(start_lat, start_lon, end_lat, end_lon)
    avg_speed = 80 - (traffic * 10)  

    fuel_efficiency = calculate_fuel_efficiency(distance, traffic, avg_speed)

    data.append([traffic, pollution, fuel_efficiency, 100 - (traffic * 10)])

df = pd.DataFrame(data, columns=["traffic", "pollution", "fuel_efficiency", "score"])

print("Generated Dataset:\n", df)  
print(df["score"].describe())  


# Train Model
X = df[["traffic", "pollution", "fuel_efficiency"]]
y = df["score"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

joblib.dump(model, "route_score_model.pkl")
print("✅ Model saved as route_score_model.pkl")
