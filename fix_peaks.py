import sys
import os

with open('backend/app/api/endpoints/safety.py', 'r') as f:
    content = f.read()

# We need to inject the 3-day peaks into get_safety_assessment
injection = """
    engine = OrcaBsiEngine()
    
    orca_result = engine.evaluate(snapshot, vessel)
    
    # Generate 3-day peaks
    daily_peaks = {}
    for d in [1, 2, 3]:
        d_date = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=datetime.timezone.utc)
        if d > 1:
            d_date += datetime.timedelta(days=d-1)
        
        peak_score = 0
        peak_rating = "SAFE"
        for h in range(0, 24, 3):
            h_date = d_date.replace(hour=h)
            h_snap = MarineForecastService.get_environment(lat, lon, h_date)
            h_res = engine.evaluate(h_snap, vessel)
            if h_res["severity_score"] > peak_score:
                peak_score = h_res["severity_score"]
                
        if peak_score >= 76:
            peak_rating = "EXTREME"
        elif peak_score >= 51:
            peak_rating = "HIGH"
        elif peak_score >= 21:
            peak_rating = "MODERATE"
            
        daily_peaks[f"day{d}"] = {"score": peak_score, "rating": peak_rating}
"""

content = content.replace("    engine = OrcaBsiEngine()\n    \n    orca_result = engine.evaluate(snapshot, vessel)", injection)

content = content.replace('"raw_metrics": {', '"daily_peaks": daily_peaks,\n        "raw_metrics": {')

with open('backend/app/api/endpoints/safety.py', 'w') as f:
    f.write(content)
