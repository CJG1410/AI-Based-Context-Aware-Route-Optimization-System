import streamlit as st
import folium
from streamlit_folium import st_folium
from utils import (
    get_coordinates,
    get_pollution_score,
    get_alternative_routes,
    get_weather,
    predict_route_score,
    calculate_fuel_efficiency
)
import polyline

# Configure Streamlit Page
st.set_page_config(page_title="AI-Based Route Optimizer", layout="wide")

st.title("AI-Based Context-Aware Route Optimizer")
st.markdown(
    "Enhance your travel decisions by optimizing routes using **real-time air quality, traffic conditions, weather data, and fuel efficiency**."
)

# Initialize session state
if "route_info" not in st.session_state:
    st.session_state["route_info"] = None

# ------------------------------
# Route Input Form
# ------------------------------
with st.form("route_form"):
    col1, col2 = st.columns(2)
    with col1:
        start_place = st.text_input("Start Location", placeholder="e.g., Coimbatore")
    with col2:
        end_place = st.text_input("Destination", placeholder="e.g., Chennai")
    submit = st.form_submit_button("Optimize Route")

# ------------------------------
# Process Route Request
# ------------------------------
if submit:
    if not start_place.strip() or not end_place.strip():
        st.warning("Please enter both start and end locations.")
        st.stop()

    # Get coordinates
    lat1, lon1 = get_coordinates(start_place)
    lat2, lon2 = get_coordinates(end_place)

    if None in (lat1, lon1, lat2, lon2):
        st.error("Unable to retrieve coordinates. Please check the location names.")
        st.stop()

    # Real-time data fetch
    pollution = get_pollution_score(lat2, lon2) or 3
    weather_data = get_weather(lat2, lon2) or {
        "temperature": "N/A",
        "humidity": "N/A",
        "condition": "N/A"
    }

    # AQI Descriptions
    AQI_LABELS = {
        1: "Good",
        2: "Fair",
        3: "Moderate",
        4: "Poor",
        5: "Very Poor"
    }
    pollution_label = AQI_LABELS.get(pollution, "Unknown")

    # Get alternative routes
    routes = get_alternative_routes(lat1, lon1, lat2, lon2)

    if not routes:
        st.error("No alternative routes found.")
    else:
        route_scores = []
        for idx, route in enumerate(routes):
            traffic = route["traffic"]
            fuel_efficiency = calculate_fuel_efficiency(traffic)
            route_score = predict_route_score(traffic, pollution, fuel_efficiency)

            route_scores.append({
                "Route": f"Route {idx + 1}",
                "Traffic Level": traffic,
                "Fuel Efficiency (km/l)": round(fuel_efficiency, 2),
                "Route Score": round(route_score, 2),
                "polyline": route["polyline"]
            })

        # Sort routes by best score
        route_scores = sorted(route_scores, key=lambda x: x["Route Score"], reverse=True)

        # Mark recommended route
        best_route = route_scores[0]
        best_route["Route"] += " (Recommended)"

        # Store in session
        st.session_state["route_info"] = {
            "start_place": start_place,
            "end_place": end_place,
            "pollution": pollution,
            "pollution_label": pollution_label,
            "weather": weather_data,
            "routes": route_scores
        }

# ------------------------------
# Display Results
# ------------------------------
if st.session_state["route_info"]:
    info = st.session_state["route_info"]

    lat1, lon1 = get_coordinates(info["start_place"])
    lat2, lon2 = get_coordinates(info["end_place"])

    st.markdown(f"### Route: {info['start_place']} → {info['end_place']}")
    st.markdown(
        f"**Air Quality Index (AQI):** {info['pollution']} ({info['pollution_label']})  \n"
        f"**Weather Conditions:** {info['weather']['temperature']}°C, "
        f"Humidity: {info['weather']['humidity']}%, "
        f"Condition: {info['weather']['condition']}"
    )

    # Route table
    st.subheader("Alternative Route Comparison")
    st.table([
        {k: v for k, v in route.items() if k != "polyline"}
        for route in info["routes"]
    ])

    # Map
    if lat1 and lon1:
        route_map = folium.Map(location=[lat1, lon1], zoom_start=7)

        # High-contrast color palette
        colors = ["#1f78b4", "#33a02c", "#e31a1c", "#ff7f00", "#6a3d9a", "#b15928"]

        for i, route in enumerate(info["routes"]):
            route_coords = polyline.decode(route["polyline"])
            is_best = "Recommended" in route["Route"]
            color = "darkgreen" if is_best else colors[i % len(colors)]

            folium.PolyLine(
                locations=route_coords,
                color=color,
                weight=7 if is_best else 5,
                opacity=0.9,
                tooltip=route["Route"]
            ).add_to(route_map)

        st.subheader("Route Visualization")
        st_folium(route_map, use_container_width=True, height=550)
