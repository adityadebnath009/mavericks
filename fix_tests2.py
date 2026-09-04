import os
import re
import shutil

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    pattern_pos = r'PFZRoutingService\.calculate_optimal_route\s*\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([\d\.]+),\s*([\d\.]+),\s*("[^"]+")\s*\)'
    
    def repl_pos(match):
        lat1, lon1, lat2, lon2, beam, speed, time = match.groups()
        return f'PFZRoutingService.calculate_optimal_route({lat1}, {lon1}, {lat2}, {lon2}, VesselProfile(length_m=20.0, beam_m={beam}, cruising_speed_kn={speed}), {time})'

    new_content = re.sub(pattern_pos, repl_pos, content)

    pattern_kwargs = r'beam_m\s*=\s*([\d\.]+)\s*,\s*cruising_speed_kn\s*=\s*([\d\.]+)'
    
    def repl_kwargs(match):
        beam, speed = match.groups()
        return f'vessel_profile=VesselProfile(length_m=20.0, beam_m={beam}, cruising_speed_kn={speed})'

    new_content = re.sub(pattern_kwargs, repl_kwargs, new_content)

    if new_content != content:
        if 'VesselProfile' not in new_content[:500] and 'VesselProfile' in new_content:
            new_content = "from app.api.services.orca_bsi_engine import VesselProfile\n" + new_content
        
        # write to tmp file and mv
        tmp_path = filepath + ".tmp"
        with open(tmp_path, 'w') as f:
            f.write(new_content)
        os.rename(tmp_path, filepath)
        print(f"Updated {filepath}")

import glob
for f in glob.glob("backend/tests/*.py"):
    process_file(f)
