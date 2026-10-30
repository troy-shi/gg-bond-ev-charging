#!/usr/bin/env bash
# Download every raw input into data/raw/. Re-running replaces the AFDC snapshot,
# so record the new retrieval date in data/processed/snapshot_metadata.json.
set -euo pipefail
cd "$(dirname "$0")/../data/raw"

# 1. AFDC: public, available (status E) U.S. electric stations, all records.
#    DEMO_KEY works for a single bulk request; get a free key at developer.nlr.gov for repeated use.
AFDC_KEY="${AFDC_API_KEY:-DEMO_KEY}"
curl -sSL -o afdc_elec_public_available.csv \
  "https://developer.nlr.gov/api/alt-fuel-stations/v1.csv?api_key=${AFDC_KEY}&fuel_type=ELEC&status=E&access=public&country=US&limit=all"

# 2. ACS 2020-2024 5-year table-based summary files (no API key required).
for t in b01003 b19013; do
  curl -sSL -o "acsdt5y2024-${t}.dat" \
    "https://www2.census.gov/programs-surveys/acs/summary_file/2024/table-based-SF/data/5YRData/acsdt5y2024-${t}.dat"
done

# 3. Census 2024 cartographic boundaries (500k for spatial join, 20m for maps).
for f in cb_2024_us_county_500k cb_2024_us_county_20m cb_2024_us_state_20m; do
  curl -sSL -o "${f}.zip" "https://www2.census.gov/geo/tiger/GENZ2024/shp/${f}.zip"
done

# 4. USDA ERS 2023 Rural-Urban Continuum Codes.
curl -sSL -o rucc2023.csv \
  "https://ers.usda.gov/sites/default/files/_laserfiche/DataFiles/53251/Ruralurbancontinuumcodes2023.csv"

date -u +"%Y-%m-%dT%H:%M:%SZ" > RETRIEVED_AT.txt
echo "Downloaded to $(pwd)"
