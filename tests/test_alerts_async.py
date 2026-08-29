import pytest
from pyetrade.async_api.alerts import ETradeAlerts

pytestmark = pytest.mark.httpx2(assert_all_called=False)


@pytest.mark.asyncio
class TestETradeAlerts:

    async def test_list_alerts(self, httpx2_mock):
        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=True)
        response_data = {"AlertsResponse": {"Alert": []}}

        url = "https://apisb.etrade.com/v1/user/alerts.json"

        httpx2_mock.get(url).respond(200, json=response_data)

        result = await alerts.list_alerts(resp_format="json")
        assert result == response_data

    async def test_list_alert_details(self, httpx2_mock):
        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=True)
        alert_id = 123
        response_data = {"AlertDetailsResponse": {"id": 123}}

        url = f"https://apisb.etrade.com/v1/user/alerts/{alert_id}.json"

        httpx2_mock.get(url).respond(200, json=response_data)

        result = await alerts.list_alert_details(alert_id, resp_format="json")
        assert result == response_data

    async def test_delete_alert(self, httpx2_mock):
        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=True)
        alert_id = 123
        response_data = {"DeleteAlertsResponse": {"id": 123}}

        url = f"https://apisb.etrade.com/v1/user/alerts/{alert_id}.json"

        httpx2_mock.delete(url).respond(200, json=response_data)

        result = await alerts.delete_alert(alert_id, resp_format="json")
        assert result == response_data
