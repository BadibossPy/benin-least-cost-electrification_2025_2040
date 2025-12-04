import numpy as np

from .config import (
    DISCOUNT_RATE,
    SUBSTATION_COST,
    MV_COST_KM,
    LV_COST_KM,
    TRANSFORMER_COST,
    CONN_GRID,
    GRID_LOSS,
    GRID_PRICE,
    PV_COST,
    BATT_COST,
    INV_COST,
    CONN_MG,
    CF_SOLAR,
    SHS_COST,
    SHS_CAP,
    MAX_TIER_SHS,
)


def crf(r: float, n: int) -> float:
    """Capital Recovery Factor, applied to vectorised capex arrays."""
    if r == 0:
        return 1.0 / n
    return (r * (1 + r) ** n) / ((1 + r) ** n - 1)


def run_lcoe_model(gdf, lines_gdf=None):
    """
    Calculate Levelized Cost of Electricity (LCOE) for Grid, Mini-Grid, SHS.

    - Grid: MV + LV + transformers + energy purchase, with a +price for HV step-down.
    - Mini-grid: PV-battery system with heat-adjusted replacements and local LV.
    - SHS: constrained to low tiers and no productive loads.
    """

    # --- 1. VOLTAGE & DISTANCE LOGIC ---
    # We don't have detailed voltage by line, so we fold the cost of a substation into
    # an "equivalent MV distance" penalty when using transmission lines.
    d_sub = gdf.get("dist_to_substations", 999).fillna(999)
    d_lines = gdf.get("distance_to_existing_transmission_lines", 999).fillna(999)

    # Penalty distance equivalent to the cost of one substation (~35 km)
    penalty_km = SUBSTATION_COST / MV_COST_KM

    # Either connect to a substation, or to a line + penalty if that is cheaper.
    dist_grid = np.minimum(d_sub, d_lines + penalty_km)

    # --- 2. GRID LCOE ---
    # Peak load sized with a diversity factor: not all households peak at once.
    peak = gdf["projected_peak"] * 0.6
    hh = gdf["households"]

    # 1.3x MV cost in areas without road access (dispersed settlements).
    terrain_factor = np.where(gdf.get("main_road_access", 1) == 0, 1.3, 1.0)

    capex_grid = (
        dist_grid * MV_COST_KM * terrain_factor
        + hh * 0.05 * LV_COST_KM  # ~50 m of LV per connection
        + np.ceil(peak / 45) * TRANSFORMER_COST
        + hh * CONN_GRID
    )

    # OPEX = O&M (2%) + energy purchase cost (generation/import)
    ann_grid_cap = capex_grid * crf(DISCOUNT_RATE, 40)
    ann_grid_om = capex_grid * 0.02
    ann_grid_energy = (gdf["projected_demand"] / (1 - GRID_LOSS)) * GRID_PRICE

    gdf["lcoe_grid"] = (ann_grid_cap + ann_grid_om + ann_grid_energy) / gdf["projected_demand"]

    # --- 3. MINI-GRID LCOE ---
    # Simple PV-battery system: 1.2x PV oversize, 1-day autonomy.
    daily_load = gdf["projected_demand"] / 365.0
    pv_kw = (daily_load / (CF_SOLAR * 8760 * 0.85)) * 1.2
    batt_kwh = daily_load / 0.8

    # Battery replacements in year 7 and 14, discounted back to t=0.
    batt_rep_cost = batt_kwh * BATT_COST
    batt_pv = (batt_rep_cost / (1 + DISCOUNT_RATE) ** 7) + (
        batt_rep_cost / (1 + DISCOUNT_RATE) ** 14
    )

    # Approximate LV distribution length as 100 m per household, priced at LV_COST_KM.
    lv_length_km = hh * 0.1  # km of LV; 0.1 km = 100 m per connection
    lv_cost_mg = lv_length_km * LV_COST_KM

    capex_mg = (
        pv_kw * PV_COST
        + batt_kwh * BATT_COST
        + batt_pv
        + peak * 1.25 * INV_COST
        + hh * CONN_MG
        + lv_cost_mg
    )

    ann_mg_cap = capex_mg * crf(DISCOUNT_RATE, 20)
    ann_mg_om = capex_mg * 0.03

    gdf["lcoe_mg"] = (ann_mg_cap + ann_mg_om) / gdf["projected_demand"]

    # --- 4. SHS LCOE ---
    # Select kit based on tier, with a hard cap on deliverable energy.
    tier = gdf["tier"]
    capex_shs = tier.map(SHS_COST) * hh

    cap_limit = tier.map(SHS_CAP)
    energy_delivered = np.minimum(gdf["projected_demand"] / hh, cap_limit) * hh

    ann_shs_cap = capex_shs * crf(DISCOUNT_RATE, 5)
    ann_shs_om = capex_shs * 0.05

    gdf["lcoe_shs"] = (ann_shs_cap + ann_shs_om) / energy_delivered

    #no SHS for productive/public loads, or above MAX_TIER_SHS.
    has_productive = (gdf["dem_comm"] > 0) | (gdf["dem_agri"] > 0) | (gdf["dem_pub"] > 0)
    mask_invalid = (tier > MAX_TIER_SHS) | has_productive
    gdf.loc[mask_invalid, "lcoe_shs"] = 999.9

    # --- 5. OPTIMISATION ---
    # least-LCOE choice by settlement, ignoring network topology.
    cols = ["lcoe_grid", "lcoe_mg", "lcoe_shs"]
    winner_col = gdf[cols].idxmin(axis=1)

    tech_labels = {
        "lcoe_grid": "Grid",
        "lcoe_mg": "MiniGrid",
        "lcoe_shs": "SHS",
    }

    gdf["min_lcoe"] = gdf[cols].min(axis=1)
    gdf["optimal_tech"] = winner_col.map(tech_labels)

    # Assign investment cost based on the winning technology.
    gdf["investment"] = np.select(
        [gdf["optimal_tech"] == "Grid", gdf["optimal_tech"] == "MiniGrid"],
        [capex_grid, capex_mg],
        default=capex_shs,
    )

    return gdf


