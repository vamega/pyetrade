"""Focused tests for PyETrade's HTTPX2 OAuth1 adapter."""

import pytest
import httpx2

from authlib.integrations.base_client import OAuthError

from pyetrade._oauth1_client import AsyncOAuth1Client, OAuth1Auth, OAuth1Client

CLIENT_KWARGS = {
    "client_id": "consumer-key",
    "client_secret": "consumer-secret",
    "token": "resource-token",
    "token_secret": "resource-secret",
}


def test_sync_client_signs_httpx2_request_and_preserves_extensions():
    def handler(request):
        assert isinstance(request, httpx2.Request)
        assert isinstance(request.extensions, dict)
        assert request.extensions["test-marker"] == "preserved"
        assert request.headers["Authorization"].startswith("OAuth ")
        return httpx2.Response(200, request=request, json={"ok": True})

    client = OAuth1Client(
        **CLIENT_KWARGS,
        transport=httpx2.MockTransport(handler),
    )
    try:
        assert isinstance(client, httpx2.Client)
        assert isinstance(client.auth, OAuth1Auth)
        assert isinstance(client.auth, httpx2.Auth)

        request = client.build_request("GET", "https://example.test/resource")
        request.extensions["test-marker"] = "preserved"
        response = client.send(request)

        assert isinstance(response, httpx2.Response)
        assert response.json() == {"ok": True}
    finally:
        client.close()


def test_sync_client_preserves_body_when_force_include_body_is_enabled():
    expected_body = b"<Order><Symbol>AAPL</Symbol></Order>"

    def handler(request):
        assert request.content == expected_body
        assert request.headers["Content-Length"] == str(len(expected_body))
        assert request.headers["Authorization"].startswith("OAuth ")
        return httpx2.Response(200, request=request, text="ok")

    client = OAuth1Client(
        **CLIENT_KWARGS,
        force_include_body=True,
        transport=httpx2.MockTransport(handler),
    )
    try:
        response = client.post(
            "https://example.test/orders",
            content=expected_body,
            headers={"Content-Type": "application/xml"},
        )
        assert response.text == "ok"
    finally:
        client.close()


@pytest.mark.asyncio
async def test_async_client_signs_httpx2_request_and_preserves_extensions():
    def handler(request):
        assert isinstance(request, httpx2.Request)
        assert request.extensions["test-marker"] == "preserved"
        assert request.headers["Authorization"].startswith("OAuth ")
        return httpx2.Response(200, request=request, json={"ok": True})

    async with AsyncOAuth1Client(
        **CLIENT_KWARGS,
        transport=httpx2.MockTransport(handler),
    ) as client:
        assert isinstance(client, httpx2.AsyncClient)
        assert isinstance(client.auth, OAuth1Auth)
        assert isinstance(client.auth, httpx2.Auth)

        request = client.build_request("GET", "https://example.test/resource")
        request.extensions["test-marker"] = "preserved"
        response = await client.send(request)

        assert isinstance(response, httpx2.Response)
        assert response.json() == {"ok": True}


def test_sync_client_fetches_tokens_and_reports_missing_verifier():
    def handler(request):
        assert request.headers["Authorization"].startswith("OAuth ")
        return httpx2.Response(
            200,
            request=request,
            text="oauth_token=request-token&oauth_token_secret=request-secret",
        )

    client = OAuth1Client(
        client_id="consumer-key",
        client_secret="consumer-secret",
        transport=httpx2.MockTransport(handler),
    )
    try:
        token = client.fetch_request_token("https://example.test/request-token")
        assert token == {
            "oauth_token": "request-token",
            "oauth_token_secret": "request-secret",
        }
        assert client.token["oauth_token"] == "request-token"

        with pytest.raises(OAuthError, match="missing_verifier"):
            client.fetch_access_token("https://example.test/access-token")
    finally:
        client.close()


@pytest.mark.asyncio
async def test_async_client_fetches_tokens_and_reports_missing_verifier():
    def handler(request):
        assert request.headers["Authorization"].startswith("OAuth ")
        return httpx2.Response(
            200,
            request=request,
            text="oauth_token=access-token&oauth_token_secret=access-secret",
        )

    async with AsyncOAuth1Client(
        client_id="consumer-key",
        client_secret="consumer-secret",
        transport=httpx2.MockTransport(handler),
    ) as client:
        token = await client.fetch_request_token("https://example.test/request-token")
        assert token == {
            "oauth_token": "access-token",
            "oauth_token_secret": "access-secret",
        }

        with pytest.raises(OAuthError, match="missing_verifier"):
            await client.fetch_access_token("https://example.test/access-token")
