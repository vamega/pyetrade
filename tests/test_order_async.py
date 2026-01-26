
import pytest
import respx
from httpx import Response
from pyetrade.async_api.order import ETradeOrder

@pytest.mark.asyncio
class TestETradeOrder:
    
    @respx.mock
    async def test_list_orders(self):
        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=True)
        account_id_key = "123456"
        response_data = {"OrdersResponse": {"Order": []}}
        
        url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/orders.json"
        
        # httpx drops None values, so default params like marker=None end up not in URL.
        # But we pass count=25 by default.
        respx.get(url).mock(return_value=Response(200, json=response_data))
        
        result = await orders.list_orders(account_id_key, resp_format="json")
        assert result == response_data

    @respx.mock
    async def test_preview_equity_order(self):
        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=True)
        account_id_key = "123456"
        
        response_data = {"PreviewOrderResponse": {"PreviewIds": {"previewId": "123"}}}
        
        url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/orders/preview"
        # POST request
        # Response defaults to XML if we don't handle it in perform_request, 
        # but preview_equity_order calls perform_request(..., resp_format="xml") hardcoded in order.py line 578
        # Wait, line 578: return await self.perform_request(..., "xml")
        # So we should mock XML response or expect XML result.
        # But we can update the mock to return XML.
        
        xml_response = """<PreviewOrderResponse><PreviewIds><previewId>123</previewId></PreviewIds></PreviewOrderResponse>"""
        respx.post(url).mock(return_value=Response(200, text=xml_response))
        
        result = await orders.preview_equity_order(
            accountIdKey=account_id_key,
            symbol="ABC",
            orderAction="BUY",
            clientOrderId="1a2b3c",
            priceType="MARKET",
            quantity=100,
            orderTerm="GOOD_UNTIL_CANCEL",
            marketSession="REGULAR"
        )
        
        # Result is parsed from XML to dict
        assert result["PreviewOrderResponse"]["PreviewIds"]["previewId"] == "123"

    @respx.mock
    async def test_place_equity_order(self):
        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=True)
        account_id_key = "123456"
        
        # We need to mock preview first because place_equity_order calls preview if previewId is missing.
        preview_url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/orders/preview"
        preview_xml = """<PreviewOrderResponse><PreviewIds><previewId>123</previewId></PreviewIds></PreviewOrderResponse>"""
        respx.post(preview_url).mock(return_value=Response(200, text=preview_xml))
        
        place_url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/orders/place"
        place_xml = """<PlaceOrderResponse><OrderIds><orderId>999</orderId></OrderIds></PlaceOrderResponse>"""
        respx.post(place_url).mock(return_value=Response(200, text=place_xml))
        
        result = await orders.place_equity_order(
            accountIdKey=account_id_key,
            symbol="ABC",
            orderAction="BUY",
            clientOrderId="1a2b3c",
            priceType="MARKET",
            quantity=100,
            orderTerm="GOOD_UNTIL_CANCEL",
            marketSession="REGULAR"
        )
        
        assert result["PlaceOrderResponse"]["OrderIds"]["orderId"] == "999"

    @respx.mock
    async def test_cancel_order(self):
        orders = ETradeOrder("key", "secret", "token", "token_secret", dev=True)
        account_id_key = "123456"
        order_num = 123
        
        url = f"https://apisb.etrade.com/v1/accounts/{account_id_key}/orders/cancel"
        
        response_xml = """<CancelOrderResponse><orderId>123</orderId></CancelOrderResponse>"""
        respx.put(url).mock(return_value=Response(200, text=response_xml))
        
        result = await orders.cancel_order(account_id_key, order_num)
        
        assert result["CancelOrderResponse"]["orderId"] == "123"
