
import pytest
import respx
from httpx import Response
from pyetrade.alerts import ETradeAlertsAsync

@pytest.mark.asyncio
class TestETradeAlertsAsync:
    
    @respx.mock
    async def test_list_alerts(self):
        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=True)
        response_data = {"AlertsResponse": {"Alert": []}}
        
        url = "https://apisb.etrade.com/v1/user/alerts.json"
        
        respx.get(url).mock(return_value=Response(200, json=response_data))
        
        result = await alerts.list_alerts(resp_format="json")
        assert result == response_data

    @respx.mock
    async def test_list_alert_details(self):
        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=True)
        alert_id = 123
        response_data = {"AlertDetailsResponse": {"id": 123}}
        
        url = f"https://apisb.etrade.com/v1/user/alerts.json/{alert_id}"
        
        respx.get(url).mock(return_value=Response(200, json=response_data))
        
        result = await alerts.list_alert_details(alert_id, resp_format="json")
        assert result == response_data
        
    @respx.mock
    async def test_delete_alert(self):
        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=True)
        alert_id = 123
        response_data = {"DeleteAlertResponse": {"id": 123}}
        
        url = f"https://apisb.etrade.com/v1/user/alerts.json/{alert_id}"
        
        respx.delete(url).mock(return_value=Response(200, json=response_data))
        
        result = await alerts.delete_alert(alert_id, resp_format="json")
        assert result == response_data
