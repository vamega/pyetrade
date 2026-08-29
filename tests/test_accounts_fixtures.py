"""Tests for ETradeAccounts using fixtures."""

import pytest
from unittest.mock import patch, MagicMock

from pyetrade.accounts import ETradeAccounts
from pyetrade.async_api.accounts import ETradeAccounts as ETradeAccountsAsync
from tests.conftest import load_fixture

pytestmark = pytest.mark.httpx2(assert_all_called=False)


class TestETradeAccountsWithFixtures:
    """Test ETradeAccounts using real response fixtures."""

    @patch("pyetrade.accounts.OAuth1Client")
    def test_list_accounts_xml(self, MockOAuthClient):
        """Test list_accounts with XML fixture."""
        xml_response = load_fixture("AccountListResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        accounts = ETradeAccounts("key", "secret", "token", "token_secret", dev=False)
        result = accounts.list_accounts(resp_format="xml")

        assert "AccountListResponse" in result
        assert "Accounts" in result["AccountListResponse"]
        account_list = result["AccountListResponse"]["Accounts"]["Account"]
        assert len(account_list) == 2
        assert account_list[0]["accountId"] == "840104290"
        assert account_list[0]["accountIdKey"] == "JIdOIAcSpwR1Jva7RQBraQ"
        assert account_list[0]["accountMode"] == "MARGIN"
        assert account_list[0]["accountStatus"] == "ACTIVE"

    @patch("pyetrade.accounts.OAuth1Client")
    def test_get_account_balance_xml(self, MockOAuthClient):
        """Test get_account_balance with XML fixture."""
        xml_response = load_fixture("GetAccountBalanceResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        accounts = ETradeAccounts("key", "secret", "token", "token_secret", dev=False)
        result = accounts.get_account_balance("test_account_id_key", resp_format="xml")

        assert "BalanceResponse" in result
        balance = result["BalanceResponse"]
        assert balance["accountId"] == "835649790"
        assert balance["accountType"] == "PDT_ACCOUNT"
        assert balance["optionLevel"] == "LEVEL_4"
        assert balance["dayTraderStatus"] == "PDT_MIN_EQUITY_RES_1XK"

    @patch("pyetrade.accounts.OAuth1Client")
    def test_list_transactions_xml(self, MockOAuthClient):
        """Test list_transactions with XML fixture."""
        xml_response = load_fixture("ListTransactionsResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        accounts = ETradeAccounts("key", "secret", "token", "token_secret", dev=False)
        result = accounts.list_transactions("test_account_id_key", resp_format="xml")

        assert "TransactionListResponse" in result
        transactions = result["TransactionListResponse"]
        assert transactions["transactionCount"] == "3"
        assert transactions["totalCount"] == "5"
        assert "Transaction" in transactions

    @patch("pyetrade.accounts.OAuth1Client")
    def test_list_transaction_details_xml(self, MockOAuthClient):
        """Test list_transaction_details with XML fixture."""
        xml_response = load_fixture("ListTransactionDetailsResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        accounts = ETradeAccounts("key", "secret", "token", "token_secret", dev=False)
        result = accounts.list_transaction_details(
            "test_account_id_key", "test_transaction_id", resp_format="xml"
        )

        assert "TransactionDetailsResponse" in result

    @patch("pyetrade.accounts.OAuth1Client")
    def test_get_account_portfolio_xml(self, MockOAuthClient):
        """Test get_account_portfolio with XML fixture."""
        xml_response = load_fixture("ViewPortfolioResponse.xml")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = xml_response
        MockOAuthClient.return_value.get.return_value = mock_response

        accounts = ETradeAccounts("key", "secret", "token", "token_secret", dev=False)
        result = accounts.get_account_portfolio("test_account_id_key", resp_format="xml")

        assert "PortfolioResponse" in result
        portfolio = result["PortfolioResponse"]
        assert "AccountPortfolio" in portfolio


@pytest.mark.asyncio
class TestETradeAccountsAsyncWithFixtures:
    """Test async ETradeAccounts using real response fixtures."""

    async def test_list_accounts_xml(self, httpx2_mock):
        """Test async list_accounts with XML fixture."""
        xml_response = load_fixture("AccountListResponse.xml")

        url = "https://api.etrade.com/v1/accounts/list.xml"
        httpx2_mock.get(url).respond(200, text=xml_response)

        accounts = ETradeAccountsAsync("key", "secret", "token", "token_secret", dev=False)
        result = await accounts.list_accounts(resp_format="xml")

        assert "AccountListResponse" in result
        account_list = result["AccountListResponse"]["Accounts"]["Account"]
        assert len(account_list) == 2
        assert account_list[0]["accountId"] == "840104290"

    async def test_get_account_balance_xml(self, httpx2_mock):
        """Test async get_account_balance with XML fixture."""
        xml_response = load_fixture("GetAccountBalanceResponse.xml")

        url = "https://api.etrade.com/v1/accounts/test_key/balance"
        httpx2_mock.get(url).respond(200, text=xml_response)

        accounts = ETradeAccountsAsync("key", "secret", "token", "token_secret", dev=False)
        result = await accounts.get_account_balance("test_key", resp_format="xml")

        assert "BalanceResponse" in result
        assert result["BalanceResponse"]["accountType"] == "PDT_ACCOUNT"
