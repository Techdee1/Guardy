# Real Data Collection Guide for Nigerian Floods

**Current Status**: Initial dataset created with 663 samples based on known major flood events (2012, 2018, 2020, 2022).

**What's needed**: Replace simulated weather data with real measurements from reliable sources.

---

## Priority 1: Free & Accessible Data Sources

### 1. **CHIRPS Rainfall Data** ⭐ HIGHEST PRIORITY
**What it is**: Satellite-derived rainfall estimates for Africa  
**Resolution**: Daily, 0.05° (~5.5 km grid)  
**Coverage**: 1981-present  
**How to access**:

```bash
# Method 1: Download from website
# Visit: https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/tifs/
# Download daily rainfall for Nigeria region
# Coordinates: lat 4-14, lon 2.5-15

# Method 2: Use Python library
pip install pychirps
# Then in Python:
from pychirps import download
download.daily(2010, 2024, 'nigeria_rainfall.tif')
```

**What to extract**:
- Daily rainfall for each of our 10 focus locations
- Match dates with flood events (2012-07 to 2012-11, etc.)
- Save as CSV with columns: date, lat, lon, rainfall_mm

---

### 2. **Dartmouth Flood Observatory** ⭐ HIGH PRIORITY
**What it is**: Global database of large flood events  
**Coverage**: 1985-2023  
**How to access**:

1. Visit: https://floodobservatory.colorado.edu/Archives/index.html
2. Download: "Global Active Archive of Large Flood Events"
3. Filter for Nigeria (Country code: NG)

**What to extract**:
```csv
event_id,date,country,location,centroid_lat,centroid_lon,severity,area_km2,displaced,casualties
123,2012-10-15,Nigeria,Kogi State,7.7333,6.7333,3,15000,500000,76
```

**Nigerian flood events to look for**:
- 2012: Kogi, Benue, Delta, Rivers, Bayelsa (worst in 40 years)
- 2018: Benue, Kogi, Delta, Anambra
- 2020: 27 states affected
- 2022: Over 600 casualties, 1.4M displaced
- 2024: Recent events

---

### 3. **Global Flood Database (Cloud to Street)** ⭐ MEDIUM PRIORITY
**What it is**: Satellite-detected flood extent maps  
**Coverage**: 2000-2018  
**How to access**:

1. Visit: https://global-flood-database.cloudtostreet.ai/
2. Search for Nigeria
3. Download flood maps as GeoTIFF

**What to extract**:
- Flood extent polygons
- Affected areas (km²)
- Duration (start/end dates)

---

### 4. **ERA5 Climate Data (Copernicus)** ⭐ MEDIUM PRIORITY
**What it is**: Hourly climate reanalysis  
**Variables**: Temperature, humidity, precipitation, pressure  
**Coverage**: 1950-present  
**How to access**:

```bash
# Register at: https://cds.climate.copernicus.eu/
# Install CDS API
pip install cdsapi

# Download script
import cdsapi
c = cdsapi.Client()
c.retrieve(
    'reanalysis-era5-single-levels',
    {
        'product_type': 'reanalysis',
        'variable': ['2m_temperature', 'total_precipitation', 'relative_humidity'],
        'year': ['2010', '2011', ..., '2024'],
        'month': ['01', '02', ..., '12'],
        'day': [...],
        'time': '00:00',
        'area': [14, 2.5, 4, 15],  # North, West, South, East (Nigeria bounds)
        'format': 'netcdf',
    },
    'nigeria_climate_2010_2024.nc')
```

---

## Priority 2: Nigerian Government Sources

### 5. **NEMA (National Emergency Management Agency)** ⭐ HIGH VALUE
**What to find**:
- Annual flood reports (2010-2024)
- State-by-state casualty figures
- Affected local government areas
- Number of displaced persons

**Where to look**:
1. Official website: https://nema.gov.ng
2. Publications/Reports section
3. Annual reports and situation reports
4. Media releases during flood seasons

**Example search queries**:
- "NEMA 2012 flood report"
- "Nigeria flood statistics 2022"
- "NEMA flood situation report October 2022"

---

### 6. **Nigeria Hydrological Services Agency (NIHSA)**
**What to find**:
- River level forecasts
- Dam release schedules (Kainji, Jebba, Shiroro)
- Flood warnings
- River gauge readings

**Where to look**:
- Official website: https://nihsa.gov.ng
- Annual Flood Outlook reports
- River basin data

---

### 7. **Nigerian Meteorological Agency (NiMet)**
**What to find**:
- Historical weather data
- Rainfall totals by state
- Seasonal forecasts
- Weather station data

**Contact**:
- Request historical data via email
- May require formal request letter
- Some data may have nominal fees

---

## Priority 3: News Archives & Research Papers

### 8. **Nigerian News Archives**
**Sources to scrape/search**:
- Premium Times (premiumtimesng.com)
- The Punch (punchng.com)
- Vanguard (vanguardngr.com)
- The Guardian Nigeria (guardian.ng)
- Daily Trust (dailytrust.com)

**Search strategy**:
```python
# Search queries for each flood year
queries = [
    "Nigeria flood 2012 deaths",
    "Kogi flood October 2012",
    "Lagos flood 2011",
    "Port Harcourt flood casualties",
    "Benue flood displaced 2018"
]

# Extract from articles:
# - Date, Location, Severity, Casualties, Description
```

**Example Python scraper**:
```python
import requests
from bs4 import BeautifulSoup

def search_news(query, year):
    # Google search: site:premiumtimesng.com "query" year
    # Extract articles
    # Parse: date, location, casualties, description
    pass
```

---

### 9. **Academic Papers & Reports**
**Search on**:
- Google Scholar: "Nigeria flood 2012"
- ResearchGate
- African Journals Online (AJOL)
- Nigerian university repositories

**Key papers to find**:
- Flood risk assessment studies
- Historical flood analysis
- Climate change impacts on Nigerian floods

---

## Priority 4: Satellite & Remote Sensing Data

### 10. **NASA MODIS Flood Data**
**What it is**: Satellite-detected water extent  
**How to access**: https://modis.gsfc.nasa.gov/

### 11. **Sentinel-1 SAR Flood Maps**
**What it is**: Radar-based flood detection  
**How to access**: https://scihub.copernicus.eu/

---

## Data Enhancement Workflow

### Step 1: Download CHIRPS Data (DO THIS FIRST)
```bash
# Get rainfall for all flood event dates
python scripts/download_chirps.py --start-year 2010 --end-year 2024
```

### Step 2: Merge with Existing Dataset
```python
import pandas as pd

# Load our current data
current = pd.read_csv('data/training/real_flood_events.csv')

# Load CHIRPS rainfall
chirps = pd.read_csv('data/external/chirps_nigeria_2010_2024.csv')

# Merge on date and location
enhanced = current.merge(
    chirps[['date', 'lat', 'lon', 'rainfall_mm']],
    left_on=['date', 'latitude', 'longitude'],
    right_on=['date', 'lat', 'lon'],
    how='left'
)

# Replace simulated rainfall with real data
enhanced['rainfall_mm'] = enhanced['rainfall_mm_y'].fillna(enhanced['rainfall_mm_x'])
```

### Step 3: Add Dartmouth Flood Events
```python
# Load Dartmouth flood database
dartmouth = pd.read_csv('data/external/dartmouth_nigeria_floods.csv')

# Add new flood events we didn't know about
# Append to our dataset
```

### Step 4: Validate & Save
```python
# Check for missing values
# Verify date ranges
# Save enhanced dataset
enhanced.to_csv('data/training/enhanced_flood_events.csv', index=False)
```

---

## Sample Data Structure (Target)

```csv
date,location,state,latitude,longitude,flood_occurred,severity,casualties,displaced,
rainfall_mm,temperature,humidity,pressure,wind_speed,water_level_cm,
elevation_m,river_distance_km,urban_rural,source

2012-10-14,Lokoja,Kogi,7.7989,6.7397,1,severe,76,500000,
285.4,27.8,92,1012,3.2,185.0,
52,0.5,urban,"CHIRPS+Dartmouth+NEMA"

2012-10-15,Lokoja,Kogi,7.7989,6.7397,1,severe,0,500000,
302.1,27.5,94,1011,4.1,195.0,
52,0.5,urban,"CHIRPS+Dartmouth+NEMA"
```

---

## Quick Wins (Start Here)

✅ **Week 1**: Search Nigerian news archives for flood reports (manual)  
✅ **Week 2**: Download CHIRPS data for Nigeria (automated)  
✅ **Week 3**: Extract Dartmouth flood events for Nigeria  
✅ **Week 4**: Merge all data sources into enhanced dataset  

---

## Current Dataset Summary

**File**: `data/training/real_flood_events.csv`  
**Samples**: 663 (314 flood, 349 non-flood)  
**Date Range**: 2010-2024  
**Locations**: 10 major cities/states  
**Features**: lat, lon, date, rainfall, temp, humidity, water_level  
**Weather Data**: ⚠️ SIMULATED - needs replacement  

**Known Flood Events Included**:
- 2012 floods (240 samples across affected states)
- 2018 floods (74 samples)
- 2020 floods (partial)
- 2022 floods (partial)

---

## Resources & Links

### Data Download Tools
- **CHIRPS Python**: https://github.com/chc-ucsb/pychirps
- **ERA5 Python**: https://cds.climate.copernicus.eu/api-how-to
- **Copernicus API**: https://github.com/ecmwf/cdsapi

### Research Databases
- **Google Dataset Search**: https://datasetsearch.research.google.com/
- **World Bank Data**: https://data.worldbank.org/country/nigeria
- **FAO Data**: http://www.fao.org/faostat/en/#data

### Contact Information
- **NEMA**: info@nema.gov.ng
- **NiMet**: info@nimet.gov.ng
- **NIHSA**: info@nihsa.gov.ng

---

## Next Steps After Data Collection

1. ✅ Replace simulated weather with real CHIRPS data
2. ✅ Add Dartmouth flood events
3. ✅ Validate data quality (no missing values, realistic ranges)
4. → Run feature engineering: `python scripts/feature_engineering.py`
5. → Train models: `jupyter notebook notebooks/train_risk_scorer.ipynb`

---

**Remember**: Real data = Accurate models = Lives saved! 🇳🇬
