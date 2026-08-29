"""OAuth 1.0 clients backed by HTTPX2.

Authlib's released HTTP client integration currently subclasses its legacy
HTTPX client.
Keeping the small integration here lets the library use HTTPX2 without
requiring a process-wide ``httpx2.alias_httpx()`` call or an old ``httpx``
installation.  The protocol and token handling remain provided by Authlib.
"""

from __future__ import annotations

import typing

import httpx2
from authlib.common.encoding import to_unicode
from authlib.integrations.base_client import OAuthError
from authlib.oauth1 import (
    ClientAuth,
    SIGNATURE_HMAC_SHA1,
    SIGNATURE_TYPE_HEADER,
)
from authlib.oauth1.client import OAuth1Client as _OAuth1Client

_HTTPX_CLIENT_KWARGS = (
    "headers",
    "cookies",
    "verify",
    "cert",
    "http1",
    "http2",
    "proxy",
    "mounts",
    "timeout",
    "follow_redirects",
    "limits",
    "max_redirects",
    "event_hooks",
    "base_url",
    "transport",
    "trust_env",
    "default_encoding",
    "app",
)


def _extract_client_kwargs(kwargs: dict[str, typing.Any]) -> dict[str, typing.Any]:
    """Remove HTTPX2 client options from the Authlib options dictionary."""

    client_kwargs = {}
    for key in _HTTPX_CLIENT_KWARGS:
        if key in kwargs:
            client_kwargs[key] = kwargs.pop(key)
    return client_kwargs


def _build_request(
    url: str,
    headers: typing.Mapping[str, str],
    body: bytes,
    initial_request: httpx2.Request,
) -> httpx2.Request:
    """Build a signed request while preserving HTTPX2 request extensions."""

    updated_request = httpx2.Request(
        method=initial_request.method,
        url=url,
        headers=headers,
        content=body,
    )
    if hasattr(initial_request, "extensions"):
        updated_request.extensions = initial_request.extensions
    return updated_request


class OAuth1Auth(httpx2.Auth, ClientAuth):
    """Sign an HTTPX2 request using OAuth 1.0 (RFC 5849)."""

    requires_request_body = True

    def auth_flow(
        self, request: httpx2.Request
    ) -> typing.Generator[httpx2.Request, httpx2.Response, None]:
        url, headers, body = self.prepare(
            request.method,
            str(request.url),
            request.headers,
            request.content,
        )
        headers["Content-Length"] = str(len(body))
        yield _build_request(
            url=url,
            headers=headers,
            body=body,
            initial_request=request,
        )


class AsyncOAuth1Client(_OAuth1Client, httpx2.AsyncClient):
    """Async OAuth 1.0 client using HTTPX2's async transport."""

    auth_class = OAuth1Auth

    def __init__(
        self,
        client_id: str,
        client_secret: str | None = None,
        token: str | None = None,
        token_secret: str | None = None,
        redirect_uri: str | None = None,
        rsa_key: str | None = None,
        verifier: str | None = None,
        signature_method: str = SIGNATURE_HMAC_SHA1,
        signature_type: str = SIGNATURE_TYPE_HEADER,
        force_include_body: bool = False,
        **kwargs: typing.Any,
    ) -> None:
        client_kwargs = _extract_client_kwargs(kwargs)
        # ``app`` was accepted by old httpx integrations but removed from
        # the HTTPX2 client API. Keep it working where possible.
        app = client_kwargs.pop("app", None)
        if app is not None:
            client_kwargs["transport"] = httpx2.ASGITransport(app=app)

        httpx2.AsyncClient.__init__(self, **client_kwargs)
        _OAuth1Client.__init__(
            self,
            None,
            client_id=client_id,
            client_secret=client_secret,
            token=token,
            token_secret=token_secret,
            redirect_uri=redirect_uri,
            rsa_key=rsa_key,
            verifier=verifier,
            signature_method=signature_method,
            signature_type=signature_type,
            force_include_body=force_include_body,
            **kwargs,
        )

    async def fetch_access_token(
        self, url: str, verifier: str | None = None, **kwargs: typing.Any
    ) -> dict:
        if verifier:
            self.auth.verifier = verifier
        if not self.auth.verifier:
            self.handle_error("missing_verifier", 'Missing "verifier" value')
        token = await self._fetch_token(url, **kwargs)
        self.auth.verifier = None
        return token

    async def _fetch_token(self, url: str, **kwargs: typing.Any) -> dict:
        response = await self.post(url, **kwargs)
        body = await response.aread()
        token = self.parse_response_token(response.status_code, to_unicode(body))
        self.token = token
        return token

    @staticmethod
    def handle_error(error_type: str, error_description: str) -> typing.NoReturn:
        raise OAuthError(error_type, error_description)


class OAuth1Client(_OAuth1Client, httpx2.Client):
    """Synchronous OAuth 1.0 client using HTTPX2's sync transport."""

    auth_class = OAuth1Auth

    def __init__(
        self,
        client_id: str,
        client_secret: str | None = None,
        token: str | None = None,
        token_secret: str | None = None,
        redirect_uri: str | None = None,
        rsa_key: str | None = None,
        verifier: str | None = None,
        signature_method: str = SIGNATURE_HMAC_SHA1,
        signature_type: str = SIGNATURE_TYPE_HEADER,
        force_include_body: bool = False,
        **kwargs: typing.Any,
    ) -> None:
        client_kwargs = _extract_client_kwargs(kwargs)
        # ``app`` was accepted by old httpx integrations but removed from
        # the HTTPX2 client API. Keep it working where possible.
        app = client_kwargs.pop("app", None)
        if app is not None:
            client_kwargs["transport"] = httpx2.WSGITransport(app=app)

        httpx2.Client.__init__(self, **client_kwargs)
        _OAuth1Client.__init__(
            self,
            self,
            client_id=client_id,
            client_secret=client_secret,
            token=token,
            token_secret=token_secret,
            redirect_uri=redirect_uri,
            rsa_key=rsa_key,
            verifier=verifier,
            signature_method=signature_method,
            signature_type=signature_type,
            force_include_body=force_include_body,
            **kwargs,
        )

    @staticmethod
    def handle_error(error_type: str, error_description: str) -> typing.NoReturn:
        raise OAuthError(error_type, error_description)


__all__ = ["AsyncOAuth1Client", "OAuth1Auth", "OAuth1Client"]
