# Public EV Charging Infrastructure in the United States

CS-GY 6313 Information Visualization, Fall 2026 — **Team 9: GG BOND**
Zihang Yu (zy3493) · Zhangzhuoyue Shi (zs3699) · Yaxi Wang (yw10340)

A D3 visual narrative on how public EV charging supply is distributed across the 50 states and DC: where it is, how it compares with population, when today's stations were recorded as opening, which charging levels, networks and connectors exist, how supply relates to income and rurality, and which counties may merit a closer look.

- **Milestone 2 report:** [`docs/M2_report.md`](docs/M2_report.md)
- **Sketches:** [`sketches/`](sketches/)
- **Team tasks and who owns which question:** [`docs/TEAM_TASKS.md`](docs/TEAM_TASKS.md)
- **Observable notebooks:** _none yet_ (if added, list each URL here with its purpose; notebooks will be public or unlisted)

## Repository layout

```
scripts/00_download.sh        downloads every raw dataset into data/raw/
scripts/01_build_tables.py    cleaning, county spatial join, all processed tables, QA report
scripts/02_make_samples.py    sample tables + headline numbers used in the report (docs/samples/)
data/raw/                     raw downloads (git-ignored; recreate with 00_download.sh)
data/processed/               processed CSVs, qa_report.json, snapshot_metadata.json
docs/                         milestone reports and generated sample tables
sketches/                     hand-drawn sketches (photos/scans)
```

## How to run

Requires Python 3.9+ and `curl`.

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
bash scripts/00_download.sh                 # ~45 MB; optional: export AFDC_API_KEY=<your key>
.venv/bin/python scripts/01_build_tables.py # writes data/processed/
.venv/bin/python scripts/02_make_samples.py # writes docs/samples/
```

Re-downloading AFDC creates a **new** snapshot, so the numbers will differ from the report. The report uses the snapshot dated **2026-10-30**, and the processed tables from that snapshot are committed in `data/processed/`.

## Data access

| Dataset | Used for | Access |
|---|---|---|
| AFDC Alternative Fueling Station Locator (U.S. DOE) | Station locations, port counts by level, network, connectors, open date | API (CSV): `https://developer.nlr.gov/api/alt-fuel-stations/v1.csv?api_key=DEMO_KEY&fuel_type=ELEC&status=E&access=public&country=US&limit=all` · [Docs](https://developer.nlr.gov/docs/transportation/alt-fuel-stations-v1/all/) · [Field definitions](https://afdc.energy.gov/data_download/alt_fuel_stations_format) · [Web download](https://afdc.energy.gov/data_download) |
| ACS 2020–2024 5-year, table B01003 (total population) | County/state population + MOE | [Summary file](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b01003.dat) · [Table info](https://api.census.gov/data/2024/acs/acs5/groups/B01003.html) |
| ACS 2020–2024 5-year, table B19013 (median household income) | County income + MOE | [Summary file](https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-b19013.dat) · [Table info](https://api.census.gov/data/2024/acs/acs5/groups/B19013.html) |
| Census 2024 cartographic boundary files | County polygons (1:500k join, 1:20m maps), state polygons | [County 500k](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_500k.zip) · [County 20m](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_county_20m.zip) · [State 20m](https://www2.census.gov/geo/tiger/GENZ2024/shp/cb_2024_us_state_20m.zip) · [Overview](https://www.census.gov/geographies/mapping-files/2024/geo/carto-boundary-file.html) |
| USDA ERS Rural-Urban Continuum Codes 2023 | Metro (1–3) / nonmetro (4–9) | [CSV](https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv) · [Documentation](https://www.ers.usda.gov/data-products/rural-urban-continuum-codes) |

Filters: `fuel_type_code = ELEC`, `access_code = public`, `status_code = E` (available), 50 states + DC. The Census Data API now requires a key, so we read the identical estimates from the keyless ACS summary files.

## Processed tables

| File | One row per | Used by |
|---|---|---|
| `stations_clean.csv` | AFDC station | all |
| `county_summary.csv` | county (3,144) | Q1, Q2, Q6, Q7 |
| `state_summary.csv` | state + DC (51) | Q1, Q4 |
| `opening_year_summary.csv` | opening-year group | Q3 |
| `network_connector_summary.csv` | state × network × connector (+ `US`) | Q5 |
| `q7_sensitivity.csv` | Q7 cutoff setting | Q7 |

Column definitions and data-handling decisions are in §1 of the [M2 report](docs/M2_report.md).

## AI-use statement

> _Draft. The team must edit this to match exactly how AI was used._

- **Tool:** Claude (Anthropic), via Claude Code.
- **Used for:** writing and debugging `scripts/00_download.sh`, `scripts/01_build_tables.py`, and `scripts/02_make_samples.py`; drafting the structure and text of `docs/M2_report.md` and this README; checking our revised plan against the Milestone 1 feedback.
- **Not used for:** the visualization sketches in `sketches/`, which were drawn by the team.
- **Verification:** the team reviewed the code, re-ran the pipeline, and checked the QA counts and sample rows against the raw files. We are responsible for all numbers and design decisions.
