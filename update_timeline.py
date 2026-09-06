with open("frontend/src/components/timeline/WeatherTimelinePanel.jsx", "r") as f:
    content = f.read()

content = content.replace("domain={[0, 7]}", "domain={[0, 100]}")
content = content.replace("`${value} / 7`", "`${value} / 100`")
content = content.replace("val >= 6 ? '#FF5C5C' : val >= 4 ? '#FFB547' : '#18C7A0'", "val >= 51 ? '#FF5C5C' : val >= 21 ? '#FFB547' : '#18C7A0'")
content = content.replace("val >= 6", "val >= 51")
content = content.replace("val >= 4", "val >= 21")

with open("frontend/src/components/timeline/WeatherTimelinePanel.jsx", "w") as f:
    f.write(content)
