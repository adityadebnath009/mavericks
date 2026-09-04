import os
import glob
import re

test_files = glob.glob("backend/tests/**/*.py", recursive=True)

for file in test_files:
    with open(file, 'r') as f:
        content = f.read()
    
    if "PFZRoutingService.calculate_optimal_route" in content:
        # We need to replace:
        # length_m=X, beam_m=Y, cruising_speed_kn=Z
        # with:
        # vessel_profile=VesselProfile(length_m=X, beam_m=Y, cruising_speed_kn=Z)
        
        # Also need to make sure VesselProfile is imported
        if "from app.api.services.orca_bsi_engine import VesselProfile" not in content and "OrcaBsiEngine" not in content:
            content = "from app.api.services.orca_bsi_engine import VesselProfile\n" + content
            
        # Regex to find calculate_optimal_route calls and group the arguments
        # It's tricky to do with regex because it might be multi-line.
        pass

