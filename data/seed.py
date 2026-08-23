import os
import sys
from pathlib import Path
import geopandas as gpd
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
        
        # Paths to spatial files
        boundaries_to_seed = {
            "india_eez": "data/boundaries/eez_v12_lowres.gpkg",
            "marine_protected_areas": "data/boundaries/marine_protected_areas.geojson",
        }
        
        for table_name, filepath in boundaries_to_seed.items():
            if os.path.exists(filepath):
                print(f"Reading spatial data from {filepath}...")
                gdf = gpd.read_file(filepath)
                
                # If we are loading the global EEZ file, filter to keep only India's waters
                if table_name == "india_eez":
                    print("Filtering global EEZ database for India...")
                    # Sovereign names are stored in "SOVEREIGN1" or "SOVEREIGNTY"
                    col_name = "SOVEREIGN1" if "SOVEREIGN1" in gdf.columns else "SOVEREIGNTY"
                    gdf = gdf[gdf[col_name] == "India"]
                
                # Verify spatial projection is EPSG:4326 (WGS84 lat/lon coordinates)
                if gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")
                
                print(f"Writing to database table '{table_name}'...")
                # Write to database (PostGIS geometry coordinates are written automatically by GeoPandas)
                gdf.to_postgis(table_name, engine, if_exists="replace", index=False)
                print(f"Successfully seeded '{table_name}' with {len(gdf)} geometry records.")
            else:
                print(f"Skipping {table_name}: file not found at {filepath}")
                
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_boundaries()
