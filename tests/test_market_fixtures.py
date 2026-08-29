"""Tests for ETradeMarket using fixtures."""

import pytest
from unittest.mock import patch, MagicMock

from pyetrade.market import ETradeMarket
from pyetrade.async_api.market import ETradeMarket as ETradeMarketAsync
from tests.conftest import load_fixture

pytestmark = pytest.mark.httpx2(assert_all_called=False)


class TestETradeMarketWithFixtures:
    """Test ETradeMarket using real response fixtures."""

    @patch("pyetrade.market.OAuth1Client")
    def test_look_up_product_xml(self, MockOAuthClient):
        """Test look_up_product with XML fixture."""
        xml_response = load_fixture("LookupResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        market = ETradeMarket("key", "secret", "token", "token_secret", dev=False)
        result = market.look_up_product("google", resp_format="xml")

        assert "LookupResponse" in result
        lookup = result["LookupResponse"]
        assert "Data" in lookup

    @patch("pyetrade.market.OAuth1Client")
    def test_get_quote_xml(self, MockOAuthClient):
        """Test get_quote with XML fixture."""
        xml_response = load_fixture("GetQuotesResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        market = ETradeMarket("key", "secret", "token", "token_secret", dev=False)
        result = market.get_quote(["AAPL"], resp_format="xml")

        assert "QuoteResponse" in result
        quote_response = result["QuoteResponse"]
        assert "QuoteData" in quote_response

    @patch("pyetrade.market.OAuth1Client")
    def test_get_quote_multiple_symbols_xml(self, MockOAuthClient):
        """Test get_quote with multiple symbols using XML fixture."""
        xml_response = load_fixture("GetQuotesMultiResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        market = ETradeMarket("key", "secret", "token", "token_secret", dev=False)
        result = market.get_quote(["AAPL", "MSFT", "GOOG"], resp_format="xml")

        assert "QuoteResponse" in result
        quote_response = result["QuoteResponse"]
        assert "QuoteData" in quote_response
        # Multiple quotes should be a list
        quote_data = quote_response["QuoteData"]
        if isinstance(quote_data, list):
            assert len(quote_data) >= 1

    @patch("pyetrade.market.OAuth1Client")
    def test_get_option_chains_xml(self, MockOAuthClient):
        """Test get_option_chains with XML fixture."""
        xml_response = load_fixture("OptionChainResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        market = ETradeMarket("key", "secret", "token", "token_secret", dev=False)
        result = market.get_option_chains("SPY", resp_format="xml")

        assert "OptionChainResponse" in result
        chain = result["OptionChainResponse"]
        assert "OptionPair" in chain

    @patch("pyetrade.market.OAuth1Client")
    def test_get_option_expire_date_xml(self, MockOAuthClient):
        """Test get_option_expire_date with XML fixture."""
        xml_response = load_fixture("OptionExpireDateResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        market = ETradeMarket("key", "secret", "token", "token_secret", dev=False)
        result = market.get_option_expire_date("SPY", resp_format="xml")

        assert "OptionExpireDateResponse" in result
        expire_response = result["OptionExpireDateResponse"]
        assert "ExpirationDate" in expire_response


@pytest.mark.asyncio
class TestETradeMarketAsyncWithFixtures:
    """Test async ETradeMarket using real response fixtures."""

    async def test_look_up_product_xml(self, httpx2_mock):
        """Test async look_up_product with XML fixture."""
        xml_response = load_fixture("LookupResponse.xml")

        url = "https://api.etrade.com/v1/market/lookup/google.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        market = ETradeMarketAsync("key", "secret", "token", "token_secret", dev=False)
        result = await market.look_up_product("google", resp_format="xml")

        assert "LookupResponse" in result

    async def test_get_quote_xml(self, httpx2_mock):
        """Test async get_quote with XML fixture."""
        xml_response = load_fixture("GetQuotesResponse.xml")

        url = "https://api.etrade.com/v1/market/quote/AAPL.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        market = ETradeMarketAsync("key", "secret", "token", "token_secret", dev=False)
        result = await market.get_quote(["AAPL"], resp_format="xml")

        assert "QuoteResponse" in result
