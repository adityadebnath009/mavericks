def generate_segments(snapshots, route_coords):
    segments = []
    if not snapshots: return []
    current_risk = snapshots[0]["risk"]
    current_seg = [route_coords[0]]
    for i in range(1, len(snapshots)):
        snap = snapshots[i]
        if snap["risk"] == current_risk:
            current_seg.append(route_coords[i])
        else:
            segments.append({"risk": current_risk, "coordinates": current_seg})
            current_risk = snap["risk"]
            current_seg = [route_coords[i-1], route_coords[i]]
    if current_seg:
        segments.append({"risk": current_risk, "coordinates": current_seg})
    return segments
