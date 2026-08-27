from app.api.services.incois_geoserver import INCOISGeoServerClient

def test_get_capabilities():
    """
    Validates capabilities metadata parsing, ensuring fallback values
    exist and are correctly shaped even if connection fails.
    """
    res = INCOISGeoServerClient.get_capabilities()
    assert res is not None
    assert "source" in res
    assert "status" in res
    assert "layers" in res
    assert len(res["layers"]) >= 3
    
    # Assert presence of required layers
    layer_names = [l["name"] for l in res["layers"]]
    assert any("sst" in name.lower() for name in layer_names)
    assert any("chl" in name.lower() for name in layer_names)
    assert any("pfzlines" in name.lower() for name in layer_names)

def test_get_feature_info():
    """
    Tests GetFeatureInfo point inspector behavior on standard coordinates.
    """
    # Test point in the Arabian Sea
    lat = 15.0
    lon = 72.0
    
    # Query SST
    res = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:sst")
    assert res is not None
    assert "status" in res
    assert res["status"] in ["success", "no_data", "error"]
    if res["status"] == "success":
        assert "value" in res
        assert isinstance(res["value"], float)
        assert 0.0 <= res["value"] <= 45.0  # SST bounds
        
    # Query CHL
    res_chl = INCOISGeoServerClient.get_feature_info(lat, lon, "PFZ-TUNA-SST-CHL:chl")
    assert res_chl is not None
    assert "status" in res_chl
    assert res_chl["status"] in ["success", "no_data", "error"]
    if res_chl["status"] == "success":
        assert "value" in res_chl
        assert isinstance(res_chl["value"], float)
        assert 0.0 <= res_chl["value"] <= 15.0  # Chlorophyll bounds

def test_get_pfz_lines_wfs():
    """
    Validates WFS retrieval of Potential Fishing Zone advisory lines.
    """
    res = INCOISGeoServerClient.get_pfz_lines_wfs()
    assert res is not None
    assert "type" in res
    assert res["type"] == "FeatureCollection"
    assert "features" in res
    assert isinstance(res["features"], list)
