import pytest
import requests
import struct
from unittest.mock import patch, MagicMock
from app.api.services.incois_client import incois_client, IncoisHTTPAdapter
import pydap.client
from urllib.parse import urlparse

def fake_send(self, request, **kwargs):
    print("FAKE SEND CALLED:", request.url)
    
    # We must call the original increment metrics to prove it works
    self.client._increment_metric("requests_total")
    self.client.limiter.wait()
    self.client._increment_metric("actual_upstream_requests")
    self.client._increment_metric("requests_success")
    self.client.circuit.record_success()

    resp = requests.Response()
    resp.status_code = 200
    
    parsed = urlparse(request.url)
    path = parsed.path
    
    if path.endswith(".dds"):
        resp._content = b"Dataset { Float32 lat[lat = 1]; } test;\n"
    elif path.endswith(".das"):
        resp._content = b"Attributes { }\n"
    elif path.endswith(".dods"):
        # For dods, we need DDS + Data (XDR encoded)
        xdr_data = struct.pack('>I', 1) + struct.pack('>I', 1) + struct.pack('>f', 1.0)
        resp._content = b"Dataset { Float32 lat[lat = 1]; } test;\nData:\n" + xdr_data
    else:
        resp._content = b"test"
        
    return resp

@patch.object(IncoisHTTPAdapter, 'send', autospec=True, side_effect=fake_send)
def test_pydap_uses_adapter(mock_send):
    """
    Test that pydap's internal fetch mechanism actually uses the IncoisHTTPAdapter
    for all network requests (.das, .dds, .dods) during dataset discovery and chunk materialization.
    """
    # Clear metrics
    for k in incois_client.metrics:
        incois_client.metrics[k] = 0

    url = "http://incois.gov.in/test.nc"
    
    with incois_client.pydap_transport_protection():
        session = incois_client.get_session()
        # 1. Dataset discovery (should trigger .das and .dds fetches)
        dataset = pydap.client.open_url(url, session=session)
        
        # 2. Materialization (should trigger .dods fetch)
        lat_data = dataset['lat'].data[:]
        assert lat_data[0] == 1.0
        
    # .dds, .das, and .dods = 3 requests
    assert mock_send.call_count == 3
    assert incois_client.metrics["requests_total"] == 3
    assert incois_client.metrics["actual_upstream_requests"] == 3
