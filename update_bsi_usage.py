import os

for fpath in ["backend/app/api/services/pfz_intelligence.py", "backend/app/api/services/forecast_data.py"]:
    if not os.path.exists(fpath): continue
    with open(fpath, "r") as f:
        content = f.read()

    # Just do a naive replace for BSICalculator usages if they exist, or don't fail
    if "BSICalculator" in content:
        content = content.replace("from app.api.services.bsi_calculator import BSICalculator", "from app.api.services.orca_bsi_engine import OrcaBsiEngine, VesselProfile\nfrom app.api.services.marine_forecast import MarineForecastService")
        content = content.replace("bsi = BSICalculator.calculate_bsi(stp, hs, spr, hsea_initial, hsea_final)", "bsi = 0 # Replaced by Orca")
        content = content.replace("bsi = BSICalculator.calculate_bsi(", "bsi = 0 #")
        with open(fpath, "w") as f:
            f.write(content)

