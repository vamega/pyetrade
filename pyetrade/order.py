import logging
from datetime import datetime
from typing import Union, Dict, Any, Optional, List, Literal

import dateutil.parser
import xmltodict
from jxmlease import emit_xml
from authlib.integrations.httpx_client import OAuth1Auth
import httpx

from .utils import clean_params, validate_client_order_id
LOGGER = logging.getLogger(__name__)

# some constants
CALL = "Call"
PUT = "Put"

T_MARKET_SESSION = Literal["REGULAR", "EXTENDED"]

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
    def __init__(self, message: str, response: Optional[dict] = None) -> None:
        super().__init__(message)
        self.response = response


def get_request_result(req: httpx.Response, resp_format: str = "xml") -> dict:
    LOGGER.debug(req.text)
    raw_text = req.text or ""

    # Initialize as empty dict, otherwise, when ETrade server returns an empty string, you get this error:
    # "simplejson.errors.JSONDecodeError: Expecting value: line 1 column 1 (char 0)"
    req_output = {}

    assert resp_format in ["xml", "json"]

    if resp_format == "json" and raw_text.strip() != "":
        try:
            req_output = req.json()
        except Exception:
            if raw_text.lstrip().startswith("<"):
                req_output = xmltodict.parse(raw_text)
            else:
                raise
    elif resp_format == "xml":
        req_output = xmltodict.parse(raw_text)

    if "Error" in req_output.keys():
        error_payload = req_output.get("Error") or {}
        code = error_payload.get("code")
        message = error_payload.get("message") or error_payload.get("error") or str(error_payload)
        raise RequestException(
            f"Etrade API Error - Code: {code}, Msg: {message}",
            response={
                "status_code": req.status_code,
                "raw": raw_text,
                "parsed": req_output,
            },
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
        self._auth = OAuth1Auth(
            client_key,
            client_secret,
            token=resource_owner_key,
            token_secret=resource_owner_secret,
            signature_method="HMAC-SHA1",
        )
        self.session = httpx.Client(
            timeout=timeout,
            event_hooks={"request": [self._log_request]},
        )

    def _log_request(self, request: httpx.Request) -> None:
        LOGGER.debug("Request: %s %s", request.method, request.url)
        LOGGER.debug("Request headers: %s", dict(request.headers))
        body = request.content
        if body:
            try:
                body_text = body.decode("utf-8")
            except AttributeError:
                body_text = str(body)
            LOGGER.debug("Request body: %s", body_text)
        else:
            LOGGER.debug("Request body: <empty>")

    def list_orders(
        self,
        account_id_key: str,
        marker: str = None,
        count: int = 25,
        status: Optional[Literal["OPEN", "EXECUTED", "CANCELLED", "INDIVIDUAL_FILLS", "CANCEL_REQUESTED", "EXPIRED", "REJECTED"]] = None,
        from_date: datetime = None,
        to_date: datetime = None,
        symbols: list[str] = None,
        security_type: Optional[Literal["EQ", "OPTN", "MF", "MMF"]] = None,
        transaction_type: Optional[Literal["ATNM", "BUY", "SELL", "SELL_SHORT", "BUY_TO_COVER", "MF_EXCHANGE"]] = None,
        market_session: T_MARKET_SESSION = "REGULAR",
        resp_format: Literal["json", "xml"] = "json",
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

        req = self.session.get(api_url, params=clean_params(payload))
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

        client_order_id = kwargs.get("clientOrderId", "")
        try:
            validate_client_order_id(client_order_id)
        except ValueError as exc:
            raise OrderException(str(exc)) from exc

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
    def _extract_preview_id(preview: dict):
        preview_ids = preview.get("PreviewOrderResponse", {}).get("PreviewIds")
        if isinstance(preview_ids, list):
            if preview_ids:
                return preview_ids[0].get("previewId")
        if isinstance(preview_ids, dict):
            return preview_ids.get("previewId")
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
        if securityType == "OPTN":
            instrument["orderedQuantity"] = kwargs["quantity"]

        stop_price = kwargs.get("stopPrice")
        limit_price = kwargs.get("limitPrice")

        order_detail = {
            "allOrNone": str(kwargs.get("allOrNone", "false")).lower(),
            "priceType": kwargs["priceType"],
            "orderTerm": kwargs["orderTerm"],
            "marketSession": kwargs["marketSession"],
            "stopPrice": "",
            "limitPrice": "",
            "Instrument": [instrument],
        }

        if stop_price is not None:
            stopPrice = float(stop_price)
            round_down = "SELL" == kwargs["orderAction"][:4]
            order_detail["stopPrice"] = to_decimal_str(stopPrice, round_down)
        if limit_price is not None:
            order_detail["limitPrice"] = str(limit_price)

        payload = {
            order_type: {
                "orderType": securityType,
                "clientOrderId": kwargs["clientOrderId"],
                "Order": [order_detail],
            }
        }

        if "previewId" in kwargs:
            payload[order_type]["PreviewIds"] = [{"previewId": kwargs["previewId"]}]

        return payload

    def perform_request(
        self, method, api_url: str, payload: Union[dict, str], resp_format: str = "xml"
    ) -> dict:
        """:description: POST or PUT request with json or xml used by preview, place and cancel
        ... (docstring omitted for brevity) ...
        """

        LOGGER.debug(api_url)
        LOGGER.debug("payload: %s", payload)

        if isinstance(method, str):
            method_name = method.upper()
        else:
            method_name = getattr(method, "__name__", "post").upper()

        if resp_format == "json":
            headers = {"Accept": "application/json"}
            request = httpx.Request(method_name, api_url, json=payload, headers=headers)
            auth_request = httpx.Request(method_name, api_url, json=payload, headers=headers)
        else:
            headers = {"Content-Type": "application/xml"}
            payload = emit_xml(payload)
            LOGGER.debug("xml payload: %s", payload)
            request = httpx.Request(method_name, api_url, content=payload, headers=headers)
            auth_request = httpx.Request(method_name, api_url, content=payload, headers=headers)

        try:
            body = request.content
            LOGGER.debug("Built request content length: %s", len(body or b""))
        except Exception as exc:
            LOGGER.debug("Failed to read request content: %r", exc)

        flow = self._auth.sync_auth_flow(auth_request)
        signed_request = next(flow)
        auth_header = signed_request.headers.get("Authorization")
        if auth_header:
            request.headers["Authorization"] = auth_header

        req = self.session.send(request)

        return get_request_result(req, resp_format)

    def preview_equity_order(self, **kwargs) -> dict:
        """API is used to submit an order request for preview before placing it
        ... (docstring omitted for brevity) ...
        """
        LOGGER.debug(kwargs)

        # Test required values
        self.check_order(**kwargs)

        resp_format = kwargs.get("resp_format", "xml")
        suffix = ".json" if resp_format == "json" else ""
        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/preview{suffix}'

        # payload creation
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, resp_format)

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

        resp_format = kwargs.get("resp_format", "xml")
        return self.perform_request(self.session.post, api_url, payload, resp_format)

    def preview_option_order(self, **kwargs) -> dict:
        """:description: Preview option order (single leg)."""
        kwargs["securityType"] = "OPTN"
        return self.preview_equity_order(**kwargs)

    def preview_order_builder(self, builder, resp_format: str = "xml") -> dict:
        """Preview an order built with OrderBuilder."""
        payload = builder.build_preview_payload()
        account_id_key = builder.get_account_id_key()
        suffix = ".json" if resp_format == "json" else ""
        api_url = f"{self.base_url}/{account_id_key}/orders/preview{suffix}"
        return self.perform_request(self.session.post, api_url, payload, resp_format)

    def place_order_builder(
        self, builder, preview_ids, resp_format: str = "xml"
    ) -> dict:
        """Place an order built with OrderBuilder."""
        payload = builder.build_place_payload(preview_ids)
        account_id_key = builder.get_account_id_key()
        suffix = ".json" if resp_format == "json" else ""
        api_url = f"{self.base_url}/{account_id_key}/orders/place{suffix}"
        return self.perform_request(self.session.post, api_url, payload, resp_format)

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
            kwargs["previewId"] = self._extract_preview_id(preview)

            LOGGER.debug(
                "Got a successful preview with previewId: %s", kwargs["previewId"]
            )

        resp_format = kwargs.get("resp_format", "xml")
        suffix = ".json" if resp_format == "json" else ""
        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/place{suffix}'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        return self.perform_request(self.session.post, api_url, payload, resp_format)

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

            kwargs["previewId"] = self._extract_preview_id(preview)
            LOGGER.debug(
                "Got a successful preview with previewId: %s", kwargs["previewId"]
            )

        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/{kwargs["orderId"]}/change/place'

        # payload creation
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)

        resp_format = kwargs.get("resp_format", "xml")
        return self.perform_request(self.session.post, api_url, payload, resp_format)

    def cancel_order(
        self, account_id_key: str, order_num: int, resp_format: str = "xml"
    ) -> dict:
        """:description: Cancels a specific order for a given account
        ... (docstring omitted for brevity) ...
        """

        api_url = f"{self.base_url}/{account_id_key}/orders/cancel"
        payload = {"CancelOrderRequest": {"orderId": order_num}}

        return self.perform_request(self.session.put, api_url, payload, resp_format)
