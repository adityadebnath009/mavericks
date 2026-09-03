import pytest
import os
import time
import pickle
from unittest.mock import patch
from app.api.services.incois_resolver import IncoisDatasetResolver
from app.core.exceptions import DataUnavailableError

def test_swr_routing_rejects_stale():
    # Setup stale cache
    native_lat, native_lon, day = 15.0, 75.0, 1
    ww3_cycle, curr_cycle = "OLD_WW3", "OLD_CURR"
    ww3_file = os.path.join(IncoisDatasetResolver.CACHE_DIR, "ww3", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_{ww3_cycle}.pkl")
    os.makedirs(os.path.dirname(ww3_file), exist_ok=True)
    with open(ww3_file, "wb") as f:
        pickle.dump({"data": [{"hs": 1.0}], "metadata": {"forecast_cycle": ww3_cycle, "cached_at": time.time()}}, f)
        
    curr_file = os.path.join(IncoisDatasetResolver.CACHE_DIR, "currents", f"lat_{native_lat}_lon_{native_lon}_day_{day}_cycle_{curr_cycle}.pkl")
    os.makedirs(os.path.dirname(curr_file), exist_ok=True)
    with open(curr_file, "wb") as f:
        pickle.dump({"data": [{"u_m_s": 1.0}], "metadata": {"forecast_cycle": curr_cycle, "cached_at": time.time()}}, f)

    with patch.object(IncoisDatasetResolver, "get_ww3_url", return_value="NEW_WW3_URL"):
        with patch.object(IncoisDatasetResolver, "get_currents_url", return_value="NEW_CURR_URL"):
            with patch.object(IncoisDatasetResolver, "_extract_forecast_cycle", return_value="NEW_CYCLE"):
                with patch.object(IncoisDatasetResolver, "_fetch_remote", side_effect=DataUnavailableError("INCOIS Down")):
                    with pytest.raises(DataUnavailableError):
                        IncoisDatasetResolver.resolve_latest_forecast(native_lat, native_lon, day, purpose="routing")

def test_swr_visualization_serves_stale():
    native_lat, native_lon, day = 15.0, 75.0, 1
    with patch.object(IncoisDatasetResolver, "get_ww3_url", return_value="NEW_WW3_URL"):
        with patch.object(IncoisDatasetResolver, "get_currents_url", return_value="NEW_CURR_URL"):
            with patch.object(IncoisDatasetResolver, "_extract_forecast_cycle", return_value="NEW_CYCLE"):
                with patch.object(IncoisDatasetResolver, "_fetch_remote", side_effect=DataUnavailableError("INCOIS Down")):
                    res_w, res_c = IncoisDatasetResolver.resolve_latest_forecast(native_lat, native_lon, day, purpose="visualization")
                    assert res_w.records[0]["hs"] == 1.0
                    assert res_w.provenance["stale_fallback"] is True
                    assert res_c.records[0]["u_m_s"] == 1.0
                    assert res_c.provenance["stale_fallback"] is True
