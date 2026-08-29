#!/usr/bin/env python3
"""pyetrade authorization unit tests
TODO:
    * Test request error
    * Test API URL
"""

import json
import unittest
from unittest.mock import MagicMock

import httpx2

from pyetrade import order


class TestETradeOrder(unittest.TestCase):
    """TestEtradeOrder Unit Test"""

    def _orders_with_transport(self, handler, dev=False):
        """Build an order client whose HTTPX2 transport is under test control."""
        orders = order.ETradeOrder("abc123", "xyz123", "abctoken", "xyzsecret", dev=dev)
        # ETradeOrder owns a default client; replace it with a real HTTPX2 client
        # using a deterministic transport at the same boundary production uses.
        orders.session.close()
        orders.session = httpx2.Client(transport=httpx2.MockTransport(handler))
        self.addCleanup(orders.session.close)
        return orders

    def test_option_symbol(self):
        expected = "PLTR--220218P00023000"
        self.assertEqual(expected, order.option_symbol("PLTR", order.PUT, "2022-02-18", 23))
        self.assertEqual(expected, order.option_symbol("PLTR", order.PUT, "2022-02-18", 23.00))
        self.assertEqual(expected, order.option_symbol("PLTR", order.PUT, "2022-02-18", "23.0"))

    def test_list_orders(self):
        requests = []

        def handler(request):
            requests.append(request)
            if request.url.path.endswith(".json"):
                return httpx2.Response(200, request=request, json={"accountId": "12345"})
            return httpx2.Response(
                200,
                request=request,
                text="<OrdersResponse><Order><orderId>42</orderId></Order></OrdersResponse>",
            )

        orders = self._orders_with_transport(handler, dev=False)

        self.assertEqual(orders.list_orders("12345"), {"accountId": "12345"})
        self.assertEqual(orders.list_orders("12345"), {"accountId": "12345"})
        self.assertTrue(isinstance(orders.list_orders("12345", resp_format="xml"), dict))

        self.assertEqual([request.method for request in requests], ["GET"] * 3)
        self.assertEqual(
            str(requests[0].url),
            "https://api.etrade.com/v1/accounts/12345/orders.json?count=25&marketSession=REGULAR",
        )
        self.assertEqual(requests[2].url.path, "/v1/accounts/12345/orders")

    def test_list_order_details(self):
        requests = []

        def handler(request):
            requests.append(request)
            return httpx2.Response(200, request=request, json={"accountId": "12345"})

        orders = self._orders_with_transport(handler, dev=False)

        self.assertTrue(isinstance(orders.list_order_details("12345", 123, "json"), dict))
        self.assertEqual(len(requests), 1)
        self.assertEqual(requests[0].method, "GET")
        self.assertEqual(
            str(requests[0].url),
            "https://api.etrade.com/v1/accounts/12345/orders/123.json",
        )

    def test_find_option_orders(self):
        orders = order.ETradeOrder("abc123", "xyz123", "abctoken", "xyzsecret", dev=False)

        orders.option_symbol = MagicMock(return_value="AAPL--220218C00065000")

        orders.list_orders = MagicMock(
            return_value={
                "OrdersResponse": {
                    "Order": [
                        {
                            "OrderDetail": [
                                {
                                    "Instrument": [
                                        {
                                            "Product": {
                                                "securityType": "OPTN",
                                                "productId": {"symbol": "AAPL--220218C00065000"},
                                            }
                                        }
                                    ]
                                }
                            ]
                        }
                    ]
                }
            }
        )

        # Call the function being tested
        result = orders.find_option_orders("34fsdf43f", "AAPL", "call", "02-08-2021", 65.0)

        self.assertTrue(isinstance(result, list))

    def test_place_equity_order(self):
        requests = []
        preview_json = {"PreviewOrderResponse": {"PreviewIds": {"previewId": "321"}}}
        place_json = {"PlaceOrderResponse": {"OrderIds": {"orderId": "654"}}}

        def handler(request):
            requests.append(request)
            if request.url.path.endswith("/preview.json"):
                return httpx2.Response(200, request=request, json=preview_json)
            if request.url.path.endswith("/place.json"):
                return httpx2.Response(200, request=request, json=place_json)
            if request.url.path.endswith("/preview"):
                return httpx2.Response(
                    200,
                    request=request,
                    text="<PreviewOrderResponse><PreviewIds><previewId>321</previewId></PreviewIds></PreviewOrderResponse>",
                )
            return httpx2.Response(
                200,
                request=request,
                text="<PlaceOrderResponse><OrderIds><orderId>654</orderId></OrderIds></PlaceOrderResponse>",
            )

        orders = self._orders_with_transport(handler, dev=False)

        result = orders.place_equity_order(
            accountIdKey="12345",
            symbol="ABC",
            orderAction="BUY",
            clientOrderId="1a2b3c",
            priceType="MARKET",
            quantity=100,
            orderTerm="GOOD_UNTIL_CANCEL",
            marketSession="REGULAR",
        )

        self.assertEqual(result["PlaceOrderResponse"]["OrderIds"]["orderId"], "654")

        json_result = orders.place_equity_order(
            resp_format="json",
            accountIdKey="12345",
            symbol="ABC",
            orderAction="BUY",
            clientOrderId="1a2b3c",
            priceType="MARKET",
            quantity=100,
            orderTerm="GOOD_UNTIL_CANCEL",
            marketSession="REGULAR",
        )
        self.assertEqual(json_result, place_json)
        self.assertEqual([request.method for request in requests], ["POST"] * 4)
        self.assertEqual(requests[0].url.path, "/v1/accounts/12345/orders/preview")
        self.assertEqual(requests[1].url.path, "/v1/accounts/12345/orders/place")
        self.assertEqual(requests[2].url.path, "/v1/accounts/12345/orders/preview.json")
        self.assertEqual(requests[3].url.path, "/v1/accounts/12345/orders/place.json")
        self.assertIn("<PreviewOrderRequest>", requests[0].content.decode())
        self.assertIn("<PlaceOrderRequest>", requests[1].content.decode())
        json_payload = json.loads(requests[2].content)
        self.assertEqual(
            json_payload["PreviewOrderRequest"]["Order"][0]["Instrument"][0]["Product"]["symbol"],
            "ABC",
        )
        self.assertEqual(
            json.loads(requests[3].content)["PlaceOrderRequest"]["PreviewIds"],
            [{"previewId": "321"}],
        )
        for request in requests:
            self.assertIn("OAuth ", request.headers["Authorization"])

        # Test payload: BUY MARKET
        payload = orders.build_order_payload(
            "PreviewOrderRequest",
            resp_format="json",
            accountId="12345",
            symbol="ABC",
            orderAction="BUY",
            clientOrderId="1a2b3c",
            priceType="MARKET",
            quantity=100,
            orderTerm="GOOD_UNTIL_CANCEL",
            marketSession="REGULAR",
        )

        expected = {
            "PreviewOrderRequest": {
                "orderType": "EQ",
                "clientOrderId": "1a2b3c",
                "Order": [
                    {
                        "allOrNone": "false",
                        "priceType": "MARKET",
                        "orderTerm": "GOOD_UNTIL_CANCEL",
                        "marketSession": "REGULAR",
                        "stopPrice": "",
                        "limitPrice": "",
                        "Instrument": [
                            {
                                "Product": {"securityType": "EQ", "symbol": "ABC"},
                                "orderAction": "BUY",
                                "quantityType": "QUANTITY",
                                "quantity": 100,
                            }
                        ],
                    }
                ],
            }
        }
        self.assertTrue(expected == payload)

        # Test payload: SELL STOP
        float_decimals = [
            (
                19.99999,
                "19.99",
            ),  # double values are not exact; SELL: round down to decimal
            (20, "20.00"),  # exact int
            (20.01001, "20.01"),
            (20.01, "20.01"),
            (20.00999, "20.00"),
            (20.00001, "20.00"),
        ]

        for fd in float_decimals:
            for orderAction in ["SELL", "SELL_SHORT"]:
                payload = orders.build_order_payload(
                    "PreviewOrderRequest",
                    accountIdKey="12345",
                    symbol="ABC",
                    orderAction=orderAction,
                    clientOrderId="1a2b3c",
                    priceType="STOP",
                    stopPrice=fd[0],
                    quantity=100,
                    orderTerm="GOOD_UNTIL_CANCEL",
                    marketSession="REGULAR",
                )

                self.assertEqual(payload["PreviewOrderRequest"]["Order"][0]["stopPrice"], fd[1])

        # Test payload: BUY STOP
        float_decimals = [
            (
                19.99999,
                "20.00",
            ),  # double values are not exact; BUY: round   up to decimal
            (20, "20.00"),  # exact int
            (20.01001, "20.02"),
            (20.01, "20.01"),
            (20.00999, "20.01"),
            (20.00001, "20.01"),
        ]

        for fd in float_decimals:
            for orderAction in ["BUY", "BUY_TO_COVER"]:
                payload = orders.build_order_payload(
                    "PreviewOrderRequest",
                    accountIdKey="12345",
                    symbol="ABC",
                    orderAction=orderAction,
                    clientOrderId="1a2b3c",
                    priceType="STOP",
                    stopPrice=fd[0],
                    quantity=100,
                    orderTerm="GOOD_UNTIL_CANCEL",
                    marketSession="REGULAR",
                )

                self.assertEqual(payload["PreviewOrderRequest"]["Order"][0]["stopPrice"], fd[1])

    def test_place_equity_order_exception(self):
        """Invalid order arguments are rejected before any HTTP request."""
        orders = order.ETradeOrder("abc123", "xyz123", "abctoken", "xyzsecret", dev=False)

        # Test exception class
        with self.assertRaises(order.OrderException):
            orders.place_equity_order()
        try:
            orders.place_equity_order()
        except order.OrderException as e:
            print(e)

        # Test STOP
        with self.assertRaises(order.OrderException):
            orders.place_equity_order(
                accountIdKey="12345",
                symbol="ABC",
                orderAction="BUY",
                clientOrderId="1a2b3c",
                priceType="STOP",
                quantity=100,
                orderTerm="GOOD_UNTIL_CANCEL",
                marketSession="REGULAR",
            )
        # Test LIMIT
        with self.assertRaises(order.OrderException):
            orders.place_equity_order(
                accountIdKey="12345",
                symbol="ABC",
                orderAction="BUY",
                clientOrderId="1a2b3c",
                priceType="LIMIT",
                quantity=100,
                orderTerm="GOOD_UNTIL_CANCEL",
                marketSession="REGULAR",
            )
        # Test STOP_LIMIT
        with self.assertRaises(order.OrderException):
            orders.place_equity_order(
                accountIdKey="12345",
                symbol="ABC",
                orderAction="BUY",
                clientOrderId="1a2b3c",
                priceType="STOP_LIMIT",
                quantity=100,
                orderTerm="GOOD_UNTIL_CANCEL",
                marketSession="REGULAR",
            )

    def test_cancel_order(self):
        requests = []

        def handler(request):
            requests.append(request)
            if request.headers.get("Accept") == "application/json":
                return httpx2.Response(200, request=request, json={"accountIdKey": "12345"})
            return httpx2.Response(
                200,
                request=request,
                text="<CancelOrderResponse><orderId>42</orderId></CancelOrderResponse>",
            )

        orders = self._orders_with_transport(handler, dev=False)

        self.assertEqual(
            orders.cancel_order("12345", 42, resp_format="json"),
            {"accountIdKey": "12345"},
        )
        xml_result = orders.cancel_order("12345", 42, resp_format="xml")
        self.assertEqual(xml_result["CancelOrderResponse"]["orderId"], "42")
        self.assertEqual([request.method for request in requests], ["PUT", "PUT"])
        self.assertEqual(
            str(requests[0].url),
            "https://api.etrade.com/v1/accounts/12345/orders/cancel",
        )
        self.assertEqual(
            json.loads(requests[0].content),
            {"CancelOrderRequest": {"orderId": 42}},
        )
        self.assertIn("<CancelOrderRequest>", requests[1].content.decode())
        self.assertIn("OAuth ", requests[0].headers["Authorization"])
