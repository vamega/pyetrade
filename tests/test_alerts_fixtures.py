"""Tests for ETradeAlerts using fixtures."""

import pytest
from unittest.mock import patch, MagicMock

from pyetrade.alerts import ETradeAlerts
from pyetrade.async_api.alerts import ETradeAlerts as ETradeAlertsAsync
from tests.conftest import load_fixture

pytestmark = pytest.mark.httpx2(assert_all_called=False)


class TestETradeAlertsWithFixtures:
    """Test ETradeAlerts using real response fixtures."""

    @patch("pyetrade.alerts.OAuth1Client")
    def test_list_alerts_xml(self, MockOAuthClient):
        """Test list_alerts with XML fixture."""
        xml_response = load_fixture("ListAlertsResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=False)
        result = alerts.list_alerts(resp_format="xml")

        assert "AlertsResponse" in result
        alerts_response = result["AlertsResponse"]
        assert "Alert" in alerts_response

    @patch("pyetrade.alerts.OAuth1Client")
    def test_list_alert_details_xml(self, MockOAuthClient):
        """Test list_alert_details with XML fixture."""
        xml_response = load_fixture("ListAlertDetailsResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=False)
        result = alerts.list_alert_details(12345, resp_format="xml")

        assert "AlertDetailsResponse" in result

    @patch("pyetrade.alerts.OAuth1Client")
    def test_delete_alert_xml(self, MockOAuthClient):
        """Test delete_alert with XML fixture."""
        xml_response = load_fixture("DeleteAlertsResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.delete.return_value = mock_response

        alerts = ETradeAlerts("key", "secret", "token", "token_secret", dev=False)
        result = alerts.delete_alert(12345, resp_format="xml")

        assert "DeleteAlertsResponse" in result


@pytest.mark.asyncio
class TestETradeAlertsAsyncWithFixtures:
    """Test async ETradeAlerts using real response fixtures."""

    async def test_list_alerts_xml(self, httpx2_mock):
        """Test async list_alerts with XML fixture."""
        xml_response = load_fixture("ListAlertsResponse.xml")

        url = "https://api.etrade.com/v1/user/alerts.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=False)
        result = await alerts.list_alerts(resp_format="xml")

        assert "AlertsResponse" in result

    async def test_list_alert_details_xml(self, httpx2_mock):
        """Test async list_alert_details with XML fixture."""
        xml_response = load_fixture("ListAlertDetailsResponse.xml")

        url = "https://api.etrade.com/v1/user/alerts/12345.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=False)
        result = await alerts.list_alert_details(12345, resp_format="xml")

        assert "AlertDetailsResponse" in result

    async def test_delete_alert_xml(self, httpx2_mock):
        """Test async delete_alert with XML fixture."""
        xml_response = load_fixture("DeleteAlertsResponse.xml")

        url = "https://api.etrade.com/v1/user/alerts/12345.xml"
        httpx2_mock.delete(url).respond(200, text=xml_response)

        alerts = ETradeAlertsAsync("key", "secret", "token", "token_secret", dev=False)
        result = await alerts.delete_alert(12345, resp_format="xml")

        assert "DeleteAlertsResponse" in result
