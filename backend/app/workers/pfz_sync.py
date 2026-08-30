import os
import sys
import logging
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import PFZAdvisory
from app.api.services.incois_geoserver import INCOISGeoServerClient
from app.api.services.pfz_enricher import PFZEnricherService

logger = logging.getLogger(__name__)

def parse_incois_date(geojson: dict) -> str:
    """
    Extracts the 'Year' and 'Julian_day' from the first feature of the INCOIS GeoJSON
    and converts it into an ISO-8601 string (e.g. '2026-08-29').
    """
    if not geojson or not geojson.get("features"):
        return None
        
    first_feature = geojson["features"][0]
    props = first_feature.get("properties", {})
    
    year = props.get("Year")
    julian_day = props.get("Julian_day")
    
    if not year or not julian_day:
        return None
        
    # INCOIS Julian_day might be an integer or a string like '241'
    try:
        dt = datetime.strptime(f"{int(year)}{int(julian_day)}", "%Y%j")
        return dt.strftime("%Y-%m-%d")
    except Exception as e:
        logger.error(f"Failed to parse INCOIS date: {e}")
        return None

def sync_pfz_advisory():
    """
    Worker task that queries INCOIS, checks if a new forecast_date is available,
    and updates the database if it has changed.
    """
    logger.info("Starting PFZ synchronization worker...")
    db: Session = SessionLocal()
    
    try:
        # 1. Fetch raw data from INCOIS
        raw_geojson = INCOISGeoServerClient.get_pfz_lines_wfs()
        if not raw_geojson or not raw_geojson.get("features"):
            logger.warning("Failed to fetch or received empty PFZ data from INCOIS")
            return
            
        # 2. Extract the forecast date
        forecast_date = parse_incois_date(raw_geojson)
        if not forecast_date:
            logger.warning("Could not extract forecast_date from INCOIS payload")
            return
            
        # 3. Check current active advisory in DB
        active_advisory = db.query(PFZAdvisory).filter(PFZAdvisory.status == "active").first()
        
        if active_advisory and active_advisory.forecast_date == forecast_date:
            logger.info(f"PFZ Advisory for {forecast_date} is already active. No changes needed.")
            return
            
        logger.info(f"New PFZ Advisory detected for {forecast_date}. Enriching and storing...")
        
        # 4. Enrich the GeoJSON (add bounds, risk calculations, etc.)
        enriched_geojson = PFZEnricherService.enrich_feature_collection(raw_geojson)
        
        # 5. Mark old advisory as previous
        if active_advisory:
            active_advisory.status = "previous"
            
        # 6. Insert new advisory
        # valid_upto is typically 48 hours from forecast_date based on INCOIS ops
        valid_upto = (datetime.strptime(forecast_date, "%Y-%m-%d") + timedelta(days=2)).strftime("%Y-%m-%d")
        
        new_advisory = PFZAdvisory(
            forecast_date=forecast_date,
            valid_upto=valid_upto,
            content_json=enriched_geojson,
            status="active",
            source_url="https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/ows"
        )
        
        db.add(new_advisory)
        db.commit()
        logger.info(f"Successfully activated new PFZ Advisory for {forecast_date}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error during PFZ synchronization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    sync_pfz_advisory()
