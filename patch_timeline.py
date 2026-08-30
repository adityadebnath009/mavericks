with open("frontend/src/components/timeline/WeatherTimelinePanel.jsx", "r") as f:
    content = f.read()

# Replace {forecastTimeline.map(  with {(forecastTimeline || []).map(
content = content.replace("{forecastTimeline.map((entry, index) => (", "{(forecastTimeline || []).map((entry, index) => (")

# Also replace data={forecastTimeline} with data={forecastTimeline || []}
content = content.replace("data={forecastTimeline}", "data={forecastTimeline || []}")

with open("frontend/src/components/timeline/WeatherTimelinePanel.jsx", "w") as f:
    f.write(content)
