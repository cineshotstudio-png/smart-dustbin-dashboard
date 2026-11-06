
import streamlit as st
import folium
import requests
import re
import math
from streamlit_folium import st_folium

# --------------------------------
# PAGE CONFIGURATION
# --------------------------------

st.set_page_config(
    page_title="Smart Waste Management",
    page_icon="♻️",
    layout="wide"
)

# --------------------------------
# DUSTBIN GPS LOCATION
# --------------------------------

DUSTBIN_LAT = 22.163441619476508
DUSTBIN_LON = 84.28104928703394

# --------------------------------
# GREEN DASHBOARD DESIGN
# --------------------------------

st.markdown("""
<style>
.stApp {
    background-color: #f0f8f1;
}
h1, h2, h3 {
    color: #176b3a;
}
.metric-card {
    background: white;
    padding: 18px;
    border-radius: 12px;
    border-left: 5px solid #239b56;
    box-shadow: 0 2px 8px rgba(0,0,0,0.06);
}
.alert-card {
    background: #e0f5e8;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #83c99b;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------
# HELPER FUNCTIONS
# --------------------------------

def calculate_distance(lat1, lon1, lat2, lon2):
    radius = 6371

    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )

    return 2 * radius * math.asin(math.sqrt(a))


def extract_coordinates(message):
    lat_match = re.search(
        r"LAT\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        message,
        re.IGNORECASE
    )

    lon_match = re.search(
        r"LON\s*[:=]\s*(-?\d+(?:\.\d+)?)",
        message,
        re.IGNORECASE
    )

    if lat_match and lon_match:
        lat = float(lat_match.group(1))
        lon = float(lon_match.group(1))

        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return lat, lon

    return None, None


def get_route(start_lat, start_lon, end_lat, end_lon):
    url = (
        "https://router.project-osrm.org/route/v1/driving/"
        f"{start_lon},{start_lat};{end_lon},{end_lat}"
        "?overview=full&geometries=geojson"
    )

    response = requests.get(url, timeout=20)
    response.raise_for_status()

    data = response.json()

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    route = data["routes"][0]

    coordinates = [
        [point[1], point[0]]
        for point in route["geometry"]["coordinates"]
    ]

    distance_km = route["distance"] / 1000
    duration_min = route["duration"] / 60

    return coordinates, distance_km, duration_min


# --------------------------------
# HEADER
# --------------------------------

st.title("♻️ SMART WASTE MANAGEMENT SYSTEM")
st.caption("GPS-Based Dustbin Monitoring and Smart Garbage Collection")

st.divider()

# --------------------------------
# SIDEBAR SETTINGS
# --------------------------------

st.sidebar.title("⚙️ Dashboard Settings")

st.sidebar.subheader("Collection Team Location")

start_lat = st.sidebar.number_input(
    "Team Latitude",
    value=22.150000,
    format="%.6f"
)

start_lon = st.sidebar.number_input(
    "Team Longitude",
    value=84.270000,
    format="%.6f"
)

st.sidebar.caption(
    "These are sample starting coordinates. "
    "Enter the collection team's actual GPS coordinates."
)

st.sidebar.divider()

st.sidebar.subheader("Dustbin Location")

st.sidebar.write(f"Latitude: {DUSTBIN_LAT}")
st.sidebar.write(f"Longitude: {DUSTBIN_LON}")

st.sidebar.link_button(
    "📍 View Dustbin in Google Maps",
    f"https://www.google.com/maps?q={DUSTBIN_LAT},{DUSTBIN_LON}"
)

# --------------------------------
# SMS ALERT SECTION
# --------------------------------

st.header("📩 SMS Alert Section")

sms_message = st.text_area(
    "Paste the SMS received from the GSM module",
    placeholder=(
        "Example:\n"
        "DUSTBIN FULL!\n"
        "LAT: 22.1634416\n"
        "LON: 84.2810492"
    ),
    height=120
)

if st.button("Process SMS Alert", type="primary"):
    if sms_message.strip():
        st.session_state["latest_sms"] = sms_message
        lat, lon = extract_coordinates(sms_message)

        if lat is not None and lon is not None:
            st.session_state["sms_lat"] = lat
            st.session_state["sms_lon"] = lon
            st.session_state["sms_error"] = ""
        else:
            st.session_state["sms_error"] = (
                "Coordinates not found. Use LAT: value and LON: value."
            )
    else:
        st.warning("Please paste an SMS message first.")

if "latest_sms" in st.session_state:
    st.markdown(
        f"""
        <div class="alert-card">
        <h3>🚨 Latest Dustbin Alert</h3>
        <p>{st.session_state["latest_sms"]}</p>
        </div>
        """,
        unsafe_allow_html=True
    )

if st.session_state.get("sms_error"):
    st.warning(st.session_state["sms_error"])

if "sms_lat" in st.session_state:
    st.success(
        f"GPS coordinates received: "
        f"{st.session_state['sms_lat']}, "
        f"{st.session_state['sms_lon']}"
    )

st.divider()

# --------------------------------
# DASHBOARD METRICS
# --------------------------------

st.header("📊 Collection Dashboard")

distance_straight = calculate_distance(
    start_lat,
    start_lon,
    DUSTBIN_LAT,
    DUSTBIN_LON
)

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("System Status", "ONLINE")

with col2:
    st.metric("Dustbin Status", "FULL")

with col3:
    st.metric(
        "Straight-Line Distance",
        f"{distance_straight:.2f} km"
    )

st.divider()

# --------------------------------
# SATELLITE MAP SECTION
# --------------------------------

st.header("🛰️ Satellite Map and Collection Route")

st.caption(
    "Satellite imagery with the dustbin location, "
    "collection team and road route."
)

map_object = folium.Map(
    location=[DUSTBIN_LAT, DUSTBIN_LON],
    zoom_start=17,
    tiles=None
)

# Satellite layer
folium.TileLayer(
    tiles=(
        "https://server.arcgisonline.com/ArcGIS/rest/services/"
        "World_Imagery/MapServer/tile/{z}/{y}/{x}"
    ),
    attr="Esri, Maxar, Earthstar Geographics",
    name="Satellite View",
    overlay=False,
    control=True
).add_to(map_object)

# Street map option
folium.TileLayer(
    tiles="OpenStreetMap",
    name="Street Map",
    overlay=False,
    control=True
).add_to(map_object)

# Dustbin marker
folium.Marker(
    location=[DUSTBIN_LAT, DUSTBIN_LON],
    popup="SMART DUSTBIN LOCATION",
    tooltip="Dustbin - Full",
    icon=folium.Icon(color="red", icon="trash")
).add_to(map_object)

# Collection team marker
folium.Marker(
    location=[start_lat, start_lon],
    popup="COLLECTION TEAM LOCATION",
    tooltip="Collection Team",
    icon=folium.Icon(color="blue", icon="truck")
).add_to(map_object)

# Route calculation
try:
    route_result = get_route(
        start_lat,
        start_lon,
        DUSTBIN_LAT,
        DUSTBIN_LON
    )

    if route_result:
        route_coordinates, road_distance, travel_time = route_result

        folium.PolyLine(
            route_coordinates,
            color="green",
            weight=6,
            opacity=0.9,
            tooltip="Garbage Collection Route"
        ).add_to(map_object)

        st.success("Road route calculated successfully.")

        route_col1, route_col2 = st.columns(2)

        with route_col1:
            st.metric(
                "Road Distance",
                f"{road_distance:.2f} km"
            )

        with route_col2:
            st.metric(
                "Estimated Travel Time",
                f"{travel_time:.0f} minutes"
            )
    else:
        st.warning("No driving route was found.")

except requests.RequestException:
    st.warning(
        "Route service is unavailable. "
        "Check your internet connection and try again."
    )

except (KeyError, ValueError, TypeError):
    st.warning("Unable to process the route response.")

# Map controls
folium.LayerControl().add_to(map_object)

# Display map
st_folium(
    map_object,
    width=1100,
    height=600,
    returned_objects=[]
)

# --------------------------------
# GOOGLE MAPS NAVIGATION
# --------------------------------

st.subheader("🧭 Navigation")

google_maps_url = (
    "https://www.google.com/maps/dir/"
    f"{start_lat},{start_lon}/"
    f"{DUSTBIN_LAT},{DUSTBIN_LON}"
)

st.link_button(
    "🚛 Open Driving Route in Google Maps",
    google_maps_url
)

# --------------------------------
# FOOTER
# --------------------------------

st.divider()

st.markdown("""
<div style="text-align:center; color:#176b3a;">
    <h4>SMART WASTE MANAGEMENT SYSTEM</h4>
    GPS Monitoring | SMS Alerts | Automatic Waste Collection
    <br>
    Science Exhibition Project
</div>
""", unsafe_allow_html=True)
