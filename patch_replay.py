with open("backend/run_historical_replay.py", "r") as f:
    content = f.read()

old_path = "'../data/processed/marine_risk_processed.csv'"
new_path = "'../data/indian_coastal_marine_dataset_2020_2025.csv'"

content = content.replace(old_path, new_path)

with open("backend/run_historical_replay.py", "w") as f:
    f.write(content)
