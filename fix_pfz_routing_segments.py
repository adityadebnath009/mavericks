import os

f = "backend/app/api/services/pfz_routing.py"
with open(f, 'r') as fh: c = fh.read()

# I need to change:
# current_seg = [route_coords[0]]
# to
# current_seg = [[route_coords[0]["lat"], route_coords[0]["lon"]]]
# and
# current_seg.append(route_coords[i])
# to
# current_seg.append([route_coords[i]["lat"], route_coords[i]["lon"]])
# and
# segments.append({"risk": current_risk, "coordinates": current_seg})
# to
# segments.append({"segment_index": len(segments), "risk": current_risk, "coordinates": current_seg})

c = c.replace('current_seg = [route_coords[0]]', 'current_seg = [[route_coords[0]["lat"], route_coords[0]["lon"]]]')
c = c.replace('current_seg.append(route_coords[i])', 'current_seg.append([route_coords[i]["lat"], route_coords[i]["lon"]])')
c = c.replace('segments.append({"risk": current_risk, "coordinates": current_seg})', 'segments.append({"segment_index": len(segments), "risk": current_risk, "coordinates": current_seg})')
# also the final append outside the loop
c = c.replace('segments.append({"risk": current_risk, "coordinates": current_seg})', 'segments.append({"segment_index": len(segments), "risk": current_risk, "coordinates": current_seg})')

with open(f, 'w') as fh: fh.write(c)

