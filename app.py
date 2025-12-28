import streamlit as st
st.set_page_config(page_title="India Map Visualizer", layout="centered")
from streamlit_folium import st_folium
import folium
import random
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point
from utils import (
    add_hover_tooltips,
    plot_full_india_map,
    draw_map_lines_with_labels,
    buffer_geometries,
    export_gdf_as_geojson_bytes,
)
import io
import os

# === Load GeoJSONs ===
state_path = os.path.join("data", "in.json")
district_path = os.path.join("data", "output.geojson")

states = gpd.read_file(state_path).rename(columns={"name": "State"}).to_crs(epsg=4326)
states["State"] = states["State"].str.strip()


@st.cache_data
def load_districts(path):
    """Load districts GeoJSON and normalize naming."""
    districts_df = gpd.read_file(path).to_crs(epsg=4326)
    if "district" not in districts_df.columns and "dtname" in districts_df.columns:
        districts_df = districts_df.rename(columns={"dtname": "district"})
    if "district" in districts_df.columns:
        districts_df["district"] = districts_df["district"].str.strip()
    return districts_df


# Try loading districts once and reuse; surface errors later in UI
districts = None
districts_load_error = None
try:
    districts = load_districts(district_path)
except Exception as exc:
    districts_load_error = exc

# Title
st.title("🗺️ India Map Visualizer")
st.markdown("Select states or districts and optionally draw connection lines.")

# Sidebar: quick data downloads
st.sidebar.header("📂 Data Library")
st.sidebar.download_button(
    "Download States GeoJSON",
    data=export_gdf_as_geojson_bytes(states),
    file_name="india_states.geojson",
    mime="application/geo+json",
    help="Full India states boundary dataset",
)

if districts is not None:
    st.sidebar.download_button(
        "Download Districts GeoJSON",
        data=export_gdf_as_geojson_bytes(districts),
        file_name="india_districts.geojson",
        mime="application/geo+json",
        help="Full India districts boundary dataset",
    )
else:
    st.sidebar.warning("District dataset unavailable; see main panel for details.")

# Show full India map
fig_full = plot_full_india_map(states)
st.pyplot(fig_full)

# Download full map
buf = io.BytesIO()
fig_full.savefig(buf, format="png")
st.download_button("📥 Download India Map", data=buf.getvalue(), file_name="india_map.png", mime="image/png")

# --- Selection ---
st.markdown("---")
st.header("🔗 Select Regions & Draw Connections")

mode = st.radio("Choose connection type:", ["State-to-State", "District-to-District"])
line_type = st.selectbox("Choose line style", ["Straight", "Dashed", "Curved"])
show_boundaries = st.checkbox("Show boundaries of other states/districts", value=True)

# Target point input (optional)
st.markdown("### 📍 Optional: Click on map to add target points")
clicks = st.session_state.get("clicks", [])

if st.button("Clear Clicks"):
    st.session_state["clicks"] = []
    clicks = []

if "clicks" not in st.session_state:
    st.session_state["clicks"] = []

clicked_lon = st.number_input("Click Longitude", value=77.0)
clicked_lat = st.number_input("Click Latitude", value=28.0)
if st.button("Add Target Point"):
    st.session_state["clicks"].append((clicked_lon, clicked_lat))
    clicks = st.session_state["clicks"]

st.markdown(f"**Current Target Points:** {st.session_state['clicks']}")

# --- Region selection ---
selected_data = None

if mode == "State-to-State":
    state_options = states["State"].sort_values().unique().tolist()
    selected_states = st.multiselect("Select State(s)", state_options, default=["Madhya Pradesh"])
    selected_data = states[states["State"].isin(selected_states)]

else:
    if districts is None:
        st.error("❌ Could not load district GeoJSON.")
        if districts_load_error:
            st.exception(districts_load_error)
        st.stop()
    if "district" not in districts.columns:
        st.warning("⚠️ 'district' column not found in district data.")
        st.write("Available columns:", list(districts.columns))
    district_options = districts["district"].sort_values().unique().tolist()
    selected_districts = st.multiselect("Select District(s)", district_options)
    selected_data = districts[districts["district"].isin(selected_districts)]

# --- Export and buffer tools ---
st.markdown("### 📤 Export & Buffer Tools")
if selected_data is not None and not selected_data.empty:
    st.download_button(
        "Download Selected Features (GeoJSON)",
        data=export_gdf_as_geojson_bytes(selected_data),
        file_name=f"{mode.replace(' ', '_').lower()}_selection.geojson",
        mime="application/geo+json",
    )

    buffer_km = st.number_input("Buffer selected features (km)", min_value=0.0, max_value=500.0, value=0.0, step=1.0)
    if buffer_km > 0:
        buffered = buffer_geometries(selected_data, buffer_km)
        fig_buf, ax_buf = plt.subplots(figsize=(6, 7))
        buffered.plot(ax=ax_buf, color="lightcoral", alpha=0.5, edgecolor="red", linewidth=0.7)
        selected_data.boundary.plot(ax=ax_buf, color="black", linewidth=0.5)
        ax_buf.set_title(f"Buffered by {buffer_km} km")
        ax_buf.axis("off")
        st.pyplot(fig_buf)
        st.download_button(
            f"Download Buffered (+{buffer_km} km) GeoJSON",
            data=export_gdf_as_geojson_bytes(buffered),
            file_name=f"{mode.replace(' ', '_').lower()}_buffer_{int(buffer_km)}km.geojson",
            mime="application/geo+json",
        )
else:
    st.info("Select at least one state/district to enable export and buffering.")

# --- Draw button ---
# --- Draw button ---
if st.button("🖍️ Generate Map") and selected_data is not None:
    fig = draw_map_lines_with_labels(
        geo_data=states if mode == "State-to-State" else districts,
        selected_data=selected_data,
        target_coords=clicks if clicks else None,
        line_style=line_type,
        label_field='State' if mode == 'State-to-State' else 'district',
        show_boundaries=show_boundaries
    )
    st.session_state["generated_fig"] = fig  # Save figure in session state

# --- Display map & download ---
if "generated_fig" in st.session_state:
    fig = st.session_state["generated_fig"]
    st.pyplot(fig)

    buf = io.BytesIO()
    fig.savefig(buf, format="png")
    st.download_button("📥 Download Map", data=buf.getvalue(), file_name="map_with_lines.png", mime="image/png")


# --- Interactive Folium Map ---
st.markdown("---")
st.header("🗺️ Interactive Map with Hover Tooltips & Coloring")

folium_mode = st.radio("Select interactive map type", ["State Map (Population Color)", "District Map (Index Color)"])

@st.cache_data
def get_population(_states_df):
    return [random.randint(1_000_000, 50_000_000) for _ in range(len(_states_df))]

if folium_mode == "State Map (Population Color)":
    states["Population"] = get_population(states)

    m = folium.Map(location=[22.0, 78.0], zoom_start=5, tiles="cartodbpositron")
    add_hover_tooltips(
        m,
        states,
        field_to_color="Population",
        tooltip_fields=["State", "Population"],
        tooltip_aliases=["State:", "Population:"]
    )

    st_folium(m, width=1000, height=600)

elif folium_mode == "District Map (Index Color)":
    if districts is None:
        st.error("❌ Could not load district GeoJSON.")
        if districts_load_error:
            st.exception(districts_load_error)
    else:
        districts = districts.copy()
        districts["Index"] = list(range(len(districts)))  # dummy data

        m = folium.Map(location=[22.0, 78.0], zoom_start=5, tiles="cartodbpositron")
        add_hover_tooltips(
            m,
            districts,
            field_to_color="Index",
            tooltip_fields=["district", "Index"],
            tooltip_aliases=["District:", "Index:"]
        )

        st_folium(m, width=1000, height=600)
