# ORCA Marine Portal

Intelligent spatial decision support platform for Potential Fishing Zones (PFZs), weather safety routing, and boundary geofencing, powered by FastAPI and React.

---

## 🚀 Getting Started

### 1. Database Setup
Create a PostgreSQL database with PostGIS enabled (e.g. using Neon serverless postgres):
```sql
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 2. Backend Setup (FastAPI)
Navigate to the backend directory, activate the virtual environment, install requirements, and run the server:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```
Interactive docs will be live at `http://localhost:8000/docs`.

### 3. Frontend Setup (React + MapLibre)
Navigate to the frontend directory, install node modules, and run the development server:
```bash
cd frontend
npm install
npm run dev
```
Web app will be live at `http://localhost:5173`.
