import re

f = "backend/app/api/endpoints/telemetry.py"
with open(f, 'r') as fh: c = fh.read()

bad_chunk = """
        prov = getattr(env, 'provenance', {})
        provenance = {
            "sst": {"source": prov.get("sst_c").source if "sst_c" in prov else "missing", "fallback": prov.get("sst_c").fallback if "sst_c" in prov else True},
            "chl": {"source": prov.get("chl_mg_m3").source if "chl_mg_m3" in prov else "missing", "fallback": prov.get("chl_mg_m3").fallback if "chl_mg_m3" in prov else True},
            "wave": {"source": prov.get("wave_height_m").source if "wave_height_m" in prov else "open-meteo"},
            "wind": {"source": prov.get("wind_speed_ms").source if "wind_speed_ms" in prov else "open-meteo"}
        } if getattr(env, 'sst_c', None) else {"source": "missing"},
            "chl": {"source": "mock", "cached": False, "fallback": True} if getattr(env, 'chl_mg_m3', None) else {"source": "missing"},
            "wind": {"source": "gfs", "cached": True},
            "wave": {"source": "ww3", "cached": True}
        }
"""

good_chunk = """
        prov = getattr(env, 'provenance', {})
        provenance = {
            "sst": {"source": prov.get("sst_c").source if "sst_c" in prov else "missing", "fallback": prov.get("sst_c").fallback if "sst_c" in prov else True},
            "chl": {"source": prov.get("chl_mg_m3").source if "chl_mg_m3" in prov else "missing", "fallback": prov.get("chl_mg_m3").fallback if "chl_mg_m3" in prov else True},
            "wave": {"source": prov.get("wave_height_m").source if "wave_height_m" in prov else "open-meteo"},
            "wind": {"source": prov.get("wind_speed_ms").source if "wind_speed_ms" in prov else "open-meteo"}
        }
"""

c = c.replace(bad_chunk.strip("\n"), good_chunk.strip("\n"))

with open(f, 'w') as fh: fh.write(c)
