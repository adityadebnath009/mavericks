async function test() {
  const res = await fetch('http://127.0.0.1:8000/api/incois/vector-grid?day=1&hour=12');
  const data = await res.json();
  const toGeoJSON = (arr) => ({
    type: 'FeatureCollection',
    features: (arr || []).map(p => ({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [p.lon, p.lat] },
      properties: { ...p }
    }))
  });
  const windGeojson = toGeoJSON(data.wind);
  console.log('Wind features count:', windGeojson.features.length);
  if (windGeojson.features.length > 0) {
    console.log('First feature:', JSON.stringify(windGeojson.features[0]));
  }
}
test();
