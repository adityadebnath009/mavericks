import os
import geopandas as gpd
from sqlalchemy import create_engine

# Database Connection Settings
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/orca_marine")

def seed_boundaries():
    print("Initializing Database connection...")
    try:
        # Create SQLAlchemy spatial connection engine
        engine = create_engine(DATABASE_URL)
        
        # Paths to boundary GeoJSON files
        boundaries_to_seed = {
            "india_eez": "data/boundaries/india_eez.geojson",
            "marine_protected_areas": "data/boundaries/marine_protected_areas.geojson",
        }
        
        for table_name, filepath in boundaries_to_seed.items():
            if os.path.exists(filepath):
                print(f"Reading spatial data from {filepath}...")
                # Read spatial vector file into GeoDataFrame
                gdf = gpd.read_file(filepath)
                
                # Verify spatial projection is EPSG:4326 (WGS84 lat/lon coordinates)
                if gdf.crs != "EPSG:4326":
                    gdf = gdf.to_crs("EPSG:4326")
                
                print(f"Writing to database table '{table_name}'...")
                # Write to database (PostGIS geometry coordinates are written automatically by GeoPandas)
                gdf.to_postgis(table_name, engine, if_exists="replace", index=False)
                print(f"Successfully seeded '{table_name}'.")
            else:
                print(f"Skipping {table_name}: file not found at {filepath}")
                
    except Exception as e:
        print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_boundaries()
