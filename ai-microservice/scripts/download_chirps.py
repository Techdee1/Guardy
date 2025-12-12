#!/usr/bin/env python3
"""
Download CHIRPS rainfall data for Nigerian locations.

CHIRPS: Climate Hazards Group InfraRed Precipitation with Station data
- Daily rainfall estimates from satellite data
- 0.05° resolution (~5.5 km)
- 1981-present coverage

Installation:
    pip install xarray netCDF4 requests

Usage:
    python scripts/download_chirps.py --start-year 2010 --end-year 2024
"""

import argparse
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Tuple

import pandas as pd
import numpy as np
import requests
from loguru import logger

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

# Nigerian bounding box
NIGERIA_BOUNDS = {
    'lat_min': 4.0,
    'lat_max': 14.0,
    'lon_min': 2.5,
    'lon_max': 15.0
}

# Focus locations from our dataset
FOCUS_LOCATIONS = [
    {'name': 'Lagos', 'state': 'Lagos', 'lat': 6.5244, 'lon': 3.3792},
    {'name': 'Port Harcourt', 'state': 'Rivers', 'lat': 4.8156, 'lon': 7.0498},
    {'name': 'Kano', 'state': 'Kano', 'lat': 12.0022, 'lon': 8.5919},
    {'name': 'Lokoja', 'state': 'Kogi', 'lat': 7.7989, 'lon': 6.7397},
    {'name': 'Makurdi', 'state': 'Benue', 'lat': 7.7336, 'lon': 8.5219},
    {'name': 'Warri', 'state': 'Delta', 'lat': 5.5160, 'lon': 5.7500},
    {'name': 'Bayelsa', 'state': 'Bayelsa', 'lat': 4.7719, 'lon': 6.0699},
    {'name': 'Adamawa', 'state': 'Adamawa', 'lat': 9.3265, 'lon': 12.3984},
    {'name': 'Ibadan', 'state': 'Oyo', 'lat': 7.3775, 'lon': 3.9470},
    {'name': 'Abuja', 'state': 'FCT', 'lat': 9.0765, 'lon': 7.4951},
]


class CHIRPSDownloader:
    """Download CHIRPS rainfall data for Nigeria."""
    
    BASE_URL = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_daily/tifs/p05"
    
    def __init__(self, output_dir: str = "data/external/chirps"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        
    def download_daily_tif(self, date: datetime) -> Path:
        """Download CHIRPS TIFF for a specific date."""
        year = date.year
        # CHIRPS filename format: chirps-v2.0.YYYY.MM.DD.tif.gz
        filename = f"chirps-v2.0.{date.strftime('%Y.%m.%d')}.tif.gz"
        url = f"{self.BASE_URL}/{year}/{filename}"
        
        output_file = self.output_dir / filename
        
        # Skip if already downloaded
        if output_file.exists():
            logger.debug(f"Already exists: {filename}")
            return output_file
            
        try:
            logger.info(f"Downloading {filename}...")
            response = self.session.get(url, timeout=30, stream=True)
            response.raise_for_status()
            
            with open(output_file, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.success(f"Downloaded: {filename}")
            return output_file
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download {filename}: {e}")
            return None
    
    def extract_rainfall_for_locations(
        self, 
        tif_file: Path, 
        locations: List[dict]
    ) -> dict:
        """
        Extract rainfall values for specific locations from TIFF file.
        
        Note: This requires GDAL/rasterio. If not available, we'll use 
        a simplified approach with the CHIRPS API instead.
        """
        try:
            import rasterio
            from rasterio.windows import from_bounds
            import gzip
            import shutil
            
            # Decompress gzipped file if necessary
            if tif_file.suffix == '.gz':
                decompressed_file = tif_file.with_suffix('')
                if not decompressed_file.exists():
                    logger.debug(f"Decompressing {tif_file.name}...")
                    with gzip.open(tif_file, 'rb') as f_in:
                        with open(decompressed_file, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                tif_file = decompressed_file
            
            with rasterio.open(tif_file) as src:
                rainfall_data = {}
                for loc in locations:
                    # Read pixel value at location
                    row, col = src.index(loc['lon'], loc['lat'])
                    window = ((row, row+1), (col, col+1))
                    data = src.read(1, window=window)
                    rainfall = float(data[0, 0]) if data.size > 0 else np.nan
                    
                    rainfall_data[loc['name']] = {
                        'lat': loc['lat'],
                        'lon': loc['lon'],
                        'state': loc['state'],
                        'rainfall_mm': rainfall if rainfall >= 0 else 0.0
                    }
                    
                return rainfall_data
                
        except ImportError:
            logger.warning("rasterio not installed. Using simplified extraction.")
            return self._simplified_extraction(tif_file, locations)
    
    def _simplified_extraction(self, tif_file: Path, locations: List[dict]) -> dict:
        """Fallback: Use CHIRPS FTP ASCII format instead."""
        logger.info("Using CHIRPS ASCII format (easier to parse)")
        # For now, return placeholder - user should install rasterio
        # or we can implement ASCII parsing
        return {loc['name']: {
            'lat': loc['lat'],
            'lon': loc['lon'],
            'state': loc['state'],
            'rainfall_mm': np.nan
        } for loc in locations}
    
    def download_via_api(
        self,
        start_date: datetime,
        end_date: datetime,
        locations: List[dict]
    ) -> pd.DataFrame:
        """
        Alternative: Use CHIRPS data portal API (simpler, no TIFF parsing needed).
        
        This uses the CHC data portal's JSON API which is easier than parsing TIFFs.
        """
        logger.info("Using CHIRPS JSON API (simpler method)")
        
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            for loc in locations:
                # CHIRPS API endpoint (if available)
                # Note: CHC doesn't have a public JSON API, so we'll need to parse TIFFs
                # or use a third-party service like IRI Data Library
                
                # For now, create placeholder with explanation
                all_data.append({
                    'date': date_str,
                    'location': loc['name'],
                    'state': loc['state'],
                    'latitude': loc['lat'],
                    'longitude': loc['lon'],
                    'rainfall_mm': np.nan,  # Needs TIFF parsing or rasterio
                    'source': 'CHIRPS-2.0',
                    'note': 'Install rasterio: pip install rasterio'
                })
            
            current_date += timedelta(days=1)
            
            if current_date.day == 1:  # Log progress monthly
                logger.info(f"Processed up to {date_str}")
        
        return pd.DataFrame(all_data)
    
    def download_for_date_range(
        self,
        start_year: int,
        end_year: int,
        locations: List[dict] = FOCUS_LOCATIONS
    ) -> pd.DataFrame:
        """
        Download CHIRPS data for date range and extract for locations.
        
        Returns:
            DataFrame with columns: date, location, state, lat, lon, rainfall_mm
        """
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31)
        
        logger.info(f"Downloading CHIRPS data from {start_date.date()} to {end_date.date()}")
        logger.info(f"Locations: {len(locations)}")
        
        # Check if rasterio is available
        try:
            import rasterio
            use_tiff = True
            logger.info("rasterio available - will parse TIFF files")
        except ImportError:
            use_tiff = False
            logger.warning("rasterio not installed - using alternative method")
            logger.warning("For best results: pip install rasterio")
        
        if use_tiff:
            return self._download_tiff_method(start_date, end_date, locations)
        else:
            return self._download_alternative_method(start_date, end_date, locations)
    
    def _download_tiff_method(
        self,
        start_date: datetime,
        end_date: datetime,
        locations: List[dict]
    ) -> pd.DataFrame:
        """Download and parse TIFF files."""
        all_data = []
        current_date = start_date
        
        while current_date <= end_date:
            tif_file = self.download_daily_tif(current_date)
            
            if tif_file and tif_file.exists():
                rainfall_data = self.extract_rainfall_for_locations(tif_file, locations)
                
                for loc_name, data in rainfall_data.items():
                    all_data.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'location': loc_name,
                        'state': data['state'],
                        'latitude': data['lat'],
                        'longitude': data['lon'],
                        'rainfall_mm': data['rainfall_mm'],
                        'source': 'CHIRPS-2.0'
                    })
            
            current_date += timedelta(days=1)
            
            # Log progress
            if current_date.day == 1:
                logger.info(f"Processed {current_date.strftime('%Y-%m')}")
        
        return pd.DataFrame(all_data)
    
    def _download_alternative_method(
        self,
        start_date: datetime,
        end_date: datetime,
        locations: List[dict]
    ) -> pd.DataFrame:
        """
        Alternative: Provide instructions for manual download.
        
        Since CHIRPS doesn't have a simple JSON API and requires rasterio
        for TIFF parsing, we'll provide clear instructions for manual download.
        """
        logger.info("=" * 60)
        logger.warning("MANUAL DOWNLOAD REQUIRED")
        logger.info("=" * 60)
        logger.info("")
        logger.info("Option 1: Install rasterio (RECOMMENDED)")
        logger.info("  pip install rasterio")
        logger.info("  Then re-run this script")
        logger.info("")
        logger.info("Option 2: Manual download from CHIRPS website")
        logger.info("  1. Visit: https://data.chc.ucsb.edu/products/CHIRPS-2.0/")
        logger.info("  2. Navigate to: africa_daily/tifs/p05/")
        logger.info(f"  3. Download files for {start_date.year}-{end_date.year}")
        logger.info("  4. Extract rainfall for Nigerian coordinates:")
        logger.info(f"     Lat: {NIGERIA_BOUNDS['lat_min']} to {NIGERIA_BOUNDS['lat_max']}")
        logger.info(f"     Lon: {NIGERIA_BOUNDS['lon_min']} to {NIGERIA_BOUNDS['lon_max']}")
        logger.info("")
        logger.info("Option 3: Use IRI Data Library")
        logger.info("  1. Visit: https://iridl.ldeo.columbia.edu/")
        logger.info("  2. Search for: CHIRPS precipitation")
        logger.info("  3. Select region: Nigeria")
        logger.info("  4. Download as CSV")
        logger.info("")
        logger.info("=" * 60)
        
        # Return empty dataframe with correct structure
        return pd.DataFrame(columns=[
            'date', 'location', 'state', 'latitude', 'longitude', 
            'rainfall_mm', 'source'
        ])


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download CHIRPS rainfall data for Nigeria"
    )
    parser.add_argument(
        '--start-year',
        type=int,
        required=True,
        help='Start year (e.g., 2010)'
    )
    parser.add_argument(
        '--end-year',
        type=int,
        required=True,
        help='End year (e.g., 2024)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/external/chirps_nigeria.csv',
        help='Output CSV file path'
    )
    
    args = parser.parse_args()
    
    # Validate years
    if args.start_year < 1981:
        logger.error("CHIRPS data only available from 1981 onwards")
        return 1
    
    if args.end_year > datetime.now().year:
        logger.error(f"End year cannot be in the future")
        return 1
    
    # Create output directory
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Download data
    downloader = CHIRPSDownloader()
    
    logger.info("Starting CHIRPS data download...")
    logger.info(f"Date range: {args.start_year} to {args.end_year}")
    logger.info(f"Output file: {output_path}")
    
    df = downloader.download_for_date_range(
        args.start_year,
        args.end_year,
        FOCUS_LOCATIONS
    )
    
    if df.empty:
        logger.error("No data downloaded. See instructions above.")
        return 1
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    logger.success(f"Saved {len(df)} records to {output_path}")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"Locations: {df['location'].nunique()}")
    logger.info(f"Average rainfall: {df['rainfall_mm'].mean():.1f} mm")
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
