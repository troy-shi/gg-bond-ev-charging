"""Build the processed tables used by every view (Milestone 2).

Inputs: data/raw/ (see scripts/00_download.sh)
Outputs: data/processed/*.csv, snapshot_metadata.json, qa_report.json

Run: .venv/bin/python scripts/01_build_tables.py
"""
import json
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "processed"
OUT.mkdir(parents=True, exist_ok=True)

TERRITORY_FIPS = ["60", "66", "69", "72", "78"]
LEVELS = {"l1_ports": "EV Level1 EVSE Num", "l2_ports": "EV Level2 EVSE Num", "dcfc_ports": "EV DC Fast Count"}
FIRST_YEAR = 2015
NEAREST_MAX_M = 5_000  # fallback for coastal/edge points just outside a polygon
qa = {}

# ---------------------------------------------------------------- stations
raw = pd.read_csv(RAW / "afdc_elec_public_available.csv", low_memory=False)
qa["afdc_rows_downloaded"] = len(raw)
snapshot_date = pd.to_datetime(raw["Updated At"], utc=True).max().date().isoformat()

st = raw[
    (raw["Fuel Type Code"] == "ELEC")
    & (raw["Access Code"] == "public")
    & (raw["Status Code"] == "E")
    & (raw["Country"] == "US")
].copy()
qa["after_filters"] = len(st)
st = st.drop_duplicates(subset="ID")
qa["after_dedup_by_id"] = len(st)

counties = gpd.read_file(f"zip://{RAW / 'cb_2024_us_county_500k.zip'}")
counties = counties[~counties.STATEFP.isin(TERRITORY_FIPS)]
in_scope_states = set(counties.STUSPS)
qa["dropped_outside_50_states_dc"] = int((~st["State"].isin(in_scope_states)).sum())
st = st[st["State"].isin(in_scope_states)]

bad_xy = st["Latitude"].isna() | st["Longitude"].isna() | ~st["Latitude"].between(17, 72) | ~st["Longitude"].between(-180, -60)
qa["invalid_coordinates"] = int(bad_xy.sum())
st = st[~bad_xy]

# AFDC writes a level with no ports as a blank, never as 0 (verified: no explicit zeros in the file).
# Blank at one level is therefore 0 when the station reports ports at another level;
# a station with all three blank has unknown supply and is flagged incomplete.
for new, col in LEVELS.items():
    st[new] = pd.to_numeric(st[col], errors="coerce")
all_blank = st[list(LEVELS)].isna().all(axis=1)
qa["stations_all_port_fields_blank"] = int(all_blank.sum())
qa["negative_port_values"] = int((st[list(LEVELS)] < 0).sum().sum())
st.loc[~all_blank, list(LEVELS)] = st.loc[~all_blank, list(LEVELS)].fillna(0)
st["ports_complete"] = ~all_blank
st["total_ports"] = st[list(LEVELS)].sum(axis=1, min_count=3)

st["open_date"] = pd.to_datetime(st["Open Date"], errors="coerce")
st["open_year"] = st["open_date"].dt.year.astype("Int64")
st["network"] = st["EV Network"].fillna("Unknown network")
st["connectors"] = st["EV Connector Types"].fillna("")

# --------------------------------------------------------- spatial join
pts = gpd.GeoDataFrame(st, geometry=gpd.points_from_xy(st["Longitude"], st["Latitude"]), crs="EPSG:4326")
cty = counties[["GEOID", "STUSPS", "geometry"]].to_crs(pts.crs)
joined = gpd.sjoin(pts, cty, how="left", predicate="within").drop(columns="index_right")
joined = joined[~joined.index.duplicated(keep="first")]
joined["county_match"] = np.where(joined["GEOID"].notna(), "within_polygon", None)

miss = joined["GEOID"].isna()
if miss.any():
    proj = "EPSG:5070"  # CONUS Albers; distances for AK/HI points are approximate but only used for a 5 km cutoff
    near = gpd.sjoin_nearest(
        joined.loc[miss, ["geometry"]].to_crs(proj), cty.to_crs(proj), how="left",
        max_distance=NEAREST_MAX_M, distance_col="dist_m",
    )
    near = near[~near.index.duplicated(keep="first")]
    ok = near["GEOID"].notna()
    joined.loc[near.index[ok], "GEOID"] = near.loc[ok, "GEOID"]
    joined.loc[near.index[ok], "STUSPS"] = near.loc[ok, "STUSPS"]
    joined.loc[near.index[ok], "county_match"] = "nearest_within_5km"
joined["county_match"] = joined["county_match"].fillna("unresolved")
qa["county_match"] = joined["county_match"].value_counts().to_dict()
qa["afdc_state_differs_from_county_state"] = int(
    (joined["GEOID"].notna() & (joined["State"] != joined["STUSPS"])).sum()
)

stations = pd.DataFrame(joined.drop(columns="geometry")).rename(
    columns={"ID": "station_id", "Station Name": "station_name", "State": "state", "Latitude": "lat",
             "Longitude": "lon", "GEOID": "county_fips"}
)
stations_out = stations[[
    "station_id", "station_name", "state", "county_fips", "county_match", "lat", "lon",
    "l1_ports", "l2_ports", "dcfc_ports", "total_ports", "ports_complete",
    "network", "connectors", "open_date", "open_year",
]]
stations_out.to_csv(OUT / "stations_clean.csv", index=False)

# ------------------------------------------------------------- context
def read_acs(table):
    df = pd.read_csv(RAW / f"acsdt5y2024-{table}.dat", sep="|", dtype=str)
    est, moe = df.columns[1], df.columns[2]
    df[est] = pd.to_numeric(df[est], errors="coerce")
    df[moe] = pd.to_numeric(df[moe], errors="coerce")
    # ACS annotation codes (e.g. -666666666 = not available) become null; -555555555 MOE = controlled (no error)
    df.loc[df[est] < 0, est] = np.nan
    df.loc[df[moe] == -555555555, moe] = 0
    df.loc[df[moe] < 0, moe] = np.nan
    return df.rename(columns={est: f"{table}_e", moe: f"{table}_m"})

acs = read_acs("b01003").merge(read_acs("b19013"), on="GEO_ID", how="outer")
acs = acs.rename(columns={"b01003_e": "population", "b01003_m": "population_moe",
                          "b19013_e": "median_hh_income", "b19013_m": "median_hh_income_moe"})
acs_county = acs[acs.GEO_ID.str.startswith("0500000US")].assign(county_fips=lambda d: d.GEO_ID.str[-5:])
acs_state = acs[acs.GEO_ID.str.startswith("0400000US")].assign(state_fips=lambda d: d.GEO_ID.str[-2:])

rucc = pd.read_csv(RAW / "rucc2023.csv", dtype={"FIPS": str}, encoding="latin-1")
rucc = rucc[rucc.Attribute == "RUCC_2023"][["FIPS", "Value"]].rename(columns={"FIPS": "county_fips", "Value": "rucc_2023"})
rucc["rucc_2023"] = pd.to_numeric(rucc["rucc_2023"], errors="coerce").astype("Int64")

# ------------------------------------------------------- county_summary
def summarize(g):
    return pd.Series({
        "stations": g["station_id"].nunique(),
        "stations_ports_incomplete": int((~g["ports_complete"]).sum()),
        "l1_ports": g["l1_ports"].sum(),
        "l2_ports": g["l2_ports"].sum(),
        "dcfc_ports": g["dcfc_ports"].sum(),
    })

by_county = stations[stations.county_fips.notna()].groupby("county_fips").apply(summarize).reset_index()

cs = counties[["GEOID", "NAMELSAD", "STUSPS", "STATE_NAME"]].rename(
    columns={"GEOID": "county_fips", "NAMELSAD": "county_name", "STUSPS": "state", "STATE_NAME": "state_name"})
cs = cs.merge(by_county, on="county_fips", how="left")
cs["stations"] = cs["stations"].fillna(0).astype(int)
cs["stations_ports_incomplete"] = cs["stations_ports_incomplete"].fillna(0).astype(int)
for c in LEVELS:
    cs[c] = cs[c].fillna(0)
cs["ports_complete"] = cs["stations_ports_incomplete"] == 0
cs["total_ports"] = cs[list(LEVELS)].sum(axis=1)
cs.loc[~cs.ports_complete, ["l1_ports", "l2_ports", "dcfc_ports", "total_ports"]] = np.nan
cs["supply_status"] = np.select(
    [cs.stations == 0, ~cs.ports_complete], ["no stations recorded in this snapshot", "port counts incomplete"],
    "complete")

cs = cs.merge(acs_county[["county_fips", "population", "population_moe", "median_hh_income", "median_hh_income_moe"]],
              on="county_fips", how="left").merge(rucc, on="county_fips", how="left")
cs["metro_status"] = np.where(cs.rucc_2023.isna(), pd.NA, np.where(cs.rucc_2023 <= 3, "Metro", "Nonmetro"))

valid_pop = cs.population > 0
cs["ports_per_100k"] = np.where(valid_pop, 1e5 * cs.total_ports / cs.population, np.nan)
cs["dcfc_per_100k"] = np.where(valid_pop, 1e5 * cs.dcfc_ports / cs.population, np.nan)
cs["stations_per_100k"] = np.where(valid_pop, 1e5 * cs.stations / cs.population, np.nan)
cs["dcfc_share"] = np.where(cs.total_ports > 0, cs.dcfc_ports / cs.total_ports, np.nan)
cs["small_population_flag"] = cs.population < 10_000

# Q2: rank both measures on one common eligible set (1 = most supply)
cs["q2_eligible"] = cs.ports_complete & valid_pop
e = cs.q2_eligible
cs.loc[e, "rank_total_ports"] = cs.loc[e, "total_ports"].rank(ascending=False, method="min")
cs.loc[e, "rank_ports_per_100k"] = cs.loc[e, "ports_per_100k"].rank(ascending=False, method="min")
cs["rank_change"] = cs["rank_total_ports"] - cs["rank_ports_per_100k"]  # >0: moves up when per-capita

# Q7: percentiles over a fixed national set, equal county weight; ties at the cutoff are included.
# ~25% of counties have zero ports and ~39% zero DC fast ports, so any rate percentile below those
# shares collapses to a cutoff of 0. Each default is the first multiple of 5 above its zero share (revised in M2).
Q7_DEFAULT = {"total": 0.30, "dcfc": 0.40, "income": 0.50}
cs["q7_eligible"] = cs.ports_complete & valid_pop & cs.median_hh_income.notna()
q7 = cs[cs.q7_eligible]


def q7_select(df, p_total, p_dcfc, p_income):
    t, d, i = (q7.ports_per_100k.quantile(p_total), q7.dcfc_per_100k.quantile(p_dcfc),
               q7.median_hh_income.quantile(p_income))
    return (df.ports_per_100k <= t) & (df.dcfc_per_100k <= d) & (df.median_hh_income <= i), (t, d, i)


default_mask, (t0, d0, i0) = q7_select(cs, *Q7_DEFAULT.values())
cut = {"total_rate_cutoff": t0, "dcfc_rate_cutoff": d0, "income_cutoff": i0}
for col, src in [("pctile_ports_per_100k", "ports_per_100k"), ("pctile_dcfc_per_100k", "dcfc_per_100k"),
                 ("pctile_income", "median_hh_income")]:
    cs.loc[cs.q7_eligible, col] = q7[src].rank(pct=True, method="max")
cs["q7_selected_default"] = np.where(
    ~cs.q7_eligible, "not evaluated", np.where(default_mask, "selected", "not selected"))

# Q7 sensitivity: how the selected set changes as each cutoff moves (others held at default)
sens = []
for knob, grid in [("total", [0.25, 0.30, 0.35, 0.40, 0.50, 0.60]), ("dcfc", [0.25, 0.40, 0.50, 0.60]),
                   ("income", [0.25, 0.50, 0.75])]:
    for p in grid:
        params = dict(Q7_DEFAULT, **{knob: p})
        m, (t, d, i) = q7_select(cs, *params.values())
        m = m & cs.q7_eligible
        sens.append({"varied_cutoff": knob, "total_pctile": params["total"], "dcfc_pctile": params["dcfc"],
                     "income_pctile": params["income"], "total_cutoff_per_100k": round(t, 1),
                     "dcfc_cutoff_per_100k": round(d, 1), "income_cutoff_usd": int(i),
                     "selected": int(m.sum()), "selected_with_no_stations": int((m & (cs.stations == 0)).sum()),
                     "selected_nonmetro": int((m & (cs.metro_status == "Nonmetro")).sum()),
                     "added_vs_default": int((m & ~default_mask).sum()),
                     "removed_vs_default": int((~m & default_mask & cs.q7_eligible).sum())})
pd.DataFrame(sens).to_csv(OUT / "q7_sensitivity.csv", index=False)

for c in ["l1_ports", "l2_ports", "dcfc_ports", "total_ports", "population", "population_moe",
          "median_hh_income", "median_hh_income_moe", "rank_total_ports", "rank_ports_per_100k", "rank_change"]:
    cs[c] = cs[c].astype("Int64")
for c in ["ports_per_100k", "dcfc_per_100k", "stations_per_100k", "pctile_ports_per_100k",
          "pctile_dcfc_per_100k", "pctile_income"]:
    cs[c] = cs[c].round(2)
cs["dcfc_share"] = cs["dcfc_share"].round(3)
cs = cs.sort_values("county_fips")
cs.to_csv(OUT / "county_summary.csv", index=False)

# --------------------------------------------------------- state_summary
ss = stations.groupby("state").apply(summarize).reset_index()
ss["ports_complete"] = ss.stations_ports_incomplete == 0
ss["total_ports"] = ss[list(LEVELS)].sum(axis=1)
state_lookup = counties[["STUSPS", "STATEFP", "STATE_NAME"]].drop_duplicates().rename(
    columns={"STUSPS": "state", "STATEFP": "state_fips", "STATE_NAME": "state_name"})
ss = state_lookup.merge(ss, on="state", how="left").merge(
    acs_state[["state_fips", "population", "median_hh_income"]], on="state_fips", how="left")
for lvl in ["l1", "l2", "dcfc"]:
    ss[f"{lvl}_share"] = (ss[f"{lvl}_ports"] / ss.total_ports).round(3)
ss["ports_per_station"] = (ss.total_ports / ss.stations).round(2)
ss["ports_per_100k"] = (1e5 * ss.total_ports / ss.population).round(1)
ss["dcfc_per_100k"] = (1e5 * ss.dcfc_ports / ss.population).round(1)
ss["stations_per_100k"] = (1e5 * ss.stations / ss.population).round(1)
for c in ["stations", "l1_ports", "l2_ports", "dcfc_ports", "total_ports", "population", "median_hh_income"]:
    ss[c] = ss[c].astype("Int64")
ss = ss.sort_values("total_ports", ascending=False)
ss.to_csv(OUT / "state_summary.csv", index=False)

# --------------------------------------------------- opening_year_summary
snap_year = int(snapshot_date[:4])
yr = stations["open_year"]
cat = np.where(yr.isna(), "missing or invalid date",
               np.where(yr < FIRST_YEAR, f"before {FIRST_YEAR}",
                        np.where(yr > snap_year, "missing or invalid date", yr.astype("string"))))
# A single calendar date shared by >= 500 stations looks like a bulk database load, not real openings.
BULK_MIN = 500
date_counts = stations["open_date"].value_counts()
bulk_dates = date_counts[date_counts >= BULK_MIN]
stations["on_bulk_date"] = stations["open_date"].isin(bulk_dates.index)
grp = pd.DataFrame({"opening_year_group": cat, "on_bulk_date": stations["on_bulk_date"].values})
oy = grp.groupby("opening_year_group").agg(stations=("on_bulk_date", "size"),
                                           stations_on_bulk_dates=("on_bulk_date", "sum")).reset_index()
oy["share_of_stations"] = (oy.stations / oy.stations.sum()).round(4)
order = [f"before {FIRST_YEAR}"] + [str(y) for y in range(FIRST_YEAR, snap_year + 1)] + ["missing or invalid date"]
oy = oy.set_index("opening_year_group").reindex(order).fillna(0).reset_index()
oy[["stations", "stations_on_bulk_dates"]] = oy[["stations", "stations_on_bulk_dates"]].astype(int)
qa["bulk_open_dates"] = {d.date().isoformat(): int(n) for d, n in bulk_dates.items()}
oy["is_partial_year"] = oy.opening_year_group == str(snap_year)
oy["note"] = np.where(oy.is_partial_year, f"partial year: through {snapshot_date}", "")
oy.to_csv(OUT / "opening_year_summary.csv", index=False)

# ---------------------------------------------- network_connector_summary
CONNECTOR_LABELS = {"J1772": "J1772", "J1772COMBO": "CCS1", "TESLA": "NACS (Tesla)", "CHADEMO": "CHAdeMO",
                    "NEMA1450": "NEMA 14-50", "NEMA520": "NEMA 5-20", "NEMA515": "NEMA 5-15", "J3271": "J3271 (MCS)"}
stations["connector_list"] = stations.connectors.str.split()
stations["connector_known"] = stations.connector_list.str.len() > 0
ncs = []
for scope, frame in [("US", stations)] + list(stations.groupby("state")):
    net_tot = frame.groupby("network").agg(network_stations=("station_id", "nunique"),
                                           stations_connector_known=("connector_known", "sum")).reset_index()
    ex = frame[frame.connector_known].explode("connector_list")
    cnt = ex.groupby(["network", "connector_list"]).station_id.nunique().rename("stations_listing_connector").reset_index()
    grid = net_tot.merge(pd.DataFrame({"connector_list": list(CONNECTOR_LABELS)}), how="cross").merge(
        cnt, on=["network", "connector_list"], how="left")
    grid["stations_listing_connector"] = grid.stations_listing_connector.fillna(0).astype(int)
    grid.insert(0, "state", scope)
    ncs.append(grid)
ncs = pd.concat(ncs, ignore_index=True).rename(columns={"connector_list": "connector_code"})
ncs["connector"] = ncs.connector_code.map(CONNECTOR_LABELS)
ncs["pct_of_known"] = np.where(ncs.stations_connector_known > 0,
                               (100 * ncs.stations_listing_connector / ncs.stations_connector_known).round(1), np.nan)
ncs["network_rank_in_state"] = ncs.groupby("state").network_stations.rank(ascending=False, method="dense").astype(int)
ncs = ncs.sort_values(["state", "network_rank_in_state", "connector_code"])
ncs = ncs[["state", "network", "network_rank_in_state", "network_stations", "stations_connector_known",
           "connector_code", "connector", "stations_listing_connector", "pct_of_known"]]
ncs.to_csv(OUT / "network_connector_summary.csv", index=False)

# ------------------------------------------------------------- metadata
qa.update({
    "stations_in_scope": len(stations),
    "counties_in_scope": len(cs),
    "counties_no_stations": int((cs.stations == 0).sum()),
    "counties_ports_incomplete": int((~cs.ports_complete).sum()),
    "counties_missing_population": int(cs.population.isna().sum()),
    "counties_missing_income": int(cs.median_hh_income.isna().sum()),
    "counties_missing_rucc": int(cs.rucc_2023.isna().sum()),
    "q2_eligible_counties": int(cs.q2_eligible.sum()),
    "q7_eligible_counties": int(cs.q7_eligible.sum()),
    "q7_default_percentiles": Q7_DEFAULT,
    "q7_default_cutoffs": {k: round(float(v), 2) for k, v in cut.items()},
    "q7_share_counties_zero_ports": round(float((q7.ports_per_100k == 0).mean()), 3),
    "q7_share_counties_zero_dcfc": round(float((q7.dcfc_per_100k == 0).mean()), 3),
    "q7_selected_default": int((cs.q7_selected_default == "selected").sum()),
    "open_date_missing_or_invalid": int(stations.open_year.isna().sum()),
    "stations_connector_unknown": int((~stations.connector_known).sum()),
})
(OUT / "qa_report.json").write_text(json.dumps(qa, indent=2, default=int))
(OUT / "snapshot_metadata.json").write_text(json.dumps({
    "afdc_snapshot_date": snapshot_date,
    "afdc_retrieved_at": (RAW / "RETRIEVED_AT.txt").read_text().strip() if (RAW / "RETRIEVED_AT.txt").exists() else None,
    "afdc_filters": "fuel_type=ELEC, status=E, access=public, country=US; 50 states + DC",
    "acs": "ACS 2020-2024 5-year, tables B01003 and B19013 (summary file)",
    "boundaries": "Census 2024 cartographic boundary files (county 500k for join)",
    "rucc": "USDA ERS 2023 Rural-Urban Continuum Codes",
}, indent=2))
print(json.dumps(qa, indent=2, default=int))
