"""Tests for ETradeOrder using fixtures."""

import json
import pytest

from pyetrade.order import ETradeOrder
from pyetrade.async_api.order import ETradeOrder as ETradeOrderAsync
from tests.conftest import load_fixture, load_json_fixture

pytestmark = pytest.mark.httpx2(assert_all_called=False)


class TestETradeOrderWithFixtures:
    """Test ETradeOrder using real response fixtures."""

    def test_list_orders_xml(self, httpx2_mock):
        """Test list_orders with XML fixture."""
        xml_response = load_fixture("ListOrdersResponse.xml")

        url = (
            "https://api.etrade.com/v1/accounts/test_account_id_key/orders"
            "?count=25&marketSession=REGULAR"
        )
        route = httpx2_mock.get(url)
        route.respond(200, text=xml_response)

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.list_orders("test_account_id_key", resp_format="xml")

        assert "OrdersResponse" in result
        orders_response = result["OrdersResponse"]
        assert "Order" in orders_response
        assert route.called
        assert route.calls[0].request.method == "GET"
        assert str(route.calls[0].request.url) == url

    def test_preview_equity_order_json(self, httpx2_mock):
        """Test preview_equity_order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseEquity.json")

        url = "https://api.etrade.com/v1/accounts/test_account_key/orders/preview.json"
        route = httpx2_mock.post(url)
        route.respond(200, json=json_response)

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
        assert route.called
        request = route.calls[0].request
        assert request.method == "POST"
        assert json.loads(request.content)["PreviewOrderRequest"]["orderType"] == "EQ"
        assert "OAuth " in request.headers["Authorization"]

    def test_preview_option_order_json(self, httpx2_mock):
        """Test preview option order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseOptions.json")

        url = "https://api.etrade.com/v1/accounts/test_account_key/orders/preview.json"
        route = httpx2_mock.post(url)
        route.respond(200, json=json_response)

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
        request = route.calls[0].request
        assert request.method == "POST"
        payload = json.loads(request.content)["PreviewOrderRequest"]
        instrument = payload["Order"][0]["Instrument"][0]
        assert instrument["Product"]["securityType"] == "OPTN"
        assert instrument["Product"]["callPut"] == "CALL"

    def test_preview_spread_order_json(self):
        """Test preview spread order with JSON fixture."""
        json_response = load_json_fixture("PreviewOrderResponseSpread.json")
        # Note: This tests the expected response structure for spread orders
        # The actual method would need to support spread order requests
        assert "PreviewOrderResponse" in json_response
        preview = json_response["PreviewOrderResponse"]
        assert preview["orderType"] == "SPREADS"
        # Verify spread has multiple instruments
        order_detail = preview["Order"][0]
        assert len(order_detail["Instrument"]) == 2

    def test_place_equity_order_json(self, httpx2_mock):
        """Test place_equity_order with JSON fixture."""
        preview_response = load_json_fixture("PreviewOrderResponseEquity.json")
        place_response = load_json_fixture("PlaceOrderResponseEquity.json")

        preview_url = "https://api.etrade.com/v1/accounts/test_account_key/orders/preview.json"
        place_url = "https://api.etrade.com/v1/accounts/test_account_key/orders/place.json"
        preview_route = httpx2_mock.post(preview_url)
        preview_route.respond(200, json=preview_response)
        place_route = httpx2_mock.post(place_url)
        place_route.respond(200, json=place_response)

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
        assert preview_route.called and place_route.called
        assert preview_route.calls[0].request.method == "POST"
        assert place_route.calls[0].request.method == "POST"
        preview_payload = json.loads(preview_route.calls[0].request.content)
        place_payload = json.loads(place_route.calls[0].request.content)
        assert preview_payload["PreviewOrderRequest"]["clientOrderId"] == "test-001"
        assert place_payload["PlaceOrderRequest"]["PreviewIds"]

    def test_cancel_order_json(self, httpx2_mock):
        """Test cancel_order with JSON fixture."""
        json_response = load_json_fixture("CancelOrderResponse.json")

        url = "https://api.etrade.com/v1/accounts/test_account_key/orders/cancel"
        route = httpx2_mock.put(url)
        route.respond(200, json=json_response)

        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=False)
        result = orders.cancel_order(
            "test_account_key",
            12345,
            resp_format="json",
        )

        assert "CancelOrderResponse" in result
        assert route.called
        request = route.calls[0].request
        assert request.method == "PUT"
        assert json.loads(request.content) == {"CancelOrderRequest": {"orderId": 12345}}


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

    async def test_list_orders_xml(self, httpx2_mock):
        """Test async list_orders with XML fixture."""
        xml_response = load_fixture("ListOrdersResponse.xml")

        url = "https://api.etrade.com/v1/accounts/test_key/orders.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        orders = ETradeOrderAsync("key", "secret", "token", "token_secret", dev=False)
        result = await orders.list_orders("test_key", resp_format="xml")

        assert "OrdersResponse" in result

    async def test_cancel_order_json(self, httpx2_mock):
        """Test async cancel_order with JSON fixture."""
        json_response = load_json_fixture("CancelOrderResponse.json")

        url = "https://api.etrade.com/v1/accounts/test_key/orders/cancel.json"
        httpx2_mock.put(url).respond(200, json=json_response)

        orders = ETradeOrderAsync("key", "secret", "token", "token_secret", dev=False)
        result = await orders.cancel_order("test_key", 12345, resp_format="json")

        assert "CancelOrderResponse" in result
