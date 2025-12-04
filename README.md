Inputs

The main input is a settlement-level GeoJSON for Benin:

- settlement geometry
- population
- number of buildings
- distance to existing transmission / substations
- distance to main roads
- distance to lakes/rivers
- simple service indicators (health facilities, schools)
- simple economic proxies (nightlights, relative wealth index)

These fields are used directly in the demand and cost logic.


Demand model (high level)

- Households are derived from population and an average household size:
  slightly smaller in urban-like areas, larger in rural areas.
- A simple rule classifies settlements as “urban-ish” vs “rural” based on population and building count.
- Service level tiers (Tier 1–3) are assigned from a relative wealth index (RWI), with a small upward correction when nightlights are present.
- Each tier has an annual kWh/household and a load factor, loosely based on the ESMAP multi-tier framework and OnSSET-style defaults.
- Productive and institutional loads are added on top:
  small rural health posts, schools, SME loads, irrigation pumps, grain mills, cashew dryers.
  These are rule-of-thumb kWh values meant to capture order-of-magnitude differences.
- Settlements near lakes/rivers with enough population get extra cold chain demand (freezers) to reflect fishing/ice use.
- Demand is projected about 15 years ahead (2025–2040) using a combined population growth rate and per-capita consumption growth.
- For infrastructure sizing, a design peak is computed by applying a load factor to the projected annual demand.


Technology and cost model (high level)

- Grid option:
  MV line cost per km, LV cost per km, transformer cost per kVA, and connection cost per household.
  A “distance penalty” converts substation cost into an equivalent MV distance when connecting via transmission lines.
  Annualized costs use a 40-year lifetime and an 8% discount rate.
  Energy purchase cost is added using a wholesale grid tariff and a simple loss factor.

- Mini-grid option:
  PV-battery system sized from projected demand:
  1-day battery autonomy at 80% usable depth, and 1.2x PV oversizing, with a fixed solar capacity factor.
  Battery replacements are assumed in year 7 and 14 and discounted back to present.
  A simple LV network is included by assuming about 100 m of LV line per connected household, priced at the same LV cost per km as the grid.
  Costs are annualized over a 20-year project life with 3% O&M.

- SHS option:
  A small set of SHS “kits” (Tier 1–3) with fixed upfront costs and a maximum deliverable kWh per household over the horizon.
  If projected demand exceeds the kit capacity, delivered energy is capped and the effective LCOE rises.
  SHS capex is annualized over 5 years with 5% O&M.
  SHS is only allowed in low-tier, non-productive settlements (no commercial/agricultural/public loads and tier <= 3).


Least-cost decision

- For each settlement, the model computes an LCOE for:
  grid extension, mini-grid, and SHS.
- The least LCOE option is selected as “optimal_tech” (Grid, MiniGrid, or SHS).
- The total investment for the chosen option is also reported.


Key assumptions and simplifications

- Demand is based on simple rules and broad averages (tiers, anchor loads, growth rates).
  The focus is on relative ranking of settlements, not precise kWh.
- Productive loads (mills, irrigation, cashew, cold chain) are added using geographic heuristics:
  near rivers, in the cashew belt, above small population thresholds.
- Time structure is reduced to a single average load factor per tier.
  There is no explicit hourly or seasonal profile.
- Grid and mini-grid technologies are represented as single “typical” designs:
  one MV cost, one LV cost, one battery technology, one solar capacity factor.
- Each settlement is treated independently in the least-cost comparison.
  There is no explicit optimization of network topology or clustering beyond distance penalties.
- SHS is deliberately constrained to small, relatively simple settlements without productive loads.


Limitations and possible extensions

- Calibration: parameters could be calibrated against SBEE sales, real project costs, and national plans.
- Scenarios: it would be straightforward to rerun the model with high/low cost or demand scenarios.
- Technology set: diesel or hybrid mini-grids, and more detailed grid densification options, are not included here.
- Topology: a full national planning exercise would model the expansion of MV lines and substations explicitlyl.



## References

- ESMAP Multi-Tier Framework for Household Electricity Supply
- World Bank electrification planning guidelines
- IRENA renewable energy cost data
- Benin national electrification strategy

## Author

[Badre Alloul] - Least-Cost Electrification Analysis for Benin
