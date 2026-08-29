import logging
import asyncio
from datetime import datetime
from typing import Union, Dict, Any, Optional, List, Literal

import dateutil.parser
import xmltodict
from jxmlease import emit_xml
import httpx2
from .._oauth1_client import OAuth1Auth

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

    def __init__(self, message: str, response: Optional[dict] = None) -> None:
        super().__init__(message)
        self.response = response


def get_request_result(req: httpx2.Response, resp_format: str = "xml") -> dict:
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
def option_symbol(symbol: str, call_put: str, expiry_date: str, strike_price: float) -> str:
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
    """:description: Object to perform Orders Asynchronously"""

    async def _log_request(self, request: httpx2.Request) -> None:
        LOGGER.debug("Request: %s %s", request.method, request.url)
        LOGGER.debug("Request headers: %s", dict(request.headers))

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
        self.session = httpx2.AsyncClient(
            timeout=timeout,
            event_hooks={"request": [self._log_request]},
        )

    async def list_orders(
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
        if symbols and len(symbols) >= 26:
            LOGGER.warning(
                "list_orders asked for %d requests; only first 25 returned" % len(symbols)
            )

        api_url = (
            f"{self.base_url}/{account_id_key}/orders{'.json' if resp_format == 'json' else '.xml'}"
        )
        LOGGER.debug(api_url)

        if count >= 101:
            LOGGER.debug(f"Count {count} is greater than the max allowable value (100), using 100.")
            count = 100

        payload = {}
        if marker:
            payload["marker"] = marker
        if count is not None and count != 25:
            payload["count"] = count
        if status:
            payload["status"] = status
        if from_date:
            payload["fromDate"] = from_date.date().strftime("%m%d%Y")
        if to_date:
            payload["toDate"] = to_date.date().strftime("%m%d%Y")
        if symbols:
            payload["symbol"] = ",".join([sym for sym in symbols[:25]])
        if security_type:
            payload["securityType"] = security_type
        if transaction_type:
            payload["transactionType"] = transaction_type
        if market_session and market_session != "REGULAR":
            payload["marketSession"] = market_session

        req = await self.session.get(api_url, params=payload or None)
        req.raise_for_status()

        LOGGER.debug(req.text)

        return get_request_result(req, resp_format)

    async def perform_request(
        self,
        method: str,
        api_url: str,
        payload: Union[dict, str],
        resp_format: Literal["json", "xml"] = "xml",
    ) -> dict:
        LOGGER.debug(api_url)
        LOGGER.debug("payload: %s", payload)

        if isinstance(method, str):
            method_name = method.upper()
        else:
            method_name = getattr(method, "__name__", "post").upper()

        if resp_format == "json":
            headers = {"Accept": "application/json", "Content-Type": "application/json"}
            request = httpx2.Request(method_name, api_url, json=payload, headers=headers)
            auth_request = httpx2.Request(method_name, api_url, json=payload, headers=headers)
        else:
            headers = {"Content-Type": "application/xml"}
            payload = emit_xml(payload)
            LOGGER.debug("xml payload: %s", payload)
            request = httpx2.Request(method_name, api_url, content=payload, headers=headers)
            auth_request = httpx2.Request(method_name, api_url, content=payload, headers=headers)

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

        req = await self.session.send(request)

        return get_request_result(req, resp_format)

    async def preview_equity_order(self, **kwargs) -> dict:
        LOGGER.debug(kwargs)
        self.check_order(**kwargs)
        resp_format = kwargs.get("resp_format", "xml")
        suffix = ".json" if resp_format == "json" else ""
        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/preview{suffix}'
        payload = self.build_order_payload("PreviewOrderRequest", **kwargs)
        return await self.perform_request(self.session.post, api_url, payload, resp_format)

    async def preview_option_order(self, **kwargs) -> dict:
        kwargs["securityType"] = "OPTN"
        return await self.preview_equity_order(**kwargs)

    async def preview_order_builder(self, builder, resp_format: str = "xml") -> dict:
        payload = builder.build_preview_payload()
        account_id_key = builder.get_account_id_key()
        suffix = ".json" if resp_format == "json" else ""
        api_url = f"{self.base_url}/{account_id_key}/orders/preview{suffix}"
        return await self.perform_request(self.session.post, api_url, payload, resp_format)

    async def place_order_builder(self, builder, preview_ids, resp_format: str = "xml") -> dict:
        payload = builder.build_place_payload(preview_ids)
        account_id_key = builder.get_account_id_key()
        suffix = ".json" if resp_format == "json" else ""
        api_url = f"{self.base_url}/{account_id_key}/orders/place{suffix}"
        return await self.perform_request(self.session.post, api_url, payload, resp_format)

    async def place_equity_order(self, **kwargs) -> dict:
        LOGGER.debug(kwargs)
        self.check_order(**kwargs)

        if "previewId" not in kwargs:
            preview = await self.preview_equity_order(**kwargs)
            kwargs["previewId"] = self._extract_preview_id(preview)

        resp_format = kwargs.get("resp_format", "xml")
        suffix = ".json" if resp_format == "json" else ""
        api_url = f'{self.base_url}/{kwargs["accountIdKey"]}/orders/place{suffix}'
        payload = self.build_order_payload("PlaceOrderRequest", **kwargs)
        return await self.perform_request(self.session.post, api_url, payload, resp_format)

    async def list_order_details(
        self, account_id_key: str, order_id: int, resp_format: str = "json"
    ):
        api_url = f"{self.base_url}/{account_id_key}/orders/{order_id}{'.json' if resp_format == 'json' else ''}"
        LOGGER.debug(api_url)
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def cancel_order(
        self, account_id_key: str, order_num: int, resp_format: str = "xml"
    ) -> dict:
        api_url = "%s/%s/orders/cancel%s" % (
            self.base_url,
            account_id_key,
            ".json" if resp_format == "json" else "",
        )
        payload = {"CancelOrderRequest": {"orderId": order_num}}
        return await self.perform_request(self.session.put, api_url, payload, resp_format)

    @staticmethod
    def check_order(**kwargs):
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
            from ..utils import validate_client_order_id

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
        securityType = kwargs.get("securityType", "EQ")  # EQ by default
        product = {"securityType": securityType, "symbol": kwargs["symbol"]}

        if securityType == "OPTN":
            expiryDate = dateutil.parser.parse(kwargs.pop("expiryDate"))
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
