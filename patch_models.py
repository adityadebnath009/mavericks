import re
with open("backend/app/db/models.py", "r") as f:
    content = f.read()

new_model = """
from sqlalchemy import JSON

class PFZAdvisory(Base):
    \"\"\"
    SQLAlchemy model representing a cached daily Potential Fishing Zone advisory.
    \"\"\"
    __tablename__ = "pfz_advisories"

    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(String, index=True, nullable=False) # e.g. '2026-08-29'
    valid_upto = Column(String, nullable=True) # Usually forecast_date + 48 hours
    fetched_at = Column(DateTime(timezone=True), server_default=func.now())
    content_json = Column(JSON, nullable=False) # The actual GeoJSON FeatureCollection
    status = Column(String, default="active", index=True) # 'active' or 'previous'
    source_url = Column(String, nullable=True)
"""

if "PFZAdvisory" not in content:
    content = content + new_model
    with open("backend/app/db/models.py", "w") as f:
        f.write(content)
