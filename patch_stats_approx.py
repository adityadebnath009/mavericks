with open("backend/bsi_statistical_analysis.py", "r") as f:
    content = f.read()

content = content.replace("env_sev = (base_hs_sev + mu_sev + 0.0 + 0.0) / 4.0", "env_sev = np.clip(base_hs_sev + mu_sev, 0, 1.0)")

with open("backend/bsi_statistical_analysis.py", "w") as f:
    f.write(content)
