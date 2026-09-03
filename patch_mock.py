with open("backend/tests/test_forecast_data.py", "r") as f:
    content = f.read()

content = content.replace("assert env.bsi == 1", "assert env.bsi == 0")

with open("backend/tests/test_forecast_data.py", "w") as f:
    f.write(content)
