import math
import re
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium


st.set_page_config(
    page_title="Ireland Traffic Signs Explorer",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; }
    .metric-card {
        background: #f0faf5; border-left: 4px solid #1D9E75;
        padding: 0.6rem 1rem; border-radius: 6px; margin-bottom: 0.4rem;
    }
    h1 { color: #0F6E56; }
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_data():
    df = pd.read_excel(
        "ireland_all_signs_merged.xlsx",
        sheet_name="Ireland_All_Signs",
        engine="openpyxl",
    )
    df["latitude"]  = pd.to_numeric(df["latitude"],  errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    df = df.dropna(subset=["latitude", "longitude"])

    # Parking subset
    park = df[df["dataset"] == "Parking"].copy()
    park["parking_type"] = park["parking_type"].fillna("unknown")
    park["fee_clean"] = park["fee"].apply(
        lambda x: "Free" if str(x).lower() in ("no", "nan", "") else
                  "Paid" if str(x).lower() in ("yes",) or (str(x) not in ("nan","")) else "Unknown"
    )
    park["wheelchair"] = park["wheelchair"].fillna("unknown")
    park["name"]       = park["name"].fillna("")
    park["operator"]   = park["operator"].fillna("")
    park["capacity"]   = park["capacity"].fillna("")

    # Speed limit subset — extract numeric value
    speed = df[df["signboard_type"].str.contains("Speed Limit", na=False, case=False)].copy()
    def extract_speed(s):
        m = re.search(r'(\d+)\s*(km/h|mph)', str(s), re.IGNORECASE)
        if m:
            val, unit = int(m.group(1)), m.group(2).lower()
            return val * 1.609 if unit == "mph" else val  # normalise to km/h
        return None
    speed["speed_kmh"] = speed["signboard_type"].apply(extract_speed)
    speed = speed.dropna(subset=["speed_kmh"])
    speed["speed_kmh"] = speed["speed_kmh"].astype(int)

    return df, park, speed

df, park_df, speed_df = load_data()


COUNTY_BOUNDS = {
    "Dublin":      (53.20, 53.56, -6.55, -5.99),
    "Cork":        (51.40, 52.20, -9.20, -7.80),
    "Galway":      (52.80, 53.60, -10.10, -8.20),
    "Limerick":    (52.35, 52.85, -9.00, -8.20),
    "Waterford":   (51.95, 52.40, -7.80, -6.90),
    "Kilkenny":    (52.35, 52.75, -7.55, -6.90),
    "Wexford":     (52.10, 52.60, -6.70, -6.00),
    "Kerry":       (51.50, 52.30, -10.50, -9.20),
    "Tipperary":   (52.20, 52.90, -8.30, -7.50),
    "Clare":       (52.50, 53.10, -9.60, -8.50),
    "Wicklow":     (52.75, 53.20, -6.60, -5.99),
    "Meath":       (53.35, 53.75, -7.00, -6.30),
    "Kildare":     (52.90, 53.30, -7.15, -6.60),
    "Louth":       (53.75, 54.10, -6.75, -6.10),
    "Mayo":        (53.40, 54.15, -10.20, -8.80),
    "Roscommon":   (53.35, 54.00, -8.65, -7.70),
    "Sligo":       (53.80, 54.50, -9.00, -8.00),
    "Donegal":     (54.20, 55.40, -8.80, -7.10),
    "Cavan":       (53.75, 54.20, -7.70, -6.90),
    "Monaghan":    (53.85, 54.30, -7.25, -6.60),
    "Laois":       (52.70, 53.10, -7.70, -6.95),
    "Offaly":      (52.80, 53.35, -8.20, -7.30),
    "Westmeath":   (53.30, 53.75, -8.00, -7.10),
    "Longford":    (53.55, 54.00, -8.10, -7.50),
    "Leitrim":     (53.70, 54.30, -8.35, -7.70),
    "Carlow":      (52.50, 52.85, -7.00, -6.60),
    "Belfast":     (54.50, 54.70, -6.10, -5.80),
    "Armagh":      (54.20, 54.45, -6.80, -6.30),
    "Down":        (54.10, 54.60, -6.20, -5.40),
    "Antrim":      (54.55, 55.30, -6.55, -5.80),
    "Londonderry": (54.80, 55.20, -7.50, -6.70),
    "Tyrone":      (54.30, 54.90, -7.70, -6.70),
    "Fermanagh":   (54.10, 54.55, -8.20, -7.30),
}

def filter_by_county(dataframe, county):
    if county == "All Ireland":
        return dataframe
    if county in COUNTY_BOUNDS:
        lat_min, lat_max, lon_min, lon_max = COUNTY_BOUNDS[county]
        return dataframe[
            (dataframe["latitude"].between(lat_min, lat_max)) &
            (dataframe["longitude"].between(lon_min, lon_max))
        ]
    return dataframe

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2 * R * math.asin(math.sqrt(a))


with st.sidebar:
    st.image("https://upload.wikimedia.org/wikipedia/commons/thumb/4/45/Flag_of_Ireland.svg/60px-Flag_of_Ireland.svg.png", width=40)
    st.title("🚦 Filters")

    st.subheader("📍 Area")
    county = st.selectbox("County / Region", ["All Ireland"] + sorted(COUNTY_BOUNDS.keys()))

    st.divider()
    st.subheader("🅿️ Parking Filters")

    parking_types = ["All"] + sorted([t for t in park_df["parking_type"].unique() if t != "unknown"])
    selected_type = st.selectbox("Parking type", parking_types)

    fee_opt = st.radio("Fee", ["All", "Free", "Paid"], horizontal=True)

    wc_opt = st.radio("Wheelchair accessible", ["All", "Yes", "No / Limited"], horizontal=True)

    st.divider()
    st.subheader("🚗 Speed Limit Filters")

    all_speeds = sorted(speed_df["speed_kmh"].unique())
    speed_range = st.slider(
        "Speed limit range (km/h)",
        min_value=int(min(all_speeds)),
        max_value=int(max(all_speeds)),
        value=(30, 100),
        step=10,
    )

    st.divider()
    st.subheader("🔍 Nearby Speed Limits")
    nearby_radius = st.slider("Radius from selected parking (m)", 100, 2000, 500, 100)
    show_nearby = st.checkbox("Enable — click a parking marker to activate", value=False)

    st.divider()
    st.subheader("🗺️ Map Layers")
    show_parking = st.checkbox("Show Parking", value=True)
    show_speed   = st.checkbox("Show Speed Limits", value=True)


park_filtered = filter_by_county(park_df, county)
if selected_type != "All":
    park_filtered = park_filtered[park_filtered["parking_type"] == selected_type]
if fee_opt == "Free":
    park_filtered = park_filtered[park_filtered["fee_clean"] == "Free"]
elif fee_opt == "Paid":
    park_filtered = park_filtered[park_filtered["fee_clean"] == "Paid"]
if wc_opt == "Yes":
    park_filtered = park_filtered[park_filtered["wheelchair"] == "yes"]
elif wc_opt == "No / Limited":
    park_filtered = park_filtered[park_filtered["wheelchair"].isin(["no", "limited"])]

speed_filtered = filter_by_county(speed_df, county)
speed_filtered = speed_filtered[
    speed_filtered["speed_kmh"].between(speed_range[0], speed_range[1])
]


st.title("🇮🇪 Ireland Traffic Signs Explorer")
st.caption("Parking locations + speed limit signs from OpenStreetMap | Merged dataset: 58,404 records")


c1, c2, c3, c4 = st.columns(4)
c1.metric("🅿️ Parking Locations",  f"{len(park_filtered):,}")
c2.metric("🚗 Speed Limit Signs",  f"{len(speed_filtered):,}")
c3.metric("📊 Total Dataset",      f"{len(df):,}")
c4.metric("📍 Area",              county)

st.divider()


# Determine map centre
if county != "All Ireland" and county in COUNTY_BOUNDS:
    b = COUNTY_BOUNDS[county]
    map_centre = [(b[0]+b[1])/2, (b[2]+b[3])/2]
    zoom = 11
else:
    map_centre = [53.35, -7.80]
    zoom = 7

m = folium.Map(location=map_centre, zoom_start=zoom, tiles="CartoDB positron")

# Speed limit colour map
def speed_color(kmh):
    if kmh <= 30:  return "#2196F3"   # blue
    if kmh <= 50:  return "#4CAF50"   # green
    if kmh <= 80:  return "#FF9800"   # orange
    if kmh <= 100: return "#F44336"   # red
    return "#9C27B0"                   # purple

# Parking type colour map
def parking_color(ptype):
    m = {
        "surface":      "#1D9E75",
        "underground":  "#0F6E56",
        "multi-storey": "#2196F3",
        "street_side":  "#FF9800",
        "lane":         "#FFC107",
        "layby":        "#9E9E9E",
    }
    return m.get(str(ptype).lower(), "#607D8B")


MAX_PINS = 3000


if show_speed:
    speed_layer = folium.FeatureGroup(name="Speed Limits", show=True)
    sample_s = speed_filtered.sample(min(MAX_PINS, len(speed_filtered)), random_state=1) if len(speed_filtered) > MAX_PINS else speed_filtered
    for _, row in sample_s.iterrows():
        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=6,
            color=speed_color(row["speed_kmh"]),
            fill=True,
            fill_color=speed_color(row["speed_kmh"]),
            fill_opacity=0.8,
            popup=folium.Popup(
                f"<b>{row['signboard_type']}</b><br>"
                f"<small>OSM: {row['osm_id']}</small>",
                max_width=200
            ),
            tooltip=f"⚡ {row['speed_kmh']} km/h",
        ).add_to(speed_layer)
    speed_layer.add_to(m)

# Parking layer
if show_parking:
    park_layer = folium.FeatureGroup(name="Parking", show=True)
    sample_p = park_filtered.sample(min(MAX_PINS, len(park_filtered)), random_state=1) if len(park_filtered) > MAX_PINS else park_filtered
    for _, row in sample_p.iterrows():
        label = row["name"] if row["name"] else row["signboard_type"]
        fee_label = f"Fee: {row['fee_clean']}" if row["fee_clean"] != "Unknown" else ""
        wc_label  = f"♿ {row['wheelchair']}" if row["wheelchair"] not in ("unknown","") else ""
        cap_label = f"Capacity: {row['capacity']}" if row["capacity"] not in ("","nan") else ""
        popup_html = (
            f"<b>{label}</b><br>"
            f"<small>Type: {row['parking_type']}</small><br>"
            + (f"<small>{fee_label}</small><br>" if fee_label else "")
            + (f"<small>{cap_label}</small><br>" if cap_label else "")
            + (f"<small>{wc_label}</small><br>" if wc_label else "")
            + f"<small>OSM: {row['osm_id']}</small>"
        )
        folium.Marker(
            location=[row["latitude"], row["longitude"]],
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=f"🅿️ {label}",
            icon=folium.Icon(
                color="green" if row["fee_clean"] == "Free" else "blue",
                icon="parking" if row["parking_type"] in ("multi-storey","underground") else "map-marker",
                prefix="fa",
            ),
        ).add_to(park_layer)
    park_layer.add_to(m)

# Speed limit legend
legend_html = """
<div style="position:fixed;bottom:30px;left:10px;z-index:1000;background:white;
     padding:10px 14px;border-radius:8px;border:1px solid #ccc;font-size:12px;
     box-shadow:2px 2px 6px rgba(0,0,0,.2);">
<b>Speed Limits</b><br>
<span style="color:#2196F3">●</span> ≤30 km/h &nbsp;
<span style="color:#4CAF50">●</span> ≤50 km/h<br>
<span style="color:#FF9800">●</span> ≤80 km/h &nbsp;
<span style="color:#F44336">●</span> ≤100 km/h<br>
<span style="color:#9C27B0">●</span> &gt;100 km/h<br><br>
<b>Parking</b><br>
<span style="color:green">📍</span> Free &nbsp;
<span style="color:blue">📍</span> Paid / Unknown
</div>
"""
m.get_root().html.add_child(folium.Element(legend_html))
folium.LayerControl().add_to(m)

# Render map
map_data = st_folium(m, width="100%", height=520, returned_objects=["last_object_clicked"])

st.divider()


if show_nearby and map_data and map_data.get("last_object_clicked"):
    click = map_data["last_object_clicked"]
    clat, clon = click.get("lat"), click.get("lng")
    if clat and clon:
        nearby = speed_filtered[
            speed_filtered.apply(
                lambda r: haversine(clat, clon, r["latitude"], r["longitude"]) <= nearby_radius,
                axis=1
            )
        ]
        st.subheader(f"⚡ Speed Limit Signs within {nearby_radius}m of clicked point ({clat:.4f}, {clon:.4f})")
        if len(nearby):
            st.success(f"Found **{len(nearby)}** speed limit signs nearby")
            st.dataframe(
                nearby[["osm_id","latitude","longitude","signboard_type","speed_kmh"]].reset_index(drop=True),
                use_container_width=True, height=220,
            )
        else:
            st.info("No speed limit signs found in this radius. Try increasing the radius in the sidebar.")

st.divider()


tab1, tab2 = st.tabs([f"🅿️ Parking Locations ({len(park_filtered):,})", f"🚗 Speed Limit Signs ({len(speed_filtered):,})"])

with tab1:
    st.caption("Showing filtered parking locations. Use the sidebar to refine results.")

    # Search bar
    search = st.text_input("🔎 Search by name or operator", placeholder="e.g. Q-Park, IFSC, Lidl...")
    tbl = park_filtered.copy()
    if search:
        mask = (
            tbl["name"].str.contains(search, case=False, na=False) |
            tbl["operator"].str.contains(search, case=False, na=False)
        )
        tbl = tbl[mask]

    display_cols = ["osm_id","latitude","longitude","signboard_type","parking_type",
                    "name","operator","fee_clean","capacity","wheelchair","access"]
    st.dataframe(
        tbl[display_cols].rename(columns={"fee_clean":"fee"}).reset_index(drop=True),
        use_container_width=True,
        height=380,
    )
    st.caption(f"Showing {len(tbl):,} rows")

with tab2:
    st.caption("All speed limit signs matching the current speed range and county filter.")
    disp = speed_filtered[["osm_id","latitude","longitude","signboard_type","speed_kmh","notes"]].copy()
    st.dataframe(disp.reset_index(drop=True), use_container_width=True, height=380)
    st.caption(f"Showing {len(disp):,} rows")


st.markdown("""
---
<small>Data: OpenStreetMap contributors (ODbL) · Built with Streamlit + Folium · Merged dataset: 58,404 records</small>
""", unsafe_allow_html=True)