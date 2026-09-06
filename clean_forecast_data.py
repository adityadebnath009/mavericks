import sys

with open('backend/app/api/services/forecast_data.py', 'r') as f:
    content = f.read()

# Replace the BSICalculator import and calculation
old_code = """        # Convert directional spread from degrees to ratio for BSI calculation
        import numpy as np
        spr_rad = np.radians(spr_deg)
        ss = float(np.sqrt(2.0 * (1.0 - np.cos(spr_rad))))
        
        from app.api.services.bsi_calculator import BSICalculator
        bsi = BSICalculator.calculate_bsi(
            Ss=stp,
            Hs=hs,
            ss=ss,
            Hsea_initial=hsea_i,
            Hsea_final=hsea_f
        )"""

new_code = "        bsi = 0"

if old_code in content:
    content = content.replace(old_code, new_code)
    with open('backend/app/api/services/forecast_data.py', 'w') as f:
        f.write(content)
        print("Patched successfully!")
else:
    print("Could not find the block. Let me just replace the BSICalculator import.")
    content = content.replace("from app.api.services.bsi_calculator import BSICalculator", "")
    content = content.replace("bsi = BSICalculator.calculate_bsi(", "bsi = 0 #")
    with open('backend/app/api/services/forecast_data.py', 'w') as f:
        f.write(content)
