import os

f = "backend/app/api/services/pfz_routing.py"
with open(f, 'r') as fh: c = fh.read()

c = c.replace(
    'current_seg = [route_coords[i-1], route_coords[i]]',
    'current_seg = [[route_coords[i-1]["lat"], route_coords[i-1]["lon"]], [route_coords[i]["lat"], route_coords[i]["lon"]]]'
)

with open(f, 'w') as fh: fh.write(c)
