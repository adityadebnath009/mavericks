import pytest
from unittest.mock import patch, MagicMock
from app.api.services.cache_warmer import CacheWarmer
from app.core.exceptions import DataUnavailableError

def test_cache_warmer_initial_state():
    warmer = CacheWarmer()
    assert warmer.state == "NOT_STARTED"
    assert warmer.last_warmed_cycle is None

@patch("app.api.services.cache_warmer.IncoisDatasetResolver")
@patch("app.api.services.cache_warmer.PFZEnricherService.enrich_feature_collection")
@patch("app.api.services.cache_warmer.INCOISGeoServerClient")
def test_warmer_aborts_on_circuit_open(mock_geo, mock_enrich, mock_resolver):
    warmer = CacheWarmer()
    # Mock discover_cycle to throw DataUnavailableError
    warmer._discover_cycle = MagicMock(side_effect=DataUnavailableError("Circuit Open"))
    
    warmer.warm_if_needed()
    
    assert warmer.state == "FAILED"
    assert warmer.last_warmed_cycle is None

@patch("app.api.services.cache_warmer.CacheWarmer._execute_warm_sets")
def test_warmer_idles_on_same_cycle(mock_execute):
    warmer = CacheWarmer()
    warmer._discover_cycle = MagicMock(return_value="20260831_12_20260831_12")
    warmer.last_warmed_cycle = "20260831_12_20260831_12"
    
    warmer.warm_if_needed()
    
    assert warmer.state == "IDLE"
    mock_execute.assert_not_called()

@patch("app.api.services.cache_warmer.CacheWarmer._execute_warm_sets")
def test_warmer_updates_state_on_success(mock_execute):
    warmer = CacheWarmer()
    warmer._discover_cycle = MagicMock(return_value="20260901_12_20260901_12")
    mock_execute.return_value = True
    
    warmer.warm_if_needed()
    
    assert warmer.state == "READY"
    assert warmer.last_warmed_cycle == "20260901_12_20260901_12"
    mock_execute.assert_called_once_with("20260901_12_20260901_12")

@patch("app.api.services.cache_warmer.CacheWarmer._execute_warm_sets")
def test_warmer_preserves_old_cycle_on_partial_failure(mock_execute):
    warmer = CacheWarmer()
    warmer.last_warmed_cycle = "OLD_CYCLE"
    warmer._discover_cycle = MagicMock(return_value="NEW_CYCLE")
    mock_execute.return_value = False
    
    warmer.warm_if_needed()
    
    assert warmer.state == "PARTIAL"
    assert warmer.last_warmed_cycle == "OLD_CYCLE"

@patch("app.api.services.cache_warmer.PFZEnricherService.enrich_feature_collection")
@patch("app.api.services.cache_warmer.INCOISGeoServerClient")
@patch("app.api.services.cache_warmer.IncoisDatasetResolver")
@patch("os.path.exists")
def test_warmer_execute_sets(mock_exists, mock_resolver, mock_geo, mock_enrich):
    mock_enrich.return_value = {
            "enrichment_status": "READY",
            "pfz_cycle": "20260901_12_20260901_12",
            "features": [
                {
                    "geometry": {
                        "type": "MultiLineString",
                        "coordinates": [[[75.0, 15.0], [75.1, 15.1]]]
                    }
                }
            ]
        }
    mock_exists.return_value = True
            
    # Mock os.path.exists to always return True for assertions
    
    
    # Mock PFZ WFS
    mock_geo.get_pfz_lines_wfs.return_value = {
        "features": [
            {
                "geometry": {
                    "type": "MultiLineString", "coordinates": [[[75.0, 15.0], [75.1, 15.1]]]
                }
            }
        ]
    }
    
    mock_resolver.get_cache_paths.return_value = ("ww3_path", "curr_path")
    mock_resolver.CACHE_DIR = "/fake/cache"
    
    # We must patch get_safety_grid to avoid executing it natively
    with patch("app.api.endpoints.safety.get_safety_grid") as mock_grid:
        warmer = CacheWarmer()
        success = warmer._execute_warm_sets("20260901_12_20260901_12")
        
        assert success is True
        # Verify PFZ underlying calls
        # Verify Grid calls (day 1..3, hour 0,6,12,18 = 12 calls)
        assert mock_grid.call_count == 12
        # Verify Vector Grid call
        mock_resolver.resolve_vector_grid.assert_called_once_with(day=1, hour=12)
