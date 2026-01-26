"""Tests for ETradeOrder using fixtures."""
import pytest
import respx
from httpx import Response
from unittest.mock import patch, MagicMock

from pyetrade.order import ETradeOrder
from pyetrade.async_api.order import ETradeOrder as ETradeOrderAsync
from tests.conftest import load_fixture, load_json_fixture


class TestETradeOrderWithFixtures:
    """Test ETradeOrder using real response fixtures."""

    @patch("pyetrade.order.OAuth1Client")
    def test_list_orders_xml(self, MockOAuthClient):
        """Test list_orders with XML fixture."""
        xml_response = load_fixture("ListOrdersResponse.xml")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.list_orders("test_account_id_key", resp_format="xml")

        assert "OrdersResponse" in result
        orders_response = result["OrdersResponse"]
        assert "Order" in orders_response

    @patch("pyetrade.order.OAuth1Client")
    def test_preview_equity_order_json(self, MockOAuthClient):
        """Test preview_equity_order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseEquity.json")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = json_response
        MockOAuthClient.return_value.post.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.preview_equity_order(
            resp_format="json",
            accountIdKey="test_account_key",
            symbol="AAPL",
            orderAction="BUY",
            clientOrderId="test-001",
            priceType="MARKET",
            quantity=10,
            orderTerm="GOOD_FOR_DAY",
            marketSession="REGULAR",
        )

        assert "PreviewOrderResponse" in result
        preview = result["PreviewOrderResponse"]
        assert "Order" in preview

    @patch("pyetrade.order.OAuth1Client")
    def test_preview_option_order_json(self, MockOAuthClient):
        """Test preview option order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseOptions.json")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = json_response
        MockOAuthClient.return_value.post.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.preview_option_order(
            resp_format="json",
            accountIdKey="test_account_key",
            symbol="AAPL",
            orderAction="BUY_OPEN",
            clientOrderId="test-001",
            priceType="LIMIT",
            limitPrice=5.00,
            quantity=1,
            orderTerm="GOOD_FOR_DAY",
            marketSession="REGULAR",
            callPut="CALL",
            expiryDate="2024-12-20",
            strikePrice=180.0,
        )

        assert "PreviewOrderResponse" in result

    @patch("pyetrade.order.OAuth1Client")
    def test_preview_spread_order_json(self, MockOAuthClient):
        """Test preview spread order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseSpread.json")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = json_response
        MockOAuthClient.return_value.post.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        # Note: This tests the expected response structure for spread orders
        # The actual method would need to support spread order requests
        assert "PreviewOrderResponse" in json_response
        preview = json_response["PreviewOrderResponse"]
        assert preview["orderType"] == "SPREADS"
        # Verify spread has multiple instruments
        order_detail = preview["Order"][0]
        assert len(order_detail["Instrument"]) == 2

    @patch("pyetrade.order.OAuth1Client")
    def test_place_equity_order_json(self, MockOAuthClient):
        """Test place_equity_order with JSON fixture."""
        json_response = load_json_fixture("PlaceOrderResponseEquity.json")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = json_response
        MockOAuthClient.return_value.post.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.place_equity_order(
            resp_format="json",
            accountIdKey="test_account_key",
            symbol="AAPL",
            orderAction="BUY",
            clientOrderId="test-001",
            priceType="MARKET",
            quantity=10,
            orderTerm="GOOD_FOR_DAY",
            marketSession="REGULAR",
        )

        assert "PlaceOrderResponse" in result
        place_response = result["PlaceOrderResponse"]
        assert "Order" in place_response

    @patch("pyetrade.order.OAuth1Client")
    def test_cancel_order_json(self, MockOAuthClient):
        """Test cancel_order with JSON fixture."""
        json_response = load_json_fixture("CancelOrderResponse.json")
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = json_response
        MockOAuthClient.return_value.put.return_value = mock_response

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.cancel_order(
            "test_account_key",
            12345,
            resp_format="json",
        )

        assert "CancelOrderResponse" in result


class TestOrderFixtureStructure:
    """Test that fixtures have expected structure for spread orders."""
    
    def test_preview_request_spread_structure(self):
        """Verify PreviewOrderRequestSpread fixture has correct structure."""
        request = load_json_fixture("PreviewOrderRequestSpread.json")
        
        assert "PreviewOrderRequest" in request
        preview_req = request["PreviewOrderRequest"]
        assert preview_req["orderType"] == "SPREADS"
        assert "Order" in preview_req
        order = preview_req["Order"][0]
        assert "Instrument" in order
        # Spread should have 2 legs
        assert len(order["Instrument"]) == 2
        
        # Verify first leg (long)
        leg1 = order["Instrument"][0]
        assert leg1["orderAction"] == "BUY_OPEN"
        assert leg1["Product"]["callPut"] == "CALL"
        assert leg1["Product"]["strikePrice"] == "130"
        
        # Verify second leg (short)
        leg2 = order["Instrument"][1]
        assert leg2["orderAction"] == "SELL_OPEN"
        assert leg2["Product"]["strikePrice"] == "131"

    def test_place_request_spread_structure(self):
        """Verify PlaceOrderRequestSpread fixture has correct structure."""
        request = load_json_fixture("PlaceOrderRequestSpread.json")
        
        assert "PlaceOrderRequest" in request
        place_req = request["PlaceOrderRequest"]
        assert place_req["orderType"] == "SPREADS"
        assert "PreviewIds" in place_req
        assert len(place_req["PreviewIds"]) == 1

    def test_place_response_spread_structure(self):
        """Verify PlaceOrderResponseSpread fixture has expected response."""
        response = load_json_fixture("PlaceOrderResponseSpread.json")
        
        assert "PlaceOrderResponse" in response
        place_resp = response["PlaceOrderResponse"]
        assert place_resp["orderType"] == "SPREADS"
        assert "Order" in place_resp
        order = place_resp["Order"][0]
        # Response should include order ID
        assert "Instrument" in order
        assert len(order["Instrument"]) == 2


@pytest.mark.asyncio
class TestETradeOrderAsyncWithFixtures:
    """Test async ETradeOrder using real response fixtures."""

    @respx.mock
    async def test_list_orders_xml(self):
        """Test async list_orders with XML fixture."""
        xml_response = load_fixture("ListOrdersResponse.xml")
        
        url = "https://api.etrade.com/v1/accounts/test_key/orders.xml"
        respx.get(url).mock(return_value=Response(200, text=xml_response))

        orders = ETradeOrderAsync("key", "secret", "token", "token_secret", dev=False)
        result = await orders.list_orders("test_key", resp_format="xml")

        assert "OrdersResponse" in result

    @respx.mock
    async def test_cancel_order_json(self):
        """Test async cancel_order with JSON fixture."""
        json_response = load_json_fixture("CancelOrderResponse.json")
        
        url = "https://api.etrade.com/v1/accounts/test_key/orders/cancel.json"
        respx.put(url).mock(return_value=Response(200, json=json_response))

        orders = ETradeOrderAsync("key", "secret", "token", "token_secret", dev=False)
        result = await orders.cancel_order("test_key", 12345, resp_format="json")

        assert "CancelOrderResponse" in result
