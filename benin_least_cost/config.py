"""
Techno-economic parameters for the Benin least-cost electrification analysis.

Values are deliberately simple and rounded, 
not a fully calibrated national planning model.

Sources (approximate): World Bank WDI, ESMAP/OnSSET defaults, IRENA 2023,
Benin DHS,  SBEE.
"""

# --- PLANNING ---
PLANNING_HORIZON = 15       # 2025–2040 horizon
POP_GROWTH = 0.027          # Benin national average (WDI)
WEALTH_GROWTH = 0.015       # per-capita consumption growth (assumed)
DISCOUNT_RATE = 0.08        # WB standard social discount rate for West Africa

# --- DEMAND (ESMAP Multi-Tier Framework) ---
TIER_KWH = {1: 35, 2: 220, 3: 850, 4: 2200, 5: 3500}
# Load Factors (Lower tiers = spikier evening demand)
TIER_LF = {1: 0.18, 2: 0.20, 3: 0.25, 4: 0.30, 5: 0.35}

# ANCHOR LOADS [kWh/year] – small rural facilities, order-of-magnitude only
LOADS = {
    "health": 4000,
    "education": 1500,
    "sme": 600,
    "freezer": 2500,      # Cold chain (fishing)
    "irrigation": 3500,   # Ag: pump
    "mill": 4500,         # Ag: grain processing
    "dryer": 6000,        # Ag: cashew processing
}

# UPTAKE RATES (Infrastructure sized for 100%,
TARGET_UPTAKE_2040 = 0.85

# --- GRID COSTS
MV_COST_KM = 14000         # 33 kV line – rural average, USD/km
LV_COST_KM = 5500          # LV distribution network, USD/km
SUBSTATION_COST = 500000   # HV (161 kV) step-down, USD
TRANSFORMER_COST = 8000
CONN_GRID = 150
GRID_LOSS = 0.18
GRID_PRICE = 0.10          # USD/kWh wholesale

# --- MINI-GRID COSTS (IRENA 2023 ballpark for West Africa) ---
PV_COST = 700              # USD/kW
BATT_COST = 300            # USD/kWh (LFP, heat-derated)
INV_COST = 180             # USD/kW
CONN_MG = 100
CF_SOLAR = 0.18            # Benin Global Solar Atlas
BATT_LIFE = 7              # Effective life, high ambient temperatures

# --- SHS COSTS ---
SHS_COST = {1: 80, 2: 250, 3: 600}
SHS_CAP = {1: 35, 2: 150, 3: 350}  # Max deliverable kWh over the planning horizon
MAX_TIER_SHS = 3


