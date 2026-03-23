# 🇮🇪 Ireland Traffic Signs Explorer

A Streamlit web application for exploring parking locations and speed limit signs across the island of Ireland, powered by real OpenStreetMap data.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Dataset](#dataset)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the App](#running-the-app)
- [Usage Guide](#usage-guide)
- [Data Pipeline](#data-pipeline)
- [Tech Stack](#tech-stack)
- [Data Sources & Licence](#data-sources--licence)

---

## Overview

This project extracts, merges, and visualises traffic sign data from OpenStreetMap (OSM) for the entire island of Ireland — covering all 32 counties including Northern Ireland. It combines two datasets:

- **Traffic Signs** — 56,387 nodes tagged as stop signs, give way signs, speed limits, hazard signs, and more
- **Parking Locations** — 2,017 nodes tagged as car parks, parking areas, parking entrances, and parking signboards

The merged dataset of **58,404 records** is loaded into a Streamlit app with an interactive Folium map, sidebar filters, and tabbed data tables.

---

## Features

### 🗺️ Interactive Map
- Parking locations shown as coloured markers (🟢 free, 🔵 paid/unknown)
- Speed limit signs shown as colour-coded circles by speed value
- Click any marker to see full details (name, type, capacity, fee, wheelchair access)
- Layer toggle controls to show/hide parking or speed limits independently

### 🔍 Sidebar Filters
| Filter | Options |
|---|---|
| County / Region | All 32 counties + NI districts |
| Parking type | Surface, underground, multi-storey, street-side, lane, lay-by |
| Fee | All / Free / Paid |
| Wheelchair accessible | All / Yes / No or Limited |
| Speed limit range | Slider (km/h) |
| Nearby radius | 100m – 2000m from a selected parking spot |

### ⚡ Nearby Speed Limits
Enable "nearby" mode in the sidebar, then click any parking marker on the map to instantly see all speed limit signs within your chosen radius.

### 📊 Data Tables
- **Parking table** — searchable by name or operator, shows all filtered records
- **Speed limit table** — all filtered speed signs with coordinates and values
- Both tables show live row counts matching current filters

---

## Dataset

The app reads from a single Excel file — `ireland_all_signs_merged.xlsx` — which contains the following sheets:

| Sheet | Contents |
|---|---|
| `Ireland_All_Signs` | 58,404 merged records (main data sheet) |
| `Summary` | Sign type counts + bar chart |
| `Dataset_Breakdown` | Record counts by source |
| `Data_Sources` | Full provenance and methodology |

### Column Reference (`Ireland_All_Signs`)

| Column | Description |
|---|---|
| `osm_id` | OpenStreetMap node ID (e.g. `node/354198`) |
| `latitude` | Decimal degrees (6 d.p.) |
| `longitude` | Decimal degrees (6 d.p.) |
| `signboard_type` | Classified sign label (e.g. `RRS 001 – Stop`) |
| `dataset` | Source: `Traffic Signs` or `Parking` |
| `source` | `OSM` / `Mapillary` / `OSM+Mapillary` |
| `osm_tags` | Raw JSON of all OSM tags on the node |
| `mapillary_value` | Mapillary object_value (if applicable) |
| `last_seen` | ISO 8601 date |
| `notes` | Direction, county, supplementary info |
| `amenity` | OSM amenity value (parking nodes) |
| `parking_type` | surface / underground / multi-storey / street_side / lane / layby |
| `name` | Car park name (where mapped) |
| `operator` | Operating organisation |
| `access` | yes / customers / private / permit |
| `fee` | yes / no / charge string |
| `capacity` | Number of spaces (where mapped) |
| `wheelchair` | yes / limited / no |

---

## Project Structure

```
Traffic Assistant/
│
├── main.py                        # Streamlit application
├── ireland_all_signs_merged.xlsx  # Merged dataset (58,404 records)
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

---

## Installation

### Prerequisites
- Python 3.9 or higher
- pip

### Steps

```bash
# 1. Clone or download this project folder
cd "Traffic Assistant"

# 2. (Recommended) Create a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

### `requirements.txt`
```
streamlit>=1.35.0
folium>=0.14.0
streamlit-folium>=0.15.0
openpyxl>=3.1.0
pandas>=2.0.0
```

---

## Running the App

```bash
streamlit run main.py
```

Then open your browser at `http://localhost:8501`.

> **Note:** The first load may take 10–20 seconds while the app reads and processes the 58,404-row Excel dataset. Subsequent interactions are instant due to Streamlit's `@st.cache_data`.

---

## Usage Guide

### Exploring parking in a specific county
1. Open the sidebar → **County / Region** → select e.g. `Dublin`
2. The map re-centres on Dublin and all 3 metric cards update
3. Use **Parking type** to narrow to e.g. `underground` only
4. Toggle **Fee → Free** to show only free parking

### Finding speed limits near a car park
1. Enable **"Enable — click a parking marker to activate"** in the sidebar
2. Set your preferred radius (e.g. 500m)
3. Click any parking marker (🅿️) on the map
4. A table appears below the map showing all speed limit signs within that radius

### Searching for a specific car park
1. Scroll down to the **Parking Locations** tab
2. Type a name in the search box (e.g. `Q-Park`, `Dunnes`, `Tesco`)
3. The table filters live as you type

### Adjusting the speed limit layer
1. Use the **Speed limit range** slider (e.g. set to 80–100 km/h)
2. Only signs in that speed range appear on the map and in the speed table
3. Toggle **Show Speed Limits** off to hide the layer entirely

---

## Data Pipeline

The dataset was built through the following steps:

```
1. Overpass API query (overpass-turbo.eu)
        ↓  highway=stop/give_way, traffic_sign=*, maxspeed=*, overtaking=no
        ↓  → export.geojson  (56,387 nodes)

2. Second Overpass query
        ↓  traffic_sign~park, amenity=parking, sign_type~park
        ↓  → 2,077 parking nodes

3. Sign classification
        ↓  4-tier priority: OSM traffic_sign tag → Mapillary value
        ↓  → inferred RSA code → fallback

4. Spatial deduplication
        ↓  60 duplicate OSM node IDs removed

5. Excel merge
        ↓  ireland_all_signs_merged.xlsx  (58,404 records)

6. Streamlit app
        ↓  Interactive map + filters + data tables
```

**Coverage:** Island of Ireland — bounding box `51.3, -10.7 → 55.5, -5.8`
**Query date:** 2026-03-22

---

## Tech Stack

| Library | Purpose |
|---|---|
| `streamlit` | Web app framework |
| `folium` | Interactive Leaflet.js map |
| `streamlit-folium` | Streamlit ↔ Folium bridge |
| `pandas` | Data loading and filtering |
| `openpyxl` | Reading the `.xlsx` dataset |

---

## Data Sources & Licence

- **OpenStreetMap** — © OpenStreetMap contributors, licensed under the [Open Database Licence (ODbL)](https://opendatacommons.org/licenses/odbl/)
- **Mapillary** — street-level imagery sign detections (where applicable)
- Map tiles — © CartoDB (Positron)

> Any derived data or visualisations must carry the attribution: **"© OpenStreetMap contributors"**
