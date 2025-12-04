import numpy as np
import pandas as pd

from .config import (
    TIER_KWH,
    TIER_LF,
    LOADS,
    TARGET_UPTAKE_2040,
    POP_GROWTH,
    WEALTH_GROWTH,
    PLANNING_HORIZON,
)


def estimate_agri_loads(row: pd.Series) -> float:
    """
    agronomic / productive loads based on geography and settlement size.

    the goal is to capture relative differences
    between rural areas (riverine vs non-riverine, cashew belt vs others),
    not to a fully calibrated agricultural model.
    """
    demand = 0.0
    pop = row.get("population", 0)
    is_urban = row.get("is_urban", False)

    # Grain mills – assumed universal in rural settlements above a minimum size
    if not is_urban and pop > 500:
        demand += max(1, int(pop / 1500)) * LOADS["mill"]

    # Irrigation pumps – only in riparian areas with enough agricultural activity
    if row.get("dist_lake_river_km", 99) < 3.0 and pop > 300:
        demand += max(1, int(pop / 800)) * LOADS["irrigation"]

    # Cashew processing – north/central cashew belt, again only in rural areas
    lat = row.geometry.centroid.y if hasattr(row, "geometry") else 0
    if lat > 8.0 and not is_urban and pop > 400:
        demand += max(1, int(pop / 2000)) * LOADS["dryer"]

    return float(demand)


def run_demand_model(gdf):
    """
    Estimate settlement-level electricity demand and design peak to 2040.

    Assumes a 15-year horizon, MT-Framework-style tiers (1–3 in practice here),
    and simple rules for commercial, agricultural and public loads. The emphasis
    is on transparent relative differences across settlements, not exact kWh.
    """
    # 1. Demographics & basic classification (urban /rural)
    gdf["is_urban"] = (gdf["population"] > 5000) | (gdf.get("num_buildings", 0) > 500)
    gdf["hh_size"] = np.where(gdf["is_urban"], 4.3, 5.2)
    gdf["households"] = (
        np.ceil(gdf["population"] / gdf["hh_size"]).clip(lower=1).astype(int)
    )

    # 2. Tier assignment: RWI as a wealth proxy, with a light nightlight correction
    rwi = gdf.get("mean_rwi", 0)
    gdf["tier"] = np.select([rwi < -0.3, rwi < 0.4], [1, 2], default=3)

    if "has_nightlight" in gdf.columns:
        gdf["tier"] = np.where(
            (gdf["has_nightlight"] > 0) & (gdf["tier"] < 2), 2, gdf["tier"]
        )

    # Logistics constraint: very remote areas are capped at Tier 3
    if "dist_main_road_km" in gdf.columns:
        mask_remote = gdf["dist_main_road_km"] > 20
        gdf.loc[mask_remote & (gdf["tier"] > 3), "tier"] = 3

    gdf["kwh_hh"] = gdf["tier"].map(TIER_KWH)
    gdf["lf"] = gdf["tier"].map(TIER_LF)

    # 3. Commercial
    # More SME activity near hubs, less in remote areas, scaled by buildings/HH.
    dist_hub = gdf.get(
        "dist_nearest_hub_km", pd.Series(30, index=gdf.index, dtype="float64")
    ).fillna(30)
    gravity = np.clip(1 + (20.0 / (dist_hub + 1)), 1, 2.5)

    base_sme = np.where(gdf["is_urban"], 50, 100)
    sme = (gdf.get("num_buildings", gdf["households"]) / base_sme) * gravity
    gdf["dem_comm"] = np.ceil(sme) * LOADS["sme"]

    # Fish practice (cold chain near lakes/rivers)
    if "dist_lake_river_km" in gdf.columns:
        mask_fish = (gdf["dist_lake_river_km"] < 3.0) & (gdf["population"] > 200)
        gdf.loc[mask_fish, "dem_comm"] += (
            np.ceil(gdf.loc[mask_fish, "households"] / 100) * LOADS["freezer"]
        )

    # 4. Aggregation & projection to 2040
    # Here we focus on long-run differences across settlements rather than exact
    # year-by-year trajectories (missing time series data).
    uptake = np.where(gdf["is_urban"], 0.95, TARGET_UPTAKE_2040)
    gdf["dem_res"] = gdf["households"] * gdf["kwh_hh"] * uptake
    gdf["dem_agri"] = gdf.apply(estimate_agri_loads, axis=1)
    gdf["dem_pub"] = (
        gdf.get("num_health_facilities", 0).fillna(0) * LOADS["health"]
        + gdf.get("num_education_facilities", 0).fillna(0) * LOADS["education"]
    )

    total_yr0 = gdf["dem_res"] + gdf["dem_comm"] + gdf["dem_agri"] + gdf["dem_pub"]
    growth = (1 + ((1 + POP_GROWTH) * (1 + WEALTH_GROWTH) - 1)) ** PLANNING_HORIZON
    gdf["projected_demand"] = total_yr0 * growth

    # Design peak for infrastructure sizing (assuming 100% uptake for capacity)
    design_res = gdf["households"] * gdf["kwh_hh"]
    design_total = (design_res + gdf["dem_comm"] + gdf["dem_agri"] + gdf["dem_pub"]) * growth
    gdf["projected_peak"] = (design_total / 8760) / gdf["lf"]

    return gdf


