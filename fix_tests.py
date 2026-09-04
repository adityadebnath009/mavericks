import os
import re

def process_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Regex for positional args:
    # PFZRoutingService.calculate_optimal_route(15.0, 75.0, 15.2, 75.0, 3.0, 10.0, "2026-08-26T00:00:00")
    # Groups: 1-4 (coords), 5 (beam), 6 (speed), 7 (time)
    # Be careful with whitespace and string quotes.
    pattern_pos = r'PFZRoutingService\.calculate_optimal_route\s*\(\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([^,]+),\s*([\d\.]+),\s*([\d\.]+),\s*("[^"]+")\s*\)'
    
    def repl_pos(match):
        lat1, lon1, lat2, lon2, beam, speed, time = match.groups()
        return f'PFZRoutingService.calculate_optimal_route({lat1}, {lon1}, {lat2}, {lon2}, VesselProfile(length_m=20.0, beam_m={beam}, cruising_speed_kn={speed}), {time})'

    new_content = re.sub(pattern_pos, repl_pos, content)

    # Regex for kwargs:
    # beam_m=X, cruising_speed_kn=Y
    pattern_kwargs = r'beam_m\s*=\s*([\d\.]+)\s*,\s*cruising_speed_kn\s*=\s*([\d\.]+)'
    
    def repl_kwargs(match):
        beam, speed = match.groups()
        return f'vessel_profile=VesselProfile(length_m=20.0, beam_m={beam}, cruising_speed_kn={speed})'

    new_content = re.sub(pattern_kwargs, repl_kwargs, new_content)

    if new_content != content:
        # Need to ensure VesselProfile is imported
        if 'VesselProfile' not in new_content[:500] and 'VesselProfile' in new_content:
            new_content = "from app.api.services.orca_bsi_engine import VesselProfile\n" + new_content
        with open(filepath, 'w') as f:
            f.write(new_content)
        print(f"Updated {filepath}")

import glob
for f in glob.glob("backend/tests/*.py"):
    process_file(f)
