with open("/Users/adityadebnath/.gemini/antigravity/brain/5bba35e8-b01b-4155-8daf-4834890a1ea4/bsi_implementation_plan.md", "r") as f:
    content = f.read()

old_text = """**BSI v2.3 (Route Intelligence)**
*   Implement Route BSI profiling (evaluating conditions across space and ETA).
*   Expose aggregate route statistics (current BSI, max BSI, peak ETA, duration above threshold)."""

new_text = """**BSI v2.3 (Route Intelligence & Heatmap UI)**
*   Implement Route BSI profiling (evaluating conditions across space and ETA).
*   Expose aggregate route statistics (current BSI, max BSI, peak ETA, duration above threshold).
*   Implement the Dynamic BSI Heatmap (vectorized grid calculation without N+1 Open-Meteo API calls)."""

content = content.replace(old_text, new_text)

with open("/Users/adityadebnath/.gemini/antigravity/brain/5bba35e8-b01b-4155-8daf-4834890a1ea4/bsi_implementation_plan.md", "w") as f:
    f.write(content)
