import argparse
from pathlib import Path

import geopandas as gpd

from benin_least_cost.demand import run_demand_model
from benin_least_cost.lcoe import run_lcoe_model


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run the Benin least-cost electrification pipeline: demand estimation "
            "followed by LCOE comparison for grid, mini-grid, and SHS."
        )
    )
    parser.add_argument(
        "--input",
        type=str,
        default="Benin_settlement_properties.geojson",
        help="Path to the settlements GeoJSON (default: Benin_settlement_properties.geojson).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default="outputs",
        help="Directory to write GeoJSON outputs (default: outputs).",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    gdf = gpd.read_file(input_path)

    # 1. Demand estimation
    gdf = run_demand_model(gdf)

    # 2. LCOE and least-cost technology selection
    gdf = run_lcoe_model(gdf)

    # Persist full electrification plan
    final_path = output_dir / "final_electrification_plan.geojson"
    gdf.to_file(final_path, driver="GeoJSON")

    # Optionally also write a lighter demand-only view
    demand_cols = [
        col
        for col in [
            "settlement_id",
            "population",
            "households",
            "tier",
            "dem_res",
            "dem_comm",
            "dem_agri",
            "dem_pub",
            "projected_demand",
            "projected_peak",
        ]
        if col in gdf.columns
    ]
    demand_gdf = gdf[demand_cols].copy()
    demand_path = output_dir / "demand_output.geojson"
    demand_gdf.to_file(demand_path, driver="GeoJSON")


if __name__ == "__main__":
    main()


