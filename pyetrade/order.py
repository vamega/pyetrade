import logging
from datetime import datetime
from typing import Union, Dict, Any, Optional, List

import dateutil.parser
import xmltodict
from jxmlease import emit_xml
from authlib.integrations.httpx_client import OAuth1Client
import httpx

LOGGER = logging.getLogger(__name__)

# some constants
CALL = "Call"
PUT = "Put"


def to_decimal_str(price: float, round_down: bool) -> str:
    spstr = "%.2f" % price  # round to 2-place decimal
    spstrf = float(spstr)  # convert back to float again
    diff = price - spstrf

    if diff != 0:  # have to work hard to round to decimal
        HALF_CENT = 0.005  # e.g. BUY  stop: round up to decimal

        if round_down:
            HALF_CENT *= -1  # e.g. SELL stop: round down to decimal
        price += HALF_CENT

        if price > 0:
            spstr = "%.2f" % price  # now round to 2-place decimal

    return spstr


class RequestException(Exception):
    """:description: Exception raised when request to Etrade API returns an error"""
    pass


def get_request_result(req: httpx.Response, resp_format: str = "xml") -> dict:
    LOGGER.debug(req.text)

    # Initialize as empty dict, otherwise, when ETrade server returns an empty string, you get this error:
    # "simplejson.errors.JSONDecodeError: Expecting value: line 1 column 1 (char 0)"
    req_output = {}

    assert resp_format in ["xml", "json"]

    if resp_format == "json" and req.text.strip() != "":
        req_output = req.json()
    elif resp_format == "xml":
        req_output = xmltodict.parse(req.text)

    if "Error" in req_output.keys():
        try:
            code = req_output["Error"]["code"]
        except KeyError:
            code = None
        raise RequestException(
            f'Etrade API Error - Code: {code}, Msg: {req_output["Error"]["message"]}'
        )

    return req_output


# return Etrade internal option symbol: e.g. "PLTR--220218P00023000" ref:_test_option_symbol()
def option_symbol(
    symbol: str, call_put: str, expiry_date: str, strike_price: float
) -> str:
    sym = symbol.strip().upper()
    symstr = sym + ("-" * (6 - len(sym)))

    ed = dateutil.parser.parse(expiry_date)  # dateutil can handle most date formats
    edstr = ed.strftime("%y%m%d")
    assert len(edstr) == 6

    sp = "%08d" % (float(strike_price) * 1000)
    assert len(sp) == 8

    opt_sym = symstr + edstr + call_put.strip().upper()[0] + sp
    assert len(opt_sym) == 21

    return opt_sym


class OrderException(Exception):
    """:description: Exception raised when giving bad args to a method not from Etrade calls"""

    def __init__(self, explanation=None, params=None) -> None:
        super().__init__()
        self.required = params
        self.args = (explanation, params)

    def __str__(self) -> str:
        return "Missing required parameters"


class ETradeOrder(object):
    """:description: Object to perform Orders

    :param client_key: Client key provided by Etrade
    :type client_key: str, required
    :param client_secret: Client secret provided by Etrade
    :type client_secret: str, required
    :param resource_owner_key: Resource key from :class:`pyetrade.authorization.ETradeOAuth`
    :type resource_owner_key: str, required
    :param resource_owner_secret: Resource secret from
           :class: `pyetrade.authorization.ETradeOAuth`
    :type resource_owner_secret: str, required
    :param dev: Defines Sandbox (True) or Live (False) ETrade, defaults to True
    :type dev: bool, optional
    :param timeout: Timeout value for OAuth, defaults to 30
    :type timeout: int, optional
    :EtradeRef: https://apisb.etrade.com/docs/api/order/api-order-v1.html
    """

    def __init__(
        self,
        client_key: str,
        client_secret: str,
        resource_owner_key: str,
        resource_owner_secret: str,
        dev: bool = True,
        timeout: int = 30,
    ):
        self.dev_environment = dev
        self.base_url = f'https://{"apisb" if dev else "api"}.etrade.com/v1/accounts'
        self.timeout = timeout
        self.session = OAuth1Client(
            client_key,
            client_secret,
            token=resource_owner_key,
            token_secret=resource_owner_secret,
            signature_method="HMAC-SHA1",
            timeout=timeout,
        )

    def list_orders(
        self,
        account_id_key: str,
        marker: str = None,
        count: int = 25,
        status: str = None,
        from_date: datetime = None,
        to_date: datetime = None,
        symbols: list[str] = None,
        security_type: str = None,
        transaction_type: str = None,
        market_session: str = "REGULAR",
        resp_format: str = "json",
    ) -> dict:
        """:description: Lists orders for a specific account ID Key
        ... (docstring omitted for brevity) ...
        """

        if symbols and len(symbols) >= 26:
            LOGGER.warning(
                "list_orders asked for %d requests; only first 25 returned"
                % len(symbols)
            )

        api_url = f"{self.base_url}/{account_id_key}/orders{'.json' if resp_format == 'json' else ''}"
        LOGGER.debug(api_url)

        if count >= 101:
            LOGGER.debug(
                f"Count {count} is greater than the max allowable value (100), using 100."
            )
            count = 100

        payload = {
            "marker": marker,
            "count": count,
            "status": status,
            "fromDate": from_date.date().strftime("%m%d%Y") if from_date else None,
            "toDate": to_date.date().strftime("%m%d%Y") if to_date else None,
            "symbol": ",".join([sym for sym in symbols[:25]]) if symbols else None,
            "securityType": security_type,
            "transactionType": transaction_type,
            "marketSession": market_session,
        }

        req = self.session.get(api_url, params=payload)
        req.raise_for_status()

        LOGGER.debug(req.text)

        return get_request_result(req, resp_format)

    def list_order_details(
        self, account_id_key: str, order_id: int, resp_format: str = "json"
    ):
        """
        :description: Lists order details of a specific account ID Key and order ID
        ... (docstring omitted for brevity) ...
        """

        api_url = f"{self.base_url}/{account_id_key}/orders/{order_id}{'.json' if resp_format == 'json' else ''}"
        LOGGER.debug(api_url)

        req = self.session.get(api_url)
        req.raise_for_status()

        LOGGER.debug(req.text)

        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    def find_option_orders(
        self,
        account_id_key: str,
        symbol: str,
        call_put: str,
        expiry_date: str,
        strike_price: float,
    ) -> list:
        """:description: Lists option orders for a specific account ID Key
        ... (docstring omitted for brevity) ...
        """

        opt_sym = option_symbol(symbol, call_put, expiry_date, strike_price)
        orders = self.list_orders(
            account_id_key, resp_format="json", status="OPEN"
        )  # this call may return empty

        results = []

        if len(orders) > 0:
            for o in orders["OrdersResponse"]["Order"]:
                product = o["OrderDetail"][0]["Instrument"][0]["Product"]

                if product["securityType"] == "OPTN":
                    symbol = product["productId"][
                        "symbol"
                    ]  # e.g. "PLTR--220218P00023000"

                    if symbol == opt_sym:
                        results.append(o)
        return results

    @staticmethod
    def check_order(**kwargs):
        """:description: Check that required params for preview or place order are there and correct

        (Used internally)
        """

        mandatory = [
            "accountIdKey",
            "symbol",
            "orderAction",
            "clientOrderId",
            "priceType",
            "quantity",
            "orderTerm",
            "marketSession",
        ]

        if not all(param in kwargs for param in mandatory):
            raise OrderException

        if kwargs["priceType"] == "STOP" and "stopPrice" not in kwargs:
            raise OrderException
        if kwargs["priceType"] == "LIMIT" and "limitPrice" not in kwargs:
            raise OrderException
        if (
            kwargs["priceType"] == "STOP_LIMIT"
            and "limitPrice" not in kwargs
            and "stopPrice" not in kwargs
        ):
            raise OrderException

    @staticmethod
    def build_order_payload(order_type: str, **kwargs) -> dict:
        """:description: Builds the POST payload of a preview or place order
                      (Used internally)
        ... (docstring omitted for brevity) ...
        """
        securityType = kwargs.get("securityType", "EQ")  # EQ by default
        product = {"securityType": securityType, "symbol": kwargs["symbol"]}

        if securityType == "OPTN":
            expiryDate = dateutil.parser.parse(
                kwargs.pop("expiryDate")
            )  # dateutil can handle most date formats
            product.update(
                {
                    "expiryDay": expiryDate.day,
                    "expiryMonth": expiryDate.month,
                    "expiryYear": expiryDate.year,
                    "callPut": kwargs["callPut"],
                    "strikePrice": kwargs["strikePrice"],
                }
            )

        instrument = {
            "Product": product,
            "orderAction": kwargs["orderAction"],
            "quantityType": "QUANTITY",
            "quantity": kwargs["quantity"],
        }

        order = kwargs
        order["Instrument"] = instrument

        def remove_invalid_price_from_kwargs(key: str) -> None:
            if float(kwargs.get(key, 0)) <= 0:
                kwargs.pop(key, 0)

        remove_invalid_price_from_kwargs("stopPrice")
        remove_invalid_price_from_kwargs("limitPrice")

        if "stopPrice" in kwargs:
            stopPrice = float(kwargs["stopPrice"])
            round_down = "SELL" == kwargs["orderAction"][:4]
            spstr = to_decimal_str(stopPrice, round_down)

            order["stopPrice"] = spstr

        payload = {
            order_type: {
                "orderType": securityType,
                "clientOrderId": kwargs["clientOrderId"],
                "Order": order,
            }
        }

        if "previewId" in kwargs:
            payload[order_type]["PreviewIds"] = {"previewId": kwargs["previewId"]}

        return payload

    def perform_request(
        self, method, api_url: str, payload: Union[dict, str], resp_format: str = "xml"
    ) -> dict:
        """:description: POST or PUT request with json or xml used by preview, place and cancel
        ... (docstring omitted for brevity) ...
        """

        LOGGER.debug(api_url)
        LOGGER.debug("payload: %s", payload)

        if resp_format == "json":
            req = method(api_url, json=payload)
        else:
            headers = {"Content-Type": "application/xml"}
            payload = emit_xml(payload)
            LOGGER.debug("xml payload: %s", payload)
            req = method(api_url, content=payload, headers=headers)

        return get_request_result(req, resp_format)

    def preview_equity_order(self, **kwargs) -> dict:
        """API is used to submit an order request for preview before placing it
        ... (docstring omitted for brevity) ...
        """
        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/preview'

        # payload creation
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, "xml")

    def change_preview_equity_order(
        self, account_id_key: str, order_id: str, **kwargs
    ) -> dict:
        """:description: Same as :class:`preview_equity_order` with orderId
        ... (docstring omitted for brevity) ...
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        api_url = f"{self.base_url}/{account_id_key}/orders/{order_id}/change/preview"

        # payload creation
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)

        return self.perform_request(self.session.put, api_url, payload, "xml")

    def place_option_order(self, **kwargs) -> dict:
        """:description: Places Option Order, only single leg CALL or PUT is supported for now
        :return: Returns confirmation of the equity order
        """
        kwargs["securityType"] = "OPTN"

        return self.place_equity_order(**kwargs)

    def place_equity_order(self, **kwargs) -> dict:
        """:description: Places Equity Order
        ... (docstring omitted for brevity) ...
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        if "previewId" not in kwargs:
            LOGGER.debug(
                "No previewId given, previewing before placing order "
                "because Etrade requires all orders to have a previewId"
            )

            preview = self.preview_equity_order(**kwargs)
            kwargs["previewId"] = preview["PreviewOrderResponse"]["PreviewIds"][
                "previewId"
            ]

            LOGGER.debug(
                "Got a successful preview with previewId: %s", kwargs["previewId"]
            )

        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/place'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, "xml")

    def place_changed_option_order(self, **kwargs) -> dict:
        """:description: Places Option Order, only single leg CALL or PUT is supported for now
        :return: Returns confirmation of the equity order
        """
        kwargs["securityType"] = "OPTN"

        return self.place_changed_equity_order(**kwargs)

    def place_changed_equity_order(self, **kwargs) -> dict:
        """:description: Places changes to equity orders
         NOTE: the ETrade server will actually cancel the old orderId, and create a new orderId
        ... (docstring omitted for brevity) ...
        """

        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        if "previewId" not in kwargs:
            LOGGER.debug(
                "No previewId given, previewing before placing order "
                "because of an Etrade bug as of 1/1/2019"
            )
            preview = self.preview_equity_order(**kwargs)

            if "Error" in preview:
                LOGGER.error(preview)
                raise Exception("Please check your order!")

            kwargs["previewId"] = preview["PreviewOrderResponse"]["PreviewIds"][
                "previewId"
            ]
            LOGGER.debug(
                "Got a successful preview with previewId: %s", kwargs["previewId"]
            )

        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/{kwargs["orderId"]}/change/place'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        return self.perform_request(self.session.put, api_url, payload, "xml")

    def cancel_order(
        self, account_id_key: str, order_num: int, resp_format: str = "xml"
    ) -> dict:
        """:description: Cancels a specific order for a given account
        ... (docstring omitted for brevity) ...
        """

        api_url = f"{self.base_url}/{account_id_key}/orders/cancel"
        payload = {"CancelOrderRequest": {"orderId": order_num}}

        return self.perform_request(self.session.put, api_url, payload, resp_format)
