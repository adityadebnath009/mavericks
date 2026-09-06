import re

with open("backend/app/api/services/route_bsi_profiler.py", "r") as f:
    content = f.read()

# Replace max_bsi with max_severity
old_code = """            # Aggregation logic
            sum_severity += node_severity
            if node_bsi > max_bsi or (node_bsi == max_bsi and node_severity > (evaluated_profile[peak_node]["severity"] if evaluated_profile else 0)):
                max_bsi = node_bsi
                peak_node = node["node_idx"]
                peak_eta = node["eta"]"""

new_code = """            # Aggregation logic
            sum_severity += node_severity
            if node_severity > max_bsi:
                max_bsi = node_severity
                peak_node = node["node_idx"]
                peak_eta = node["eta"]"""

content = content.replace(old_code, new_code)

with open("backend/app/api/services/route_bsi_profiler.py", "w") as f:
    f.write(content)
print("patched profiler")
