# utils.py

import folium
import branca.colormap as cm
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point
from shapely.errors import TopologicalError
import warnings
import io

def plot_full_india_map(states_gdf):
    """Plot the full India map with state labels."""
    fig, ax = plt.subplots(figsize=(8, 10))
    states_gdf.boundary.plot(ax=ax, linewidth=0.8, edgecolor='black')
    states_gdf.plot(ax=ax, alpha=0.1)

    # Add labels
    for idx, row in states_gdf.iterrows():
        if row.geometry.is_empty or row.geometry.centroid.is_empty:
            continue
        point = row.geometry.centroid
        ax.text(point.x, point.y, row['State'], fontsize=7, ha='center')

    ax.axis('off')
    return fig


def draw_map_lines_with_labels(
    geo_data,
    selected_data,
    target_coords=None,
    line_style="Straight",
    label_field="State",
    show_boundaries=True
):
    """Draw map with optional lines and region labels."""
    fig, ax = plt.subplots(figsize=(8, 10))

    try:
        cleaned_geo = geo_data.copy()
        cleaned_geo['geometry'] = cleaned_geo['geometry'].buffer(0)  # Clean invalid geometries
    except TopologicalError:
        cleaned_geo = geo_data  # fallback

    # Plot background boundaries if toggled
    if show_boundaries:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                gpd.GeoSeries(cleaned_geo.unary_union.boundary).plot(ax=ax, linewidth=0.4, edgecolor='lightgray')
            except Exception:
                pass

    # Plot selected regions with darker color
    selected_data.plot(ax=ax, color='skyblue', edgecolor='black', linewidth=0.8)

    # Draw labels only for selected data
    for _, row in selected_data.iterrows():
        if row.geometry.is_empty:
            continue
        center = row.geometry.centroid
        label = row[label_field] if label_field in row else "Label"
        ax.text(center.x, center.y, label, fontsize=8, ha='center', weight='bold')

    # Draw lines if targets are given
    if target_coords and not selected_data.empty:
        for target in target_coords:
            for _, row in selected_data.iterrows():
                try:
                    centroid = row.geometry.centroid
                    line = LineString([centroid, Point(target)])
                    linestyle = '-' if line_style == "Straight" else '--' if line_style == "Dashed" else ':'
                    ax.plot(*line.xy, color='red', linestyle=linestyle)
                except Exception as e:
                    continue

    ax.axis('off')
    return fig


def add_hover_tooltips(map_obj, gdf, field_to_color, tooltip_fields, tooltip_aliases):
    min_val = gdf[field_to_color].min()
    max_val = gdf[field_to_color].max()
    colormap = cm.linear.YlGnBu_09.scale(min_val, max_val)
    colormap.caption = f"{field_to_color} Scale"

    folium.GeoJson(
        gdf,
        style_function=lambda feature: {
            'fillColor': colormap(feature['properties'][field_to_color]),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=tooltip_fields,
            aliases=tooltip_aliases,
            localize=True,
            sticky=True
        )
    ).add_to(map_obj)

    colormap.add_to(map_obj)


def buffer_geometries(gdf, distance_km):
    """Buffer geometries by distance (km) using a metric CRS, return GeoDataFrame in WGS84."""
    if gdf.empty:
        return gdf

    # Use Web Mercator for simplicity; acceptable for small buffers at this scale
    try:
        metric = gdf.to_crs(epsg=3857)
        buffered = metric.copy()
        buffered["geometry"] = metric.geometry.buffer(distance_km * 1000)
        return buffered.to_crs(epsg=4326)
    except Exception:
        return gdf  # fallback to original if reprojection fails


def export_gdf_as_geojson_bytes(gdf):
    """Serialize GeoDataFrame to GeoJSON bytes for download."""
    if gdf.empty:
        return b"{}"
    buf = io.StringIO()
    gdf.to_json(buf)
    return buf.getvalue().encode("utf-8")
