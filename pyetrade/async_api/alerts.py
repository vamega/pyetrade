import logging
import asyncio
import xmltodict
from .._oauth1_client import AsyncOAuth1Client

from ..utils import clean_params

# Set up logging
LOGGER = logging.getLogger(__name__)


class ETradeAlerts(object):
    """:description: Async Object to retrieve alerts"""

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
        self.base_url = f'https://{"apisb" if dev else "api"}.etrade.com/v1/user/alerts'
        self.session = AsyncOAuth1Client(
            self.client_key,
            self.client_secret,
            token=self.resource_owner_key,
            token_secret=self.resource_owner_secret,
            signature_method="HMAC-SHA1",
        )

    async def list_alerts(
        self, count: int = 25, sort_order: str = "DESC", resp_format: str = "xml"
    ) -> dict:
        api_url = "%s%s" % (
            self.base_url,
            ".json" if resp_format == "json" else ".xml",
        )
        LOGGER.debug(api_url)
        if count >= 301:
            LOGGER.debug(f"Count {count} is greater than the max allowable value (300), using 300")
            count = 300
        params = {}
        if count != 25:
            params["count"] = count
        if sort_order and sort_order != "DESC":
            params["direction"] = sort_order
        req = await self.session.get(api_url, params=clean_params(params))
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def list_alert_details(
        self, alert_id: int, html_tags: bool = False, resp_format: str = "xml"
    ) -> dict:
        api_url = "%s/%s%s" % (
            self.base_url,
            alert_id,
            ".json" if resp_format == "json" else ".xml",
        )
        LOGGER.debug(api_url)
        params = {"htmlTags": html_tags} if html_tags else None
        req = await self.session.get(api_url, params=clean_params(params))
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()

    async def delete_alert(self, alert_id: int, resp_format: str = "xml") -> dict:
        api_url = "%s/%s%s" % (
            self.base_url,
            alert_id,
            ".json" if resp_format == "json" else ".xml",
        )
        LOGGER.debug(api_url)
        req = await self.session.delete(api_url)
        req.raise_for_status()
        LOGGER.debug(req.text)
        return xmltodict.parse(req.text) if resp_format.lower() == "xml" else req.json()
