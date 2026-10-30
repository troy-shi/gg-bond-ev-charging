"""Write the representative sample tables and summary figures quoted in the Milestone 2 report.

Run after 01_build_tables.py:  .venv/bin/python scripts/02_make_samples.py
Output: docs/samples/*.md (markdown tables) and docs/samples/key_numbers.json
"""
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "data" / "processed"
OUT = ROOT / "docs" / "samples"
OUT.mkdir(parents=True, exist_ok=True)

cs = pd.read_csv(P / "county_summary.csv", dtype={"county_fips": str})
ss = pd.read_csv(P / "state_summary.csv", dtype={"state_fips": str})
oy = pd.read_csv(P / "opening_year_summary.csv")
ncs = pd.read_csv(P / "network_connector_summary.csv")
sens = pd.read_csv(P / "q7_sensitivity.csv")
st = pd.read_csv(P / "stations_clean.csv", dtype={"county_fips": str}, low_memory=False)
key = {}


def write(name, df):
    (OUT / f"{name}.md").write_text(df.fillna({c: "" for c in df.columns if df[c].dtype == object}).to_markdown(index=False) + f"\n\n_{len(df)} sample rows shown._\n")


def pick(df, fips):
    return df.set_index("county_fips").loc[fips].reset_index()


# Stations table (input to every view)
examples = [0, 1000, 40000, 60000, st.dcfc_ports.idxmax(), st.l2_ports.idxmax(),
            st[~st.ports_complete].index[0], st[st.county_match != "within_polygon"].index[0]]
write("stations_clean", st.loc[sorted(set(examples))][
    ["station_id", "station_name", "state", "county_fips", "county_match", "l1_ports", "l2_ports", "dcfc_ports",
     "total_ports", "network", "connectors", "open_date"]])

# Q1 / Q2: ordinary, largest, tiny-high-rate, zero, incomplete, missing-income
e = cs[cs.q2_eligible]
high_rate_small = e[e.population < 10_000].sort_values("ports_per_100k", ascending=False).iloc[0].county_fips
big_mover = e[e.population < 50_000].sort_values("rank_change", ascending=False).iloc[0].county_fips
q2_rows = ["06037", "17031", "36061", high_rate_small, big_mover, "39049", "47157",
           e[e.stations == 1].iloc[0].county_fips,
           cs[cs.stations == 0].iloc[0].county_fips, cs[cs.supply_status == "port counts incomplete"].iloc[0].county_fips]
q12 = pick(cs, q2_rows)[["county_fips", "county_name", "state", "stations", "l1_ports", "l2_ports", "dcfc_ports",
                         "total_ports", "population", "ports_per_100k", "rank_total_ports", "rank_ports_per_100k",
                         "supply_status"]]
write("q1_q2_county_summary", q12)

write("q1_state_counts", ss.head(5)._append(ss.tail(3))[
    ["state", "state_name", "stations", "total_ports", "ports_per_station"]])

# Q3
write("q3_opening_year_summary", oy)

# Q4
q4 = ss.sort_values("dcfc_per_100k")[["state", "total_ports", "l1_ports", "l2_ports", "dcfc_ports", "l1_share",
                                      "l2_share", "dcfc_share", "population", "dcfc_per_100k"]]
write("q4_state_level_mix", pd.concat([q4.head(4), q4[q4.state.isin(["FL", "TX", "NY"])], q4.tail(3)]))

# Q5: one state as the dropdown example, long format + pivot preview
ny = ncs[(ncs.state == "NY") & (ncs.network_rank_in_state <= 4) & ncs.connector_code.isin(["J1772", "J1772COMBO", "CHADEMO", "TESLA"])]
write("q5_network_connector_long_NY", ny.head(12))
piv = ny.pivot_table(index=["network", "network_stations"], columns="connector", values="pct_of_known").reset_index()
piv = piv.sort_values("network_stations", ascending=False)
write("q5_network_connector_pivot_NY", piv)

# Q6
q6 = cs[cs.q7_eligible]
q6_rows = q6.sort_values("median_hh_income").iloc[[0, 400, 1500, 2700, -1]].county_fips.tolist() + ["06037", "08014", "54047"]
write("q6_income_rurality", pick(cs, q6_rows)[["county_fips", "county_name", "state", "median_hh_income",
                                               "median_hh_income_moe", "population", "ports_per_100k", "dcfc_per_100k",
                                               "rucc_2023", "metro_status"]])
corr = {}
for m in ["Metro", "Nonmetro"]:
    g = q6[q6.metro_status == m]
    corr[m] = {"n": len(g),
               "spearman_income_total_rate": round(g.median_hh_income.corr(g.ports_per_100k, method="spearman"), 2),
               "spearman_income_dcfc_rate": round(g.median_hh_income.corr(g.dcfc_per_100k, method="spearman"), 2),
               "median_ports_per_100k": round(g.ports_per_100k.median(), 1),
               "share_zero_ports": round((g.ports_per_100k == 0).mean(), 3)}
key["q6_by_metro"] = corr

# Q7
sel = cs[cs.q7_selected_default == "selected"]
q7 = pd.concat([sel[sel.stations > 0].sort_values("population", ascending=False).head(4),
                sel[sel.stations == 0].sort_values("population", ascending=False).head(3),
                cs[cs.q7_selected_default == "not selected"].head(2),
                cs[cs.q7_selected_default == "not evaluated"]])
write("q7_screen", q7[["county_fips", "county_name", "state", "stations", "total_ports", "dcfc_ports", "population",
                       "ports_per_100k", "dcfc_per_100k", "median_hh_income", "metro_status", "q7_selected_default"]])
write("q7_sensitivity", sens)

# Headline numbers quoted in the report
key.update({
    "stations": int(len(st)), "total_ports": int(st.total_ports.sum()),
    "l1_ports": int(st.l1_ports.sum()), "l2_ports": int(st.l2_ports.sum()), "dcfc_ports": int(st.dcfc_ports.sum()),
    "top5_states_share_of_ports": round(ss.head(5).total_ports.sum() / ss.total_ports.sum(), 3),
    "top5_states": ss.head(5).state.tolist(),
    "ca_share_of_ports": round(float(ss.loc[ss.state == "CA", "total_ports"].iloc[0] / ss.total_ports.sum()), 3),
    "networks_us": int(ncs[ncs.state == "US"].network.nunique()),
    "chargepoint_share_of_stations": round(float((st.network == "ChargePoint Network").mean()), 3),
    "counties_zero_dcfc": int((cs.dcfc_ports == 0).sum()),
    "high_rate_small_county": cs.set_index("county_fips").loc[high_rate_small, ["county_name", "state", "population", "stations", "total_ports", "ports_per_100k", "rank_total_ports", "rank_ports_per_100k"]].to_dict(),
    "big_mover": cs.set_index("county_fips").loc[big_mover, ["county_name", "state", "population", "rank_total_ports", "rank_ports_per_100k"]].to_dict(),
})
(OUT / "key_numbers.json").write_text(json.dumps(key, indent=2, default=str))
print(json.dumps(key, indent=2, default=str))
