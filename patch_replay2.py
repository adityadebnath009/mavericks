with open("backend/run_historical_replay.py", "r") as f:
    content = f.read()

content = content.replace("'../data/indian_coastal_marine_dataset_2020_2025.csv'", "'data/indian_coastal_marine_dataset_2020_2025.csv'")

with open("backend/run_historical_replay.py", "w") as f:
    f.write(content)
