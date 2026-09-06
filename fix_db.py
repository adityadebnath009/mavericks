import os
import psycopg2
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))
from app.api.services.reporting import ReportingService

conn = ReportingService._connect()
with conn.cursor() as cur:
    cur.execute("DROP TABLE IF EXISTS marine_safety_corpus;")
    cur.execute("""
    CREATE TABLE marine_safety_corpus (
        id SERIAL PRIMARY KEY,
        source VARCHAR(255),
        clause_id VARCHAR(100),
        text TEXT,
        embedding vector(3072)
    );
    """)
    print("Table marine_safety_corpus recreated with vector(3072)!")
conn.commit()
conn.close()
