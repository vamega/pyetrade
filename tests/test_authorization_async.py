import pytest
from pyetrade.async_api.authorization import ETradeOAuth, ETradeAccessManager

pytestmark = pytest.mark.httpx2(assert_all_called=False)


@pytest.mark.asyncio
class TestETradeOAuthAsync:

    async def test_get_request_token(self, httpx2_mock):
        oauth = ETradeOAuth("key", "secret")

        # Mock fetch_request_token by mocking the request token URL endpoint?
        # OAuth1Client.fetch_request_token makes a POST usually? or GET?
        # ETrade docs say GET for request_token usually? Or POST?
        # The URL is https://api.etrade.com/oauth/request_token
        # client.fetch_request_token(url)
        # authlib does a POST or GET? OAuth 1.0a spec says POST usually but GET is allowed.
        # Let's mock both or check spec. ETrade might use specific method.
        # Existing tests mocked `fetch_request_token` method directly on the mock object.
        # Here we are using real AsyncOAuth1Client with httpx2_mock.

        url = "https://api.etrade.com/oauth/request_token"
        # OAuth response body usually: oauth_token=abc&oauth_token_secret=xyz&oauth_callback_confirmed=true
        body = "oauth_token=abc&oauth_token_secret=xyz&oauth_callback_confirmed=true"

        # Taking a guess it's GET or POST. Let's mock ANY method on that URL.
        httpx2_mock.route(url=url).respond(200, text=body)

        auth_url = await oauth.get_request_token()

        expected_url = "https://us.etrade.com/e/t/etws/authorize?key=key&token=abc"
        assert auth_url == expected_url
        assert oauth.resource_owner_key == "abc"

    async def test_get_access_token(self, httpx2_mock):
        oauth = ETradeOAuth("key", "secret")
        # We need to set resource_owner_key/secret because get_access_token uses them from get_request_token usually.
        # But get_access_token takes verifier.
        # Also need session with token set?
        # In `__init__`, session isn't created. It's created in `get_request_token`.
        # So we should call get_request_token first or manually setup.

        # Manual setup:
        from pyetrade._oauth1_client import AsyncOAuth1Client

        oauth.session = AsyncOAuth1Client(
            "key", "secret", token="req_token", token_secret="req_secret"
        )

        url = "https://api.etrade.com/oauth/access_token"
        body = "oauth_token=access_token&oauth_token_secret=access_secret"
        httpx2_mock.route(url=url).respond(200, text=body)

        tokens = await oauth.get_access_token("verifier_code")

        assert tokens["oauth_token"] == "access_token"
        assert tokens["oauth_token_secret"] == "access_secret"


@pytest.mark.asyncio
class TestETradeAccessManagerAsync:

    async def test_renew_access_token(self, httpx2_mock):
        manager = ETradeAccessManager("key", "secret", "token", "token_secret")

        url = "https://api.etrade.com/oauth/renew_access_token"
        httpx2_mock.get(url).respond(200, text="Access Token has been renewed")

        result = await manager.renew_access_token()
        assert result is True

    async def test_revoke_access_token(self, httpx2_mock):
        manager = ETradeAccessManager("key", "secret", "token", "token_secret")

        url = "https://api.etrade.com/oauth/revoke_access_token"
        httpx2_mock.get(url).respond(200, text="Revoked")

        result = await manager.revoke_access_token()
        assert result is True
