
import streamlit as st
import folium
import requests
import math
import re
from streamlit_folium import st_folium

st.set_page_config(
    page_title="Smart Waste Management",
    page_icon="♻️",
    layout="wide"
)

# GREEN DASHBOARD DESIGN
st.markdown("""
<style>
.stApp {
    background-color: #f0f8f1;
    color: #183b28;
}
[data-testid="stSidebar"] {
    background-color: #dff1e3;
}
h1, h2, h3 {
    color: #176b39;
}
div.stButton > button {
    background-color: #198754;
    color: white;
    border-radius: 10px;
    border: none;
    font-weight: bold;
}
div.stButton > button:hover {
    background-color: #126b40;
    color: white;
}
div[data-testid="stMetric"] {
    background: white;
    border: 1px solid #d5ead9;
    padding: 15px;
    border-radius: 12px;
}
</style>
""", unsafe_allow_html=True)


# DISTANCE CALCULATION
def distance_km(lat1, lon1, lat2, lon2):
    r = 6371
    p1 = math.radians(lat1)
    p2 = math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)

    a = (math.sin(dp / 2) ** 2 +
         math.cos(p1) * math.cos(p2) *
         math.sin(dl / 2) ** 2)

    return 2 * r * math.asin(math.sqrt(a))


# READ GPS COORDINATES FROM SMS
def read_sms(message):
    lat = re.search(
        r"LAT\s*:\s*(-?\d+\.?\d*)", message, re.I
    )
    lon = re.search(
        r"LON\s*:\s*(-?\d+\.?\d*)", message, re.I
    )

    if lat and lon:
        latitude = float(lat.group(1))
        longitude = float(lon.group(1))

        if -90 <= latitude <= 90 and -180 <= longitude <= 180:
            return latitude, longitude

    return None


# DEFAULT DEMO LOCATION
if "dust_lat" not in st.session_state:
    st.session_state.dust_lat = 22.163441619476508

if "dust_lon" not in st.session_state:
    st.session_state.dust_lon = 84.28104928703394

if "sms" not in st.session_state:
    st.session_state.sms = "DEMO: DUSTBIN FULL"


# DASHBOARD TITLE
st.markdown("""
<div style="
background: linear-gradient(100deg,#14532d,#269653);
padding:25px;
border-radius:18px;
color:white;">
<h1 style="color:white;">♻️ SMART WASTE MANAGEMENT</h1>
<p style="color:#e8f5e9;">
Smart Dustbin Monitoring and GPS Collection System
</p>
</div>
""", unsafe_allow_html=True)

st.write("")


# SIDEBAR
st.sidebar.title("⚙️ Dashboard Control")

st.sidebar.subheader("Collection Team Location")

start_lat = st.sidebar.number_input(
    "Starting Latitude",
    value=22.120000,
    format="%.6f"
)

start_lon = st.sidebar.number_input(
    "Starting Longitude",
    value=84.030000,
    format="%.6f"
)

st.sidebar.divider()

st.sidebar.subheader("📩 SMS Alert Test")

sms_input = st.sidebar.text_area(
    "Paste received SMS",
    value="DUSTBIN FULL LAT: 22.120000 LON: 84.030000"
)

if st.sidebar.button("PROCESS SMS"):
    result = read_sms(sms_input)

    if result:
        st.session_state.dust_lat = result[0]
        st.session_state.dust_lon = result[1]
        st.session_state.sms = sms_input
        st.sidebar.success("GPS location updated!")
    else:
        st.sidebar.error("Invalid GPS coordinates in SMS.")


# COORDINATES
dust_lat = st.session_state.dust_lat
dust_lon = st.session_state.dust_lon

distance = distance_km(
    start_lat, start_lon,
    dust_lat, dust_lon
)


# DASHBOARD CARDS
c1, c2, c3 = st.columns(3)

c1.metric("SYSTEM STATUS", "ONLINE 🟢")
c2.metric("DUSTBIN STATUS", "FULL ⚠️")
c3.metric("DISTANCE", f"{distance:.2f} KM")


# MAP AND ALERT
left, right = st.columns([1.6, 1])

with left:
    st.subheader("🗺️ Dustbin Collection Route")

    m = folium.LayerControl().addfolium.Map(
    location=[dustbin_lat, dustbin_lon],
    zoom_start=17,
    tiles=None
)

folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Esri, Maxar, Earthstar Geographics",
    name="Satellite",
    overlay=False,
    control=True
).add_to(m)

folium.TileLayer(
    "OpenStreetMap",
    name="Street Map",
    overlay=False,
    control=True
).add_to(m)

folium.Marker(
        [start_lat, start_lon],
        popup="Collection Team",
        tooltip="Starting Point",
        icon=folium.Icon(color="blue")
    ).add_to(map_object)

    folium.Marker(
        [dust_lat, dust_lon],
        popup="Dustbin Location",
        tooltip="Dustbin",
        icon=folium.Icon(color="green")
    ).add_to(map_object)

    # ROAD ROUTE
    try:
        if (start_lat, start_lon) != (dust_lat, dust_lon):
            url = (
                "https://router.project-osrm.org/route/v1/driving/"
                f"{start_lon},{start_lat};{dust_lon},{dust_lat}"
                "?overview=full&geometries=geojson"
            )

            response = requests.get(url, timeout=15)
            data = response.json()

            if data["code"] == "Ok" and data["routes"]:
                route = data["routes"][0]

                route_points = [
                    [lat, lon]
                    for lon, lat in
                    route["geometry"]["coordinates"]
                ]

                folium.PolyLine(
                    route_points,
                    color="#168044",
                    weight=6,
                    opacity=0.9
                ).add_to(map_object)

                road_distance = route["distance"] / 1000
                travel_time = route["duration"] / 60

                map_object.fit_bounds([
                    [start_lat, start_lon],
                    [dust_lat, dust_lon]
                ])

                st_folium(
                    map_object,
                    width=None,
                    height=450
                )

                x, y = st.columns(2)
                x.metric("ROAD DISTANCE", f"{road_distance:.2f} KM")
                y.metric("TRAVEL TIME", f"{travel_time:.0f} MIN")

            else:
                st_folium(map_object, height=450)
                st.warning("Road route not found.")

        else:
            st_folium(map_object, height=450)
            st.info("Starting point and dustbin are the same.")

    except Exception:
        st_folium(map_object, height=450)
        st.warning("Route unavailable. Check internet connection.")

with right:
    st.subheader("📨 Latest SMS Alert")

    st.info(st.session_state.sms)

    st.subheader("📍 Dustbin GPS Location")

    st.write(f"Latitude: {dust_lat:.6f}")
    st.write(f"Longitude: {dust_lon:.6f}")

    google_url = (
        "https://www.google.com/maps/search/?api=1&query="
        f"{dust_lat},{dust_lon}"
    )

    st.link_button(
        "OPEN IN GOOGLE MAPS",
        google_url
    )


# FOOTER
st.divider()

st.subheader("How the System Works")

st.write("""
1. GPS detects the dustbin location.
2. Arduino detects the dustbin full condition.
3. SIM900A sends an SMS alert with GPS coordinates.
4. The dashboard reads the coordinates.
5. The map displays the dustbin and collection route.
""")

st.caption(
    "Demo coordinates are sample values. "
    "Automatic SMS connection requires an additional web connection."
)
