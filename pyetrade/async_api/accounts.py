import logging
from datetime import datetime
import asyncio
import xmltodict
import httpx
from authlib.integrations.httpx_client import AsyncOAuth1Client

from ..utils import clean_params
LOGGER = logging.getLogger(__name__)

class ETradeAccounts(object):
    """:description: Async Accounts object to access account information"""

    def __init__(
        self,
        client_key: str,
        client_secret: str,
        resource_owner_key: str,
        resource_owner_secret: str,
        dev: bool = True,
    ):
        self.client_key = client_key
        self.client_secret = client_secret
        self.resource_owner_key = resource_owner_key
        self.resource_owner_secret = resource_owner_secret
        self.base_url = f'https://{"apisb" if dev else "api"}.etrade.com/v1/accounts'
        self.session = AsyncOAuth1Client(
            self.client_key,
            self.client_secret,
            token=self.resource_owner_key,
            token_secret=self.resource_owner_secret,
            signature_method="HMAC-SHA1",
        )

    async def list_accounts(self, resp_format: str = "xml") -> dict:
        api_url = "%s/list%s" % (
            self.base_url,
            ".json" if resp_format == "json" else ".xml",
        )
        LOGGER.debug(api_url)
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_account_balance(
        self,
        account_id_key: str,
        account_type: str = None,
        real_time: bool = True,
        resp_format: str = "xml",
    ) -> dict:
        api_url = "%s/%s/balance%s" % (
            self.base_url,
            account_id_key,
            ".json" if resp_format == "json" else ".xml",
        )
        payload = {}
        if real_time is not None and real_time is False:
            payload["realTimeNAV"] = real_time
        if account_type:
            payload["accountType"] = account_type
        LOGGER.debug(api_url)
        req = await self.session.get(api_url, params=clean_params(payload))
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_account_portfolio(
        self,
        account_id_key: str,
        count: int = 50,
        sort_by: str = None,
        sort_order: str = "DESC",
        page_number: int = None,
        market_session: str = "REGULAR",
        totals_required: bool = False,
        lots_required: bool = False,
        view: str = "QUICK",
        resp_format: str = "xml",
    ) -> dict:
        api_url = "%s/%s/portfolio%s" % (
            self.base_url,
            account_id_key,
            ".json" if resp_format == "json" else "",
        )
        payload = {
            "count": count,
            "sortBy": sort_by,
            "sortOrder": sort_order,
            "pageNumber": page_number,
            "marketSession": market_session,
            "totalsRequired": totals_required,
            "lotsRequired": lots_required,
            "view": view,
        }
        LOGGER.debug(api_url)
        req = await self.session.get(api_url, params=clean_params(payload))
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_portfolio_position_lot(
        self, symbol: str, account_id_key: str, resp_format: str = "xml"
    ) -> dict:
        portfolio = await self.get_account_portfolio(
            account_id_key, lots_required=True, resp_format="json"
        )
        account_portfolio = portfolio["PortfolioResponse"]["AccountPortfolio"][0]["Position"]
        lot_position_id = [
            position["positionId"]
            for position in account_portfolio
            if symbol.upper() == position["Product"]["symbol"].upper()
        ]
        if len(lot_position_id) != 1:
            raise KeyError(
                f'Symbol "{symbol}" could not be found. '
                f"Please check your portfolio and symbol before trying again."
            )
        LOGGER.debug(lot_position_id[0])
        api_url = "%s/%s/portfolio/%s%s" % (
            self.base_url,
            account_id_key,
            lot_position_id[0],
            ".json" if resp_format == "json" else "",
        )
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def list_transactions(
        self,
        account_id_key: str,
        start_date: datetime.date = None,
        end_date: datetime.date = None,
        sort_order: str = "DESC",
        marker: str = None,
        count: int = 50,
        resp_format: str = "xml",
    ) -> dict:
        api_url = "%s/%s/transactions%s" % (
            self.base_url,
            account_id_key,
            ".json" if resp_format == "json" else "",
        )
        payload = {
            "startDate": start_date.strftime("%m%d%Y") if start_date else None,
            "endDate": end_date.strftime("%m%d%Y") if end_date else None,
            "sortOrder": sort_order,
            "marker": marker,
            "count": count,
        }
        LOGGER.debug(api_url)
        req = await self.session.get(api_url, params=clean_params(payload))
        req.raise_for_status()
        LOGGER.debug(req.text)
        if req.text == "":
            return {}
        elif resp_format.lower() == "xml":
            return xmltodict.parse(req.text)
        else:
            return req.json()

    async def list_transaction_details(
        self,
        account_id_key: str,
        transaction_id: int,
        store_id: any = None,
        resp_format: str = "xml",
    ) -> dict:
        api_url = "%s/%s/transactions/%s%s" % (
            self.base_url,
            account_id_key,
            transaction_id,
            ".json" if resp_format == "json" else "",
        )
        LOGGER.debug(api_url)
        req = await self.session.get(api_url, params=clean_params({"storeId": store_id}))
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()
