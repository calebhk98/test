#!/usr/bin/env bash
# Download the two open geography/deprivation datasets used by db/schema_geo.sql.
# Run from the project root:  bash etl/00_download_geo.sh
# Everything here is open data with stable, citable URLs so a student on a fresh
# machine gets byte-for-byte the same inputs.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw data/raw/pcd_unzip

# 1. English Indices of Deprivation 2019 — File 7 (all scores/ranks/deciles per
#    2011 LSOA). Source page:
#    https://www.gov.uk/government/statistics/english-indices-of-deprivation-2019
echo "[1/2] IoD 2019 File 7 (LSOA-level)…"
curl -fL --retry 4 --retry-delay 2 -o data/raw/imd2019_lsoa_all.csv \
  "https://assets.publishing.service.gov.uk/media/5dc407b440f0b6379a7acc8d/File_7_-_All_IoD2019_Scores__Ranks__Deciles_and_Population_Denominators_3.csv"

# 2. ONS "Postcode to OA(2011) to LSOA to MSOA to LAD (August 2021) Best Fit
#    Lookup in the UK". 2011 LSOAs, chosen to match IoD 2019.
#    Open Geography Portal item: 3e265c6a114f425fbd92e863977e698a
echo "[2/2] ONS postcode -> 2011 LSOA lookup (≈24 MB zip, 389 MB CSV)…"
curl -fL --retry 4 --retry-delay 2 -o data/raw/pcd_lsoa_aug21.zip \
  "https://www.arcgis.com/sharing/rest/content/items/3e265c6a114f425fbd92e863977e698a/data"
unzip -o data/raw/pcd_lsoa_aug21.zip -d data/raw/pcd_unzip >/dev/null

echo "Done. Now: mysql < db/schema_geo.sql && node etl/03_load_geo.js"
