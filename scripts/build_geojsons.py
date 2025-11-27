#!/usr/bin/env python3
"""
Utility to rebuild the GeoJSON files required by the Streamlit app.

It uses the level-2 administrative boundaries from the local GADM dataset
(`gadm41_IND_2.json`) to derive both:
  • `data/in.json`      -> India state polygons (dissolved from districts)
  • `data/output.geojson` -> India district polygons
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

import geopandas as gpd

DEFAULT_SOURCE = Path.home() / "Downloads" / "Download2" / "gadm41_IND_2.json"


def tidy_name(value: str) -> str:
    """Insert spaces into camel-cased names and normalise whitespace."""
    if not isinstance(value, str):
        return value
    cleaned = value.replace("_", " ").replace("-", " ")
    cleaned = re.sub(r"(?<=[a-z])and(?=[A-Z])", " and ", cleaned)
    cleaned = re.sub(r"(?<!\s)(?=[A-Z])", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def rebuild_geojsons(source: Path, output_dir: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source boundary file not found: {source}")
    output_dir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(source)
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(epsg=4326)

    gdf["state"] = gdf["NAME_1"].apply(tidy_name)
    gdf["district"] = gdf["NAME_2"].apply(tidy_name)
    districts = gdf[["state", "district", "geometry"]].copy()
    districts = districts.sort_values(["state", "district"]).reset_index(drop=True)

    # Dissolve district geometries to get state boundaries.
    states = districts.dissolve(by="state", as_index=False, aggfunc="first")
    states = states.rename(columns={"state": "name"})
    states = states[["name", "geometry"]]

    state_path = output_dir / "in.json"
    district_path = output_dir / "output.geojson"

    states.to_file(state_path, driver="GeoJSON")
    districts.to_file(district_path, driver="GeoJSON")

    print(f"Wrote {len(states)} states to {state_path}")
    print(f"Wrote {len(districts)} districts to {district_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Rebuild India state/district GeoJSON files from a local GADM dataset."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help=f"Path to gadm41_IND_2.json (default: {DEFAULT_SOURCE})",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data"),
        help="Directory where GeoJSON files will be written (default: ./data)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rebuild_geojsons(args.source.expanduser(), args.output_dir)


if __name__ == "__main__":
    main()
