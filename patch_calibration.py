with open("backend/app/api/services/orca_bsi_engine.py", "r") as f:
    content = f.read()

old_env = """        env_severity_raw = (base_hs_severity + steepness_data["severity"] + rapid_dev_data["severity"] + crossing_severity) / 4.0"""

new_env = """        # Environmental Severity is strictly additive, capped at 1.0. 
        # Missing hazards do not artificially dilute the score.
        env_severity_raw = min(base_hs_severity + steepness_data["severity"] + rapid_dev_data["severity"] + crossing_severity, 1.0)"""

content = content.replace(old_env, new_env)

with open("backend/app/api/services/orca_bsi_engine.py", "w") as f:
    f.write(content)
