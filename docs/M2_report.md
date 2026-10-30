# Public EV Charging Infrastructure in the United States
## Milestone 2: Data Analysis & Sketches

CS-GY 6313 Information Visualization | Fall 2026 | **Team 9: GG BOND**

| Name | NetID |
|---|---|
| Zihang Yu | zy3493 |
| Zhangzhuoyue Shi | zs3699 |
| Yaxi Wang | yw10340 |

**GitHub repository:** `<PASTE REPO URL>` (private; shared with `ctsilva` and `kimryan0416`)
**Data access, run instructions, and AI-use statement:** see the repository `README.md`.
**AI use in this report:** sections marked **[AI-a]** used AI assistance as described in [§8](#8-ai-use-statement). All sketches are hand-drawn by the team.

---

## 0. What changed since Milestone 1

The table below lists every change to the questions, designs, and data handling since the V1 proposal (Oct 19). It covers the three points in the instructor feedback and the issues we found once we processed the real data.

| # | Area | V1 proposal | Milestone 2 decision | Why |
|---|---|---|---|---|
| C1 | **Q3 question** | "How has public charging grown since 2015, and where has DC fast capacity expanded fastest?" Cumulative line chart by level + year-slider map. | **"Among stations present in our snapshot, how many have recorded opening dates in each year since 2015?"** Annual bar chart of station counts, with a permanent on-chart note. | Feedback point 1. The snapshot excludes closed stations, and `open_date` is approximate. We also found that **8.0% of all stations share one opening date (2021-01-27)** and 2.3% share another (2020-06-12). These look like bulk database loads (§1.3). Today's port counts cannot be assigned to past years. |
| C2 | **Q7 framing** | "Potential supply gaps." | **"Counties for closer review."** The rule, actual cutoff values, sensitivity counts, and a permanent caption sit next to the map and table. | Feedback point 2. A screen identifies places to look at; it does not prove a shortage. |
| C3 | **Q7 default cutoffs** | Total and DC fast rates at or below the 25th percentile; sliders from 10th to 50th. | Defaults are **30th percentile (total rate) and 40th percentile (DC fast rate)**. Rate sliders run from **25th to 60th**. Income is unchanged (50th; 25th–75th). | Data finding: **25.3%** of counties have zero recorded ports and **39.0%** have zero DC fast ports. Every rate percentile below those shares gives a cutoff of exactly 0. Under the old defaults, all 526 selected counties had no stations at all, and the 10th–25th part of the slider did nothing (§3.7). |
| C4 | **Essential interactions** | Interaction in every view (toggle, linked maps, year slider, level filter, …). | **Three coordinated interactions only:** Q2 linked map ↔ dot plot, Q5 state dropdown, Q7 threshold sliders. Q1, Q3, Q4, and Q6 use hover only. | Feedback point 3. Keeps the scope feasible for three people. |
| C5 | **Q1** | Station/port toggle on the map. | Port-count map plus two aligned state bar charts (stations, ports). No toggle. | Showing both measures side by side makes "many locations vs. many ports" visible without any interaction. |
| C6 | **Q4** | Stacked bars + linked DC fast map. | Stacked 100% share bars + aligned DC fast rate dot plot, in the same state order. No map. | Saves a map, and a shared row order supports direct comparison. |
| C7 | **Q5** | Heatmap with state **and charging-level** filters; claimed to show "where NACS has spread". | State dropdown only. We dropped the level filter and the NACS-spread claim. | `ev_connector_types` lists connectors per **station**, not per port or per level, and has no history. It cannot support a level filter or an adoption timeline. |
| C8 | **Q6** | One scatterplot with a total/DC fast toggle; color for rural/urban. | Two side-by-side scatterplots (total, DC fast) with shared axes. Metro/nonmetro shown with **color and shape**. | Removes a toggle, allows direct comparison, and does not rely on color alone. |
| C9 | **Port-count missingness** | "Missing counts stay distinct from verified zeros." | AFDC writes zero ports at a level as a **blank**. A blank level is recoded to 0 when the station reports ports at another level. A station with **all three** levels blank is "incomplete" (1 station). | Data finding: the file contains no explicit zeros, and 83,665 of 83,666 stations report at least one level (§1.3). |
| C10 | **ACS source** | Census Data API. | ACS **table-based Summary File** (same tables and estimates). | The Census API now requires a key. The summary file is keyless and reproducible. |
| C11 | **Storyline** | Implicit. | Explicit storyboard (§2) with a short introduction that defines station / port / level / connector. | Recommended design direction: "Keep one storyline." |
| C12 | **Per-capita caveat** | Mentioned in text. | A note next to Q2 and Q6 states what "per 100,000 residents" measures and what it does not. | Recommended design direction: "Ask what per-capita supply answers." |

Not changed: the problem context, the seven questions' scope (apart from the Q3 wording), the data sources, and the optional second denominator (EV registrations / traffic). We keep that last one optional and do not plan it for this project.

---

## 1. Data snapshot and processing **[AI-a]**

### 1.1 Sources (frozen snapshot)

| Source | What we use | Vintage / retrieval | Rows used |
|---|---|---|---|
| AFDC Alternative Fueling Station Locator (DOE / NLR) | Station ID, location, port counts by level, network, connectors, open date | Snapshot dated **2026-10-30** (max `Updated At`), retrieved 2026-10-30 | 83,666 stations |
| ACS 2020–2024 5-year, B01003 | County and state population + MOE | 2020–2024 estimates, retrieved 2026-10-30 | 3,144 counties, 51 states |
| ACS 2020–2024 5-year, B19013 | Median household income (2024 $) + MOE | 2020–2024 estimates, retrieved 2026-10-30 | 3,143 counties with a value |
| Census 2024 cartographic boundaries | County polygons (1:500k for joins; 1:20m for maps) | 2024 | 3,144 counties |
| USDA ERS Rural-Urban Continuum Codes | `RUCC_2023` (1–3 metro, 4–9 nonmetro) | 2023 | 3,144 counties |

Access URLs and a one-command download script (`scripts/00_download.sh`) are in the README. County identifiers match across all three county sources (3,144 = 3,144 = 3,144). This includes Connecticut's nine planning regions (`09110`–`09190`), which ACS 2024, the 2024 boundaries, and RUCC 2023 all use.

### 1.2 Pipeline (`scripts/01_build_tables.py`)

| Step | Operation | Records after step |
|---|---|---|
| 1 | Download all AFDC records with `fuel_type=ELEC`, `status=E`, `access=public`, `country=US` | 83,686 |
| 2 | Deduplicate by AFDC `id` | 83,686 (0 duplicates) |
| 3 | Keep 50 states + DC (drops 20 Puerto Rico stations) | 83,666 |
| 4 | Validate coordinates (in U.S. bounding range, non-null) | 83,666 (0 invalid) |
| 5 | Recode port blanks (see C9); flag stations with all levels blank | 1 station flagged incomplete |
| 6 | Assign county by **point-in-polygon** (1:500k boundaries) | 83,648 within a polygon |
| 7 | For points just outside a polygon (piers, coastline), assign the nearest county **within 5 km** and flag it | +16 (`nearest_within_5km`) |
| 8 | Report the rest as unresolved; never drop silently | 2 unresolved (kept in station table, excluded from county sums) |
| 9 | Start from **all 3,144 counties**, left-join station sums, ACS, RUCC | 3,144 counties; 795 with no stations |
| 10 | Compute rates, ranks, percentiles, flags; write tables | see §1.4 |

QA output is written to `data/processed/qa_report.json`. Three stations sit in a county whose state differs from AFDC's `state` field (e.g. a mall on the NH/MA line). We trust the geometry and keep a flag.

### 1.3 What the data told us (findings that changed the plan)

1. **Opening dates are complete but partly synthetic.** No station is missing `open_date`. However, **6,694 stations (8.0%) share 2021-01-27** and **1,935 (2.3%) share 2020-06-12**. Almost all of them are ChargePoint stations (99.9% and 98.9%), which points to a network data feed being loaded on those days rather than to real opening dates. Only those two dates are shared by 500 or more stations. We flag them as likely bulk-load dates (`stations_on_bulk_dates`) and show them as a separate bar segment in Q3. → **C1**
2. **Zero ports are blanks.** In all three level fields the minimum non-blank value is 1. A blank therefore means "none at this level". Only one station (Vallejo Ferry Terminal, Solano County, CA) has all three blank. Under our rule ("an incomplete sum is not presented as complete") this makes **Solano County "port counts incomplete"**: it is excluded from Q2 ranks and Q7, and is shown with the missing-data style. → **C9**
3. **A quarter of counties have no recorded charging.** 795 of 3,144 counties (25.3%) have zero stations, and 1,225 (39.0%) have zero DC fast ports. This makes low percentiles degenerate. → **C3**
4. **Supply is concentrated.** California holds **26.5%** of all ports. The top five states (CA, NY, FL, TX, MA) hold **49.7%**. Nationally, ports split into 182,819 Level 2 (69.5%), 79,555 DC fast (30.2%), and only 688 Level 1 (0.3%).
5. **Small denominators dominate per-capita ranks.** Gilpin County, CO (pop. 5,901; casinos) ranks **#1** per capita with 99 ports, against #408 by count. Thomas County, NE (pop. 564) jumps from #2,059 to #49 with just 2 ports. → Q2 shows raw counts and population beside every rate and flags counties under 10,000 residents.

### 1.4 Processed tables (each supports one or more questions)

| Table | Unit of observation | Rows | Supports |
|---|---|---|---|
| `stations_clean.csv` | One AFDC station | 83,666 | Input to all; Q1 hover |
| `county_summary.csv` | One county / county-equivalent | 3,144 | **Q1, Q2, Q6, Q7** |
| `state_summary.csv` | One state or DC | 51 | **Q1, Q4** |
| `opening_year_summary.csv` | One opening-year group | 14 | **Q3** |
| `network_connector_summary.csv` | One state × network × connector (plus `state = US`) | 13,200 | **Q5** |
| `q7_sensitivity.csv` | One cutoff setting | 13 | **Q7** |

### 1.5 Measure definitions

| Measure | Definition | Undefined when |
|---|---|---|
| Stations | Distinct AFDC `id` | — |
| Total ports | L1 + L2 + DC fast ports | Any station in the area has all levels blank |
| Ports per 100k | `100000 × total_ports / population` | Ports incomplete or population ≤ 0 |
| DC fast per 100k | `100000 × dcfc_ports / population` | Same as above |
| Level share | Level ports / total ports | Total ports = 0 or incomplete |
| Network stations | Distinct stations whose `ev_network` = network | — |
| Connector % | Stations listing connector / stations with any connector listed (same network, same state) | Denominator = 0 |
| Rank (Q2) | Rank on the common eligible set (3,143 counties), 1 = most supply, ties share the lowest rank | Not eligible |
| Percentile (Q7) | Share of the 3,142 eligible counties at or below the value (equal county weight) | Not eligible |

> **Interpretation note (used beside Q2 and Q6):** "Ports per 100,000 residents" measures recorded public supply relative to the people who live in a county. It does **not** measure supply relative to EV ownership, highway traffic, visitors, or charging demand, and it says nothing about reliability, price, or waiting time.

---

## 2. Storyboard

The article is a single scroll. Each step answers one question and sets up the next one.

| Step | View | Reader takeaway | Transition to next |
|---|---|---|---|
| Intro | Four small icons: station, port, level (L1/L2/DC fast), connector | The vocabulary used in the charts | "Let's start with where chargers are." |
| Q1 | County port map + state bars | Supply is concentrated on the coasts and in big metros | "But big places have more people. What if we divide by residents?" |
| Q2 | Linked choropleth + ranked dot plot ★ | Rankings reshuffle; small counties jump | "When did these stations appear?" |
| Q3 | Opening-year bars | Most stations in today's data are recent, with caveats | "Not all chargers are equal. How fast, and which plug?" |
| Q4 | Level shares + DC fast rate | States differ in fast-charging supply | "Who runs them, and which cars can plug in?" |
| Q5 | Network bars + connector heatmap ★ | A few networks dominate; plug standards differ by network | "Does supply follow income or rurality?" |
| Q6 | Two scatterplots | Weak positive association; nonmetro counties lower | "Which counties combine all three conditions?" |
| Q7 | Sliders + map + table ★ | An adjustable shortlist, not a verdict | Conclusion |

★ = one of the three essential coordinated interactions.

> **[Insert storyboard sketch here: `sketches/storyboard.jpg`]**

---

## 3. Questions, processed data, and sketches

Sketch convention: every sketch shows the title, axis labels with units, the legend, the data source and snapshot date, the permanent notes, and the interactions marked in red.

### 3.1 Q1. Geographic distribution

**Question (unchanged):** Where are public charging stations and ports concentrated across states, and what local patterns appear within states?

**Processed data:** `county_summary.csv` (unit: county) and `state_summary.csv` (unit: state).
**Transformation:** station → county by point-in-polygon; sum ports by level; count distinct station IDs; carry a completeness flag.

Sample, `state_summary.csv` (top 5 and bottom 3 by total ports):

| state | state_name | stations | total_ports | ports_per_station |
|---|---|---:|---:|---:|
| CA | California | 20,380 | 69,630 | 3.42 |
| NY | New York | 5,540 | 20,563 | 3.71 |
| FL | Florida | 4,464 | 15,490 | 3.47 |
| TX | Texas | 3,867 | 13,160 | 3.40 |
| MA | Massachusetts | 4,617 | 11,842 | 2.56 |
| SD | South Dakota | 114 | 329 | 2.89 |
| ND | North Dakota | 108 | 283 | 2.62 |
| AK | Alaska | 70 | 194 | 2.77 |

(The county-level columns for Q1 are in the Q2 sample below; it is the same table.)

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Where public chargers are: ports by county" |
| Map | Albers USA, county outlines in light gray. **Circle at each county centroid; area ∝ total ports** (sqrt scale, 0 – 18,829). Counties with 0 stations: no circle. Solano (incomplete): hollow dashed circle + legend entry "port count incomplete". |
| Bars (right) | Two aligned horizontal bar charts with one state per row, sorted by total ports. Left panel: **stations** (x: 0–21k). Right panel: **ports** (x: 0–70k). Each panel has its own labeled axis. |
| Legend | Three reference circles (100, 1,000, 10,000 ports) + "incomplete" symbol |
| Hover | County/state name, stations, L1/L2/DC fast ports, completeness |
| Note | "Source: AFDC snapshot 2026-10-30. Circle area = ports." |

> **[Insert sketch Q1 here: `sketches/q1.jpg`]**

### 3.2 Q2. Population-adjusted supply ★

**Question (unchanged):** How do county rankings differ between total ports and ports per 100,000 residents?

**Processed data:** `county_summary.csv` (unit: county).
**Transformation:** join ACS population; compute `ports_per_100k`; rank both measures **on the same 3,143 eligible counties** (complete ports, population > 0), so that rank changes come only from the denominator.

| county_fips | county_name | state | stations | l1 | l2 | dcfc | total_ports | population | ports_per_100k | rank_total | rank_per_100k | supply_status |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 06037 | Los Angeles County | CA | 4,883 | 57 | 15,272 | 3,500 | 18,829 | 9,808,667 | 191.96 | 1 | 150 | complete |
| 17031 | Cook County | IL | 813 | 0 | 1,656 | 982 | 2,638 | 5,182,090 | 50.91 | 12 | 1,016 | complete |
| 36061 | New York County | NY | 386 | 0 | 1,601 | 62 | 1,663 | 1,629,477 | 102.06 | 21 | 436 | complete |
| 08047 | Gilpin County | CO | 38 | 0 | 97 | 2 | 99 | 5,901 | 1,677.68 | 408 | **1** | complete |
| 31171 | Thomas County | NE | 2 | 0 | 0 | 2 | 2 | 564 | 354.61 | 2,059 | 49 | complete |
| 39049 | Franklin County | OH | 428 | 0 | 883 | 207 | 1,090 | 1,333,048 | 81.77 | 43 | 592 | complete |
| 47157 | Shelby County | TN | 81 | 0 | 126 | 86 | 212 | 919,173 | 23.06 | 233 | 1,750 | complete |
| 01025 | Clarke County | AL | 1 | 0 | 0 | 2 | 2 | 22,543 | 8.87 | 2,059 | 2,220 | complete |
| 01009 | Blount County | AL | 0 | 0 | 0 | 0 | 0 | 59,518 | 0.00 | 2,349 | 2,349 | no stations recorded in this snapshot |
| 06095 | Solano County | CA | 161 | — | — | — | — | 451,918 | — | — | — | port counts incomplete |

Distribution of `ports_per_100k` (eligible counties): 0 → 795; (0, 10] → 166; (10, 25] → 488; (25, 50] → 665; (50, 100] → 578; (100, 200] → 313; > 200 → 138.

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Same chargers, different story: counts vs. ports per 100,000 residents" |
| Control | Segmented toggle **[Total ports | Ports per 100k]** shared by both views |
| Map (left) | County choropleth, sequential single hue. Bins for the rate: (0,10], (10,25], (25,50], (50,100], (100,200], >200. Bins for the count: quantile bins. **0 = light gray with a diagonal hatch**, labeled "no stations recorded". **Incomplete = white with a dashed outline.** Legend shows all bins, including zero and incomplete. |
| Dot plot (right) | One row per county, sorted by the selected measure. x = selected measure (count: 0–18,829 sqrt; rate: 0–1,700 sqrt), with the scale fixed per measure. Scrollable list with a sticky axis. Counties with population under 10,000 drawn as **hollow dots**, plus a legend entry. |
| Linking | Click a county in either view → highlighted in both (thick outline / enlarged dot) + **detail box**: name, ports, population, rate, rank by count, rank by rate, Δ rank |
| Note (always visible) | "Ports per 100,000 residents measures supply relative to residents, not highway travel demand. Rates in small counties can change greatly when a single station is added." |

> **[Insert sketch Q2 here: `sketches/q2.jpg`]**

### 3.3 Q3. Recorded opening dates of current stations (**revised, see C1**)

**Question:** Among stations present in our snapshot, how many have recorded opening dates in each year since 2015?

**Processed data:** `opening_year_summary.csv` (unit: opening-year group).
**Transformation:** parse `open_date` → year; group years before 2015 into one bin; mark the snapshot year as partial; count stations on dates shared by ≥ 500 stations (bulk-load flag). Invalid and future dates go to a separate "missing or invalid" group (0 in this snapshot).

| opening_year_group | stations | stations_on_bulk_dates | share_of_stations | is_partial_year | note |
|---|---:|---:|---:|---|---|
| before 2015 | 1,932 | 0 | 2.3% | False | |
| 2015 | 1,111 | 0 | 1.3% | False | |
| 2016 | 1,199 | 0 | 1.4% | False | |
| 2017 | 1,399 | 0 | 1.7% | False | |
| 2018 | 1,701 | 0 | 2.0% | False | |
| 2019 | 2,348 | 0 | 2.8% | False | |
| 2020 | 5,281 | **1,935** | 6.3% | False | |
| 2021 | 12,990 | **6,694** | 15.5% | False | |
| 2022 | 9,262 | 0 | 11.1% | False | |
| 2023 | 11,601 | 0 | 13.9% | False | |
| 2024 | 11,903 | 0 | 14.2% | False | |
| 2025 | 12,824 | 0 | 15.3% | False | |
| 2026 | 10,115 | 0 | 12.1% | **True** | partial year: through 2026-10-30 |
| missing or invalid date | 0 | 0 | 0.0% | False | |

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "When today's stations were recorded as opening" |
| Bars | x = year 2015 … 2026; y = **station count** (0–14,000). Bulk-date stations are a **hatched segment** on top of the 2020 and 2021 bars, labeled "single shared date (likely bulk entry)". 2026 is drawn with a lighter fill and a dashed outline, labeled "partial year (through Oct 30)". |
| Side summaries | Two small labeled boxes to the left/right of the axis: "Before 2015: 1,932" and "Missing/invalid date: 0" (kept even when 0) |
| Note **under the chart, always visible** | "This chart groups stations in the current snapshot by their recorded opening year. Closed stations are absent. Some dates are approximate or reflect when a station first appeared in the database; 8,629 stations share just two dates. These counts do not reconstruct the full history of charging supply." |
| Interaction | Hover only (exact count, share, bulk-date count) |

> **[Insert sketch Q3 here: `sketches/q3.jpg`]**

### 3.4 Q4. Charging-level mix

**Question (unchanged):** Which states have a higher share of Level 2 ports, and which have relatively little DC fast supply per resident?

**Processed data:** `state_summary.csv` (unit: state).
**Transformation:** sum ports by level per state; shares = level / total; DC fast rate uses the **state** ACS population.

Sample (four lowest DC fast rates, three large states, three highest):

| state | total_ports | l1 | l2 | dcfc | l1_share | l2_share | dcfc_share | population | dcfc_per_100k |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| LA | 848 | 0 | 427 | 421 | 0.000 | 0.504 | 0.496 | 4,611,961 | 9.1 |
| AR | 1,111 | 0 | 810 | 301 | 0.000 | 0.729 | 0.271 | 3,049,391 | 9.9 |
| DC | 1,096 | 2 | 1,025 | 69 | 0.002 | 0.935 | 0.063 | 681,294 | 10.1 |
| KY | 1,208 | 4 | 731 | 473 | 0.003 | 0.605 | 0.392 | 4,534,824 | 10.4 |
| NY | 20,563 | 9 | 17,221 | 3,333 | 0.000 | 0.837 | 0.162 | 19,852,366 | 16.8 |
| TX | 13,160 | 0 | 7,452 | 5,708 | 0.000 | 0.566 | 0.434 | 30,188,424 | 18.9 |
| FL | 15,490 | 33 | 9,957 | 5,500 | 0.002 | 0.643 | 0.355 | 22,416,077 | 24.5 |
| NV | 2,866 | 3 | 1,580 | 1,283 | 0.001 | 0.551 | 0.448 | 3,184,612 | 40.3 |
| CA | 69,630 | 284 | 49,688 | 19,658 | 0.004 | 0.714 | 0.282 | 39,287,377 | 50.0 |
| VT | 1,360 | 16 | 1,007 | 337 | 0.012 | 0.740 | 0.248 | 647,106 | 52.1 |

Early observation: a high DC fast **share** does not mean high DC fast **supply**. Louisiana has the highest share (49.6%) but the lowest rate (9.1 per 100k). This is why the two measures sit side by side.

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Level 2 dominates; fast-charging supply per resident varies more than five-fold" |
| Left panel | 100% stacked horizontal bar per state, **fixed 0–100% axis**, fixed segment order L1 → L2 → DC fast, with the share printed inside segments ≥ 8%. Three distinct hues + segment labels in the legend. |
| Right panel | Dot plot of DC fast ports per 100k (x: 0–60), **same row order** as the left panel. Sort selector: by L2 share (default) or by DC fast rate. National value as a vertical reference line (23.8 per 100k). |
| Hover | Absolute ports by level, total, population |
| Missing | Undefined share → gray "n/a" row (none at state level in this snapshot, but the style is defined) |

> **[Insert sketch Q4 here: `sketches/q4.jpg`]**

### 3.5 Q5. Networks and connectors ★

**Question (unchanged; scope narrowed, see C7):** Which networks have the most recorded stations in a selected state, and which connector types are listed at those stations?

**Processed data:** `network_connector_summary.csv` (unit: state × network × connector; `state = US` for the national default).
**Transformation:** split `ev_connector_types` on spaces; per state and network, count distinct stations (bar length) and the stations with any connector listed (denominator); per connector, count the stations listing it (numerator). `pct_of_known` = numerator / denominator. Connector labels: J1772, CCS1 (`J1772COMBO`), CHAdeMO, NACS (Tesla), NEMA 14-50, NEMA 5-20, NEMA 5-15, J3271 (MCS). Only 3 stations nationwide list no connector.

Long-format sample (dropdown = New York, top 3 networks, 4 main connectors):

| state | network | rank | network_stations | stations_connector_known | connector | stations_listing_connector | pct_of_known |
|---|---|---:|---:|---:|---|---:|---:|
| NY | ChargePoint Network | 1 | 2,614 | 2,614 | J1772 | 2,414 | 92.3 |
| NY | ChargePoint Network | 1 | 2,614 | 2,614 | CCS1 | 199 | 7.6 |
| NY | ChargePoint Network | 1 | 2,614 | 2,614 | CHAdeMO | 129 | 4.9 |
| NY | ChargePoint Network | 1 | 2,614 | 2,614 | NACS (Tesla) | 46 | 1.8 |
| NY | VIALYNK | 2 | 677 | 677 | J1772 | 654 | 96.6 |
| NY | VIALYNK | 2 | 677 | 677 | CCS1 | 38 | 5.6 |
| NY | VIALYNK | 2 | 677 | 677 | CHAdeMO | 0 | 0.0 |
| NY | VIALYNK | 2 | 677 | 677 | NACS (Tesla) | 8 | 1.2 |
| NY | Tesla Destination | 3 | 413 | 413 | J1772 | 77 | 18.6 |
| NY | Tesla Destination | 3 | 413 | 413 | NACS (Tesla) | 413 | 100.0 |

The same data as it feeds the heatmap (rows = networks, cells = % of stations listing the connector):

| network | stations | CCS1 | CHAdeMO | J1772 | NACS (Tesla) |
|---|---:|---:|---:|---:|---:|
| ChargePoint Network | 2,614 | 7.6 | 4.9 | 92.3 | 1.8 |
| VIALYNK | 677 | 5.6 | 0.0 | 96.6 | 1.2 |
| Tesla Destination | 413 | 0.0 | 0.0 | 18.6 | 100.0 |
| EVOKE | 259 | 2.7 | 0.0 | 97.3 | 0.0 |

Nationally there are 98 networks (median 32 per state). ChargePoint operates 58.5% of all stations. AFDC lists "Tesla" (Supercharger) and "Tesla Destination" as separate networks; we keep them separate. "Non-Networked" is kept as its own category.

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Who operates the stations, and which plugs they list — [State]" |
| Control | Dropdown: "United States (all)" + 50 states + DC |
| Left: bars | Top 10 networks by distinct stations + one "All other networks" bar; x = stations (axis rescales per state, labeled). "Non-Networked" bar in neutral gray. |
| Right: heatmap | Same row order as the bars; columns = connectors (CCS1, CHAdeMO, J1772, NACS, Other). Cell color = % of the network's stations with known connectors that list it, **fixed 0–100% sequential scale** across all states, with the % printed in each cell. |
| Hover | e.g. "J1772: 77 of 413 stations (18.6%)". Numerator and denominator always shown |
| Notes | "A station can list several connectors, so rows can sum to more than 100%. Listed connectors describe stations, not individual ports, and do not guarantee access for every vehicle." + "Stations with no connector listed: n" |

> **[Insert sketch Q5 here: `sketches/q5.jpg`]**

### 3.6 Q6. Income and rural-urban context

**Question (unchanged):** How does county income relate to ports per resident, and how do the patterns differ between metro and nonmetro counties?

**Processed data:** `county_summary.csv` (unit: county; 3,142 counties with income, population, and complete ports).
**Transformation:** join ACS income + MOE and RUCC 2023; `metro_status` = Metro if RUCC 1–3, Nonmetro if 4–9.

| county_fips | county_name | state | median_hh_income | income_moe | population | ports_per_100k | dcfc_per_100k | rucc_2023 | metro_status |
|---|---|---|---:|---:|---:|---:|---:|---:|---|
| 21189 | Owsley County | KY | 22,188 | 9,297 | 3,971 | 0.00 | 0.00 | 9 | Nonmetro |
| 54047 | McDowell County | WV | 31,559 | 2,515 | 17,943 | 0.00 | 0.00 | 9 | Nonmetro |
| 28101 | Newton County | MS | 50,540 | 5,200 | 21,093 | 9.48 | 0.00 | 8 | Nonmetro |
| 42117 | Tioga County | PA | 64,899 | 2,262 | 40,945 | 39.08 | 9.77 | 8 | Nonmetro |
| 51073 | Gloucester County | VA | 84,306 | 4,938 | 39,526 | 0.00 | 0.00 | 1 | Metro |
| 06037 | Los Angeles County | CA | 90,112 | 392 | 9,808,667 | 191.96 | 35.68 | 1 | Metro |
| 08014 | Broomfield County | CO | 123,874 | 3,714 | 76,304 | 305.36 | 51.11 | 1 | Metro |
| 51107 | Loudoun County | VA | 181,765 | 3,438 | 432,998 | 112.93 | 36.49 | 1 | Metro |

Preliminary association (descriptive only, Spearman ρ):

| Group | Counties | ρ(income, ports/100k) | ρ(income, DC fast/100k) | Median ports/100k | Share with 0 ports |
|---|---:|---:|---:|---:|---:|
| Metro | 1,185 | 0.36 | 0.22 | 38.4 | 11.1% |
| Nonmetro | 1,957 | 0.21 | 0.15 | 20.9 | 33.9% |

Excluded: De Baca County, NM (income not published by ACS) and Solano County, CA (ports incomplete). The plot displays "2 counties excluded (missing data)".

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Higher-income counties tend to have more chargers per resident, but the spread is wide" |
| Layout | Two scatterplots side by side: **All ports per 100k** \| **DC fast ports per 100k**, with **identical x and y scales** |
| x | Median household income, $20k–$190k, linear, ticks every $40k |
| y | Ports per 100k, **sqrt scale** 0–1,700 (keeps zeros visible on the axis; high outliers labeled) |
| Marks | Metro = filled **circle**, Nonmetro = hollow **triangle**, plus two contrasting colors (shape + color, not color alone). Opacity 0.5 for overplotting. Zero-rate counties sit on the baseline. |
| Hover | County, state, RUCC code + description, population, ports, income ± MOE |
| Note | Per-capita note from §1.5 + "Association only; income or rurality does not imply cause. Small income differences are within the ACS margin of error." |

> **[Insert sketch Q6 here: `sketches/q6.jpg`]**

### 3.7 Q7. Counties for closer review ★ (**cutoffs revised, see C2/C3**)

**Question:** Which counties combine low total charging supply per resident, low DC fast supply per resident, and lower household income, and how does the selected set change with the cutoffs?

**Processed data:** `county_summary.csv` (unit: county) + `q7_sensitivity.csv` (unit: cutoff setting).
**Transformation:** eligible set = 3,142 counties with complete ports, population > 0, and income. Percentiles are computed once on this fixed national set (equal county weight). Ties at a cutoff are included.

`selected = total_rate ≤ total_cutoff AND dcfc_rate ≤ dcfc_cutoff AND income ≤ income_cutoff`

| Condition | M1 default | **M2 default** | Actual value | **M2 slider range** |
|---|---|---|---|---|
| Total ports per 100k | ≤ 25th pct | **≤ 30th pct** | ≤ 9.4 | 25th–60th |
| DC fast ports per 100k | ≤ 25th pct | **≤ 40th pct** | ≤ 2.4 | 25th–60th |
| Median household income | ≤ 50th pct | ≤ 50th pct | ≤ $65,671 | 25th–75th |

Why the change: with 25.3% of counties at 0 total ports and 39.0% at 0 DC fast ports, both the 10th and the 25th percentile equal **0**. The old default therefore selected only counties with no stations at all (526/526), and the bottom half of each slider changed nothing. Each new default is **the first multiple of 5 above that measure's zero share** (25.3% → 30th; 39.0% → 40th). Both cutoffs are then above zero, so the screen also catches counties with *some* but very little supply. The slider ranges start at the 25th percentile so that readers can still see the "zero only" case.

Sample, `county_summary.csv` (Q7 columns): the 4 largest selected counties with stations, the 3 largest selected with none, and examples of "not selected" and "not evaluated":

| county_fips | county_name | state | stations | total_ports | dcfc_ports | population | ports_per_100k | dcfc_per_100k | income | metro | q7 status |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|
| 18095 | Madison County | IN | 3 | 7 | 1 | 131,900 | 5.31 | 0.76 | 63,037 | Metro | selected |
| 22057 | Lafourche Parish | LA | 1 | 2 | 2 | 96,252 | 2.08 | 2.08 | 63,135 | Metro | selected |
| 05145 | White County | AR | 4 | 7 | 0 | 77,838 | 8.99 | 0.00 | 55,249 | Nonmetro | selected |
| 28067 | Jones County | MS | 1 | 4 | 0 | 66,472 | 6.02 | 0.00 | 52,216 | Nonmetro | selected |
| 22045 | Iberia Parish | LA | 0 | 0 | 0 | 68,599 | 0.00 | 0.00 | 56,961 | Nonmetro | selected |
| 51143 | Pittsylvania County | VA | 0 | 0 | 0 | 59,856 | 0.00 | 0.00 | 54,085 | Nonmetro | selected |
| 01009 | Blount County | AL | 0 | 0 | 0 | 59,518 | 0.00 | 0.00 | 64,190 | Metro | selected |
| 01001 | Autauga County | AL | 3 | 13 | 10 | 59,947 | 21.69 | 16.68 | 72,481 | Metro | not selected |
| 01003 | Baldwin County | AL | 43 | 119 | 46 | 246,989 | 48.18 | 18.62 | 78,775 | Metro | not selected |
| 06095 | Solano County | CA | 161 | — | — | 451,918 | — | — | 100,401 | Metro | **not evaluated** |
| 35011 | De Baca County | NM | 1 | 4 | 4 | 1,576 | 253.81 | 253.81 | — | Nonmetro | **not evaluated** |

Sensitivity sample, `q7_sensitivity.csv` (one cutoff varied, the others held at the default):

| varied | total pct | DC pct | income pct | total cutoff | DC cutoff | income cutoff | selected | of which 0 stations | nonmetro | added vs default | removed vs default |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| total | 25th | 40th | 50th | 0.0 | 2.4 | $65,671 | 526 | 526 | 462 | 0 | 49 |
| **default** | **30th** | **40th** | **50th** | **9.4** | **2.4** | **$65,671** | **575** | **526** | **501** | **0** | **0** |
| total | 35th | 40th | 50th | 13.8 | 2.4 | $65,671 | 617 | 526 | 534 | 42 | 0 |
| total | 40th | 40th | 50th | 18.8 | 2.4 | $65,671 | 662 | 526 | 570 | 87 | 0 |
| total | 50th | 40th | 50th | 28.7 | 2.4 | $65,671 | 707 | 526 | 607 | 132 | 0 |
| total | 60th | 40th | 50th | 40.5 | 2.4 | $65,671 | 735 | 526 | 631 | 160 | 0 |
| DC fast | 30th | 25th | 50th | 9.4 | 0.0 | $65,671 | 569 | 526 | 500 | 0 | 6 |
| DC fast | 30th | 50th | 50th | 9.4 | 9.6 | $65,671 | 614 | 526 | 530 | 39 | 0 |
| DC fast | 30th | 60th | 50th | 9.4 | 15.9 | $65,671 | 614 | 526 | 530 | 39 | 0 |
| income | 30th | 40th | 25th | 9.4 | 2.4 | $56,725 | 336 | 305 | 301 | 0 | 239 |
| income | 30th | 40th | 75th | 9.4 | 2.4 | $75,811 | 775 | 704 | 654 | 200 | 0 |

Observations:
- The selected set is most sensitive to the **income** cutoff (336 → 775 counties across its range).
- The DC fast cutoff matters little once the total-rate cutoff is low: with total ≤ 9.4 per 100k, few counties can have much DC fast supply.
- **91% of the default selection (526 of 575) are counties with no recorded station.** The table therefore separates "no stations recorded" from "some stations", so the zero group does not hide the low-but-nonzero counties.

**Sketch: views and encodings**

| Element | Specification |
|---|---|
| Title | "Counties that may merit a closer look" |
| Control panel (top) | Three sliders labeled with **percentile and actual value** (e.g. "Total ports/100k ≤ 30th pct = 9.4"), the **rule in plain text**, a counter "575 counties selected (526 with no stations) · +0 / −0 vs. default", and a **Reset** button |
| Map | County map: selected + 0 stations = dark fill; selected + some stations = medium fill with a dot pattern; not selected = very light; **not evaluated = white with a dashed outline**. Legend lists all four. |
| Table | Sortable columns: county, state, stations, ports, DC fast, population, ports/100k, DC fast/100k, income, metro/nonmetro, status. A filter chip toggles "show not evaluated". |
| Linking | Click a map county ↔ the table row highlights and scrolls; the sliders update map, table, and counter |
| Caption (always visible) | "These counties meet the selected screening criteria and may merit closer review. This does not prove a charging shortage. Travel demand, EV ownership, neighboring chargers, operating conditions, and uncertainty in the estimates are not fully represented." |

> **[Insert sketch Q7 here: `sketches/q7.jpg`]**

---

## 4. Essential interactions (feedback point 3)

| # | Interaction | Views linked | Why it is essential |
|---|---|---|---|
| 1 | Count/rate toggle + county selection | Q2 map ↔ Q2 dot plot ↔ detail box | The core comparison of the project (count vs. per capita) |
| 2 | State dropdown | Q5 network bars ↔ connector heatmap | 52 states × ~32 networks cannot be shown at once |
| 3 | Threshold sliders + county selection | Q7 sliders → map + table + counter | Shows that the shortlist depends on the cutoffs |

All other views use hover tooltips only.

## 5. Design checks applied to every sketch

| Check | How we meet it |
|---|---|
| Readable labels | Dot plot and table scroll with sticky axes/headers; heatmap shows top 10 networks + "other"; values printed in cells/segments |
| Consistent scales | Q2 scale fixed per measure; Q4 share axis fixed 0–100%; Q5 heatmap fixed 0–100% across states; Q6 two panels share identical axes |
| Missing data explicit | Separate legend entries for "no stations recorded" (0), "port counts incomplete", "not evaluated", "missing/invalid date"; excluded counts printed |
| Not color-only | Q6 shape + color; Q7 fill + pattern; Q4 segment labels + fixed order; zero hatch on maps |
| Units and sources | Every axis has units; every view shows "AFDC snapshot 2026-10-30; ACS 2020–2024" |

## 6. Plan for Milestone 3 (Nov 16)

- Export `county_summary` joined with simplified 1:20m county geometry as TopoJSON for D3.
- Build Q2, Q5, and Q7 (the interactive views) first, then the four static views.
- Write the intro section and the transitions from the storyboard.
- Task split: `<fill in who owns which questions>`.

## 7. Repository contents

```
scripts/00_download.sh       download all raw data (URLs inside)
scripts/01_build_tables.py   cleaning, spatial join, all processed tables, QA report
scripts/02_make_samples.py   sample tables and numbers used in this report
data/processed/              processed CSVs + qa_report.json + snapshot_metadata.json
docs/M2_report.md            this report
sketches/                    hand-drawn sketches (photos/scans)
```

## 8. AI-use statement

> *Draft. The team must edit this to match exactly how AI was used before submission.*

- **Tool:** Claude (Anthropic), used through Claude Code.
- **Where:** (1) writing and debugging the download and data-processing scripts in `scripts/`; (2) drafting the structure and wording of §0–§7 of this report, including the sample tables, which are generated by `scripts/02_make_samples.py` from our real data; (3) reviewing the M1 feedback against our revised plan.
- **Not used for:** the sketches. All sketches were drawn by the team by hand / in Excalidraw.
- **Verification:** the team re-ran the pipeline, checked the QA counts and sample rows against the raw AFDC/ACS files, and is responsible for every number and design decision in this report.
