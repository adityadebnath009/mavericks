with open("backend/run_historical_replay.py", "r") as f:
    content = f.read()

# Update path to the Downloads folder
content = content.replace(
    "'data/indian_coastal_marine_dataset_2020_2025.csv'", 
    "'/Users/adityadebnath/Downloads/indian_coastal_marine_dataset_2020_2025 (2).csv'"
)

# Increase sample size to 100,000 for a massive statistical sample
content = content.replace("sample_size = min(10000, len(df))", "sample_size = min(100000, len(df))")

with open("backend/run_historical_replay.py", "w") as f:
    f.write(content)
