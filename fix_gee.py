with open("backend/app/api/services/gee_service.py", "r") as f:
    content = f.read()

# Fix the missing project ID in ee.Initialize()
content = content.replace("ee.Initialize()", "ee.Initialize(project='stately-winter-461407-c7')")

with open("backend/app/api/services/gee_service.py", "w") as f:
    f.write(content)

with open("backend/app/api/services/marine_forecast.py", "r") as f:
    content = f.read()

# Reduce INCOIS timeout to 3 seconds
content = content.replace("res_chl = future.result(timeout=15.0)", "res_chl = future.result(timeout=3.0)")
content = content.replace("INCOIS fetch timed out (15s strict limit)", "INCOIS fetch timed out (3s strict limit)")

with open("backend/app/api/services/marine_forecast.py", "w") as f:
    f.write(content)

print("Applied fixes successfully!")
