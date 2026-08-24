import os
import sys
from pathlib import Path
import geopandas as gpd
import pandas as pd
from dotenv import load_dotenv

# Dynamically locate and load backend/.env file
BASE_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = os.path.join(BASE_DIR, "backend", ".env")
load_dotenv(dotenv_path=ENV_PATH)

# Add the 'backend' directory to the Python path to resolve imports
sys.path.append(os.path.join(BASE_DIR, "backend"))

# Import the centralized database engine from app.db.session
from app.db.session import engine

def seed_boundaries():
    print("Initializing Database connection...")
    try:
        # ----------------------------------------------------
        # 1. Seed Exclusive Economic Zone (EEZ)
        # ----------------------------------------------------
        eez_path = "data/boundaries/eez_v12_lowres.gpkg"
        if os.path.exists(eez_path):
            print(f"Reading Exclusive Economic Zone data from {eez_path}...")
            gdf_eez = gpd.read_file(eez_path)
            
            # Sovereign names are stored in "SOVEREIGN1" or "SOVEREIGNTY"
            col_name = "SOVEREIGN1" if "SOVEREIGN1" in gdf_eez.columns else "SOVEREIGNTY"
            gdf_eez = gdf_eez[gdf_eez[col_name] == "India"]
            
            # Verify spatial projection is EPSG:4326
            if gdf_eez.crs != "EPSG:4326":
                gdf_eez = gdf_eez.to_crs("EPSG:4326")
                
            print(f"Writing to database table 'india_eez'...")
            gdf_eez.to_postgis("india_eez", engine, if_exists="replace", index=False)
            print(f"Successfully seeded 'india_eez' with {len(gdf_eez)} records.")
        else:
            print(f"Skipping EEZ: file not found at {eez_path}")
            
        # ----------------------------------------------------
        # 2. Seed Marine Protected Areas (WDPA Shapefiles)
        # ----------------------------------------------------
        wdpa_dir = Path("data/boundaries/protect_water_bodies")
        parts = [
            "WDPA_WDOECM_Aug2026_Public_IND_shp_0", 
            "WDPA_WDOECM_Aug2026_Public_IND_shp_1", 
            "WDPA_WDOECM_Aug2026_Public_IND_shp_2"
        ]
        
        gdfs = []
        for part in parts:
            part_path = wdpa_dir / part / "WDPA_WDOECM_Aug2026_Public_IND_shp-polygons.shp"
            if part_path.exists():
                print(f"Loading WDPA shapefile part: {part_path.parent.name}...")
                part_gdf = gpd.read_file(part_path)
                gdfs.append(part_gdf)
                
        if gdfs:
            print("Combining and filtering Marine Protected Areas...")
            combined_wdpa = gpd.GeoDataFrame(pd.concat(gdfs, ignore_index=True), crs=gdfs[0].crs)
            
            # Filter for Marine Protected Areas (either GIS marine area or Reported marine area > 0)
            marine_gdf = combined_wdpa[
                (combined_wdpa['GIS_M_AREA'] > 0.0) | 
                (combined_wdpa['REP_M_AREA'] > 0.0)
            ].copy()
            
            # Project to WGS84 EPSG:4326
            if marine_gdf.crs != "EPSG:4326":
                marine_gdf = marine_gdf.to_crs("EPSG:4326")
                
            print(f"Writing to database table 'marine_protected_areas'...")
            marine_gdf.to_postgis("marine_protected_areas", engine, if_exists="replace", index=False)
            print(f"Successfully seeded 'marine_protected_areas' with {len(marine_gdf)} marine records.")
        else:
            print("Skipping MPAs: no WDPA shapefile parts found in protect_water_bodies.")
            
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_boundaries()
