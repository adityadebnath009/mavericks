from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean
from sqlalchemy.sql import func
from app.db.session import Base

class Vessel(Base):
    """
    SQLAlchemy model representing a fishing vessel or boat.
    """
    __tablename__ = "vessels"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    registration_number = Column(String, unique=True, index=True, nullable=False)
    owner_name = Column(String, nullable=True)
    
    # Live tracking coordinates
    last_latitude = Column(Float, nullable=True)
    last_longitude = Column(Float, nullable=True)
    
    # Status indicators
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class GeofenceZone(Base):
    """
    SQLAlchemy model representing restricted or safety boundary zones.
    Note: For precise spatial geometry operations, you can use GeoAlchemy2's Geometry column type.
    However, for simple bounding checks or standard GIS data, storing GeoJSON strings is also supported.
    """
    __tablename__ = "geofence_zones"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, unique=True)
    zone_type = Column(String, nullable=False) # e.g., 'IMBL', 'MPA', 'Restricted'
    
    # Boundary warning parameters
    warning_buffer_km = Column(Float, default=5.0)
    is_active = Column(Boolean, default=True)
    
    # Optional metadata or descriptions
    description = Column(String, nullable=True)
