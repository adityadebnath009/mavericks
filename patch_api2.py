with open("frontend/src/services/api.js", "r") as f:
    content = f.read()

content = content.replace("if (data && Array.isArray(data)) return data;", "if (data && Array.isArray(data.landing_centers)) return data.landing_centers;")

with open("frontend/src/services/api.js", "w") as f:
    f.write(content)
