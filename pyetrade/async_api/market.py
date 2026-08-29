import logging
from datetime import datetime
import asyncio
import xmltodict
from .._oauth1_client import AsyncOAuth1Client

from ..utils import clean_params

LOGGER = logging.getLogger(__name__)


class ETradeMarket(object):
    """:description: Async Market object to access market information"""

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
        self.dev_environment = dev
        self.base_url = f'https://{"apisb" if dev else "api"}.etrade.com/v1/market/'
        self.session = AsyncOAuth1Client(
            self.client_key,
            self.client_secret,
            token=self.resource_owner_key,
            token_secret=self.resource_owner_secret,
            signature_method="HMAC-SHA1",
        )

    async def look_up_product(self, search_str: str, resp_format: str = "xml") -> dict:
        api_url = "%slookup/%s" % (
            self.base_url,
            f"{search_str}.xml" if resp_format.lower() == "xml" else f"{search_str}.json",
        )
        LOGGER.debug(api_url)
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_quote(
        self,
        symbols: list[str],
        detail_flag: str = None,
        require_earnings_date: str = None,
        skip_mini_options_check: str = None,
        resp_format: str = "xml",
    ) -> dict:
        if detail_flag is not None:
            detail_flag = detail_flag.lower()
        if len(symbols) >= 26:
            LOGGER.warning("get_quote asked for %d requests; only first 25 returned" % len(symbols))
        args = list()
        if detail_flag is not None:
            args.append("detailflag=%s" % detail_flag.upper())
        if require_earnings_date:
            args.append("requireEarningsDate=true")
        if skip_mini_options_check is not None:
            args.append("skipMiniOptionsCheck=%s" % str(skip_mini_options_check))
        api_url = "%s%s%s" % (self.base_url, "quote/", ",".join(symbols[:25]))
        if resp_format.lower() == "json":
            api_url += ".json"
        else:
            api_url += ".xml"
        if len(args):
            api_url += "?" + "&".join(args)
        LOGGER.debug(api_url)
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_option_chains(
        self,
        underlier: str,
        expiry_date: datetime.date,
        skip_adjusted: str = None,
        chain_type: str = None,
        strike_price_near: int = None,
        no_of_strikes: int = None,
        option_category: str = None,
        price_type: str = None,
        resp_format: str = "xml",
    ) -> dict:
        if chain_type is not None:
            chain_type = chain_type.lower()
        if option_category is not None:
            option_category = option_category.lower()
        if price_type is not None:
            price_type = price_type.lower()

        args = ["symbol=%s" % underlier]
        if expiry_date is not None:
            args.append(
                "expiryDay=%02d&expiryMonth=%02d&expiryYear=%04d"
                % (expiry_date.day, expiry_date.month, expiry_date.year)
            )
        if strike_price_near is not None:
            args.append("strikePriceNear=%0.2f" % strike_price_near)
        if chain_type is not None:
            args.append("chainType=%s" % chain_type.upper())
        if option_category is not None:
            args.append("optionCategory=%s" % option_category.upper())
        if price_type is not None:
            args.append("priceType=%s" % price_type.upper())
        if skip_adjusted is not None:
            args.append("skipAdjusted=%s" % str(skip_adjusted))
        if no_of_strikes is not None:
            args.append("noOfStrikes=%d" % no_of_strikes)

        api_url = "%s%s%s" % (
            self.base_url,
            "optionchains?" if resp_format.lower() == "xml" else "optionchains.json?",
            "&".join(args),
        )
        LOGGER.debug(api_url)
        req = await self.session.get(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def get_option_expire_date(self, symbol: str, resp_format: str = "xml") -> dict:
        api_url = "%s%s" % (
            self.base_url,
            "optionexpiredate" if resp_format.lower() == "xml" else "optionexpiredate.json",
        )
        LOGGER.debug(api_url)
        req = await self.session.get(
            api_url, params=clean_params({"symbol": symbol, "expiryType": "ALL"})
        )
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()
