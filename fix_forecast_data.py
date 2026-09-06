with open('backend/app/api/services/forecast_data.py', 'r') as f:
    content = f.read()

# Restore the numpy logic that was accidentally deleted
missing_code = """        import numpy as np
        spr_rad = np.radians(spr_deg)
        ss = float(np.sqrt(2.0 * (1.0 - np.cos(spr_rad))))
        
        bsi = 0"""

if "bsi = 0" in content and "import numpy as np" not in content:
    content = content.replace("        bsi = 0", missing_code)
    with open('backend/app/api/services/forecast_data.py', 'w') as f:
        f.write(content)
        print("Restored ss and numpy to forecast_data.py")
