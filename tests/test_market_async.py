import pytest
import respx
from httpx import Response
from pyetrade.async_api.market import ETradeMarket

import datetime

@pytest.mark.asyncio
class TestETradeMarket:
    
    @respx.mock
    async def test_look_up_product(self):
        market = ETradeMarket("key", "secret", "token", "token_secret", dev=True)
        response_data = {"LookupResponse": {"Data": [{"symbol": "MMM"}]}}
        
        # Test look_up_product with json format
        # URL structure: https://apisb.etrade.com/v1/market/lookup/{search_str}.json
        url = "https://apisb.etrade.com/v1/market/lookup/mmm.json"
        respx.get(url).mock(return_value=Response(200, json=response_data))
        
        result = await market.look_up_product("mmm", resp_format="json")
        assert result == response_data

    @respx.mock
    async def test_get_quote(self):
        market = ETradeMarket("key", "secret", "token", "token_secret", dev=True)
        response_data = {"QuoteResponse": {"QuoteData": [{"Product": {"symbol": "AAPL"}}]}}
        
        # Note: get_quote builds URL like quote/AAPL,GOOG.json
        url = "https://apisb.etrade.com/v1/market/quote/AAPL.json"
        respx.get(url).mock(return_value=Response(200, json=response_data))
        
        result = await market.get_quote(["AAPL"], resp_format="json")
        assert result == response_data

    @respx.mock
    async def test_get_option_chains(self):
        market = ETradeMarket("key", "secret", "token", "token_secret", dev=True)
        response_data = {"OptionChainResponse": {}}
        
        expiry_date = datetime.date(2023, 1, 1)
        
        # URL: optionchains.json?symbol=AAPL&expiryDay=01&expiryMonth=01&expiryYear=2023
        # respx with params matching
        url = "https://apisb.etrade.com/v1/market/optionchains.json"
        
        route = respx.get(url) 
        route.mock(return_value=Response(200, json=response_data))
        
        result = await market.get_option_chains("AAPL", expiry_date=expiry_date, resp_format="json")
        assert result == response_data
