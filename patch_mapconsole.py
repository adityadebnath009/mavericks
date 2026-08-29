import re
with open("frontend/src/components/map/MapConsole.jsx", "r") as f:
    content = f.read()

# Fix WMS tile layer URLs (sst and chl) to use www
content = content.replace(
    "'https://incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms",
    "'https://www.incois.gov.in/geoserver/PFZ-TUNA-SST-CHL/wms"
)

# Fix popup metrics extraction to handle nested JSON
old_popup = """              const sst = metrics.sst_c != null ? `${Number(metrics.sst_c).toFixed(1)}°C` : (metrics.sst != null ? `${Number(metrics.sst).toFixed(1)}°C` : '28.4°C');
              const chl = metrics.chl_mg_m3 != null ? `${Number(metrics.chl_mg_m3).toFixed(2)} mg/m³` : (metrics.chlorophyll != null ? `${Number(metrics.chlorophyll).toFixed(2)} mg/m³` : '0.45 mg/m³');
              const wind = metrics.wind_speed_kmh != null ? `${Number(metrics.wind_speed_kmh).toFixed(1)} km/h` : '18.5 km/h';
              const curr = metrics.current_speed_ms != null ? `${Number(metrics.current_speed_ms).toFixed(2)} m/s` : '0.35 m/s';
              const wave = metrics.wave_height_m != null ? `${Number(metrics.wave_height_m).toFixed(2)} m` : '1.20 m';"""

new_popup = """              const getVal = (m, key1, key2) => {
                const v = m[key1] ?? m[key2];
                if (v && typeof v === 'object' && v.value != null) return Number(v.value);
                if (v != null && typeof v !== 'object') return Number(v);
                return null;
              };
              
              const vSst = getVal(metrics, 'sst', 'sst_c');
              const vChl = getVal(metrics, 'chlorophyll', 'chl_mg_m3');
              const vWind = getVal(metrics, 'wind_speed', 'wind_speed_kmh');
              const vCurr = getVal(metrics, 'current_speed', 'current_speed_ms');
              const vWave = getVal(metrics, 'wave_height', 'wave_height_m');
              
              const sst = vSst != null ? `${vSst.toFixed(1)}°C` : 'N/A';
              const chl = vChl != null ? `${vChl.toFixed(2)} mg/m³` : 'N/A';
              const wind = vWind != null ? `${vWind.toFixed(1)} km/h` : 'N/A';
              const curr = vCurr != null ? `${vCurr.toFixed(2)} m/s` : 'N/A';
              const wave = vWave != null ? `${vWave.toFixed(2)} m` : 'N/A';"""

content = content.replace(old_popup, new_popup)

with open("frontend/src/components/map/MapConsole.jsx", "w") as f:
    f.write(content)
