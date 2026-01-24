#!/usr/bin/env python3
"""pyetrade authorization unit tests
   TODO:
    * add more mock tests for revoke
    * add more mock tests for renew"""
import unittest
from unittest.mock import patch

from pyetrade import authorization


class TestETradeAuthorization(unittest.TestCase):
    """TestEtradeAuthorization Unit Test"""

    # Mock out OAuth1Client
    @patch("pyetrade.authorization.OAuth1Client")
    def test_get_request_token(self, MockOAuthClient):
        """test_get_request_token(self, MockOAuthClient)"""
        # Set Mock returns
        MockOAuthClient.return_value.fetch_request_token.return_value = None
        MockOAuthClient.return_value.token = {"oauth_token": "abc123"}
        MockOAuthClient.return_value.create_authorization_url.return_value = (
            "https://us.etrade.com/e/t/etws/authorize?key=xyz321&token=abc123"
        )

        # Setup authorization
        oauth = authorization.ETradeOAuth("xyz321", "secret")
        self.assertEqual(
            oauth.get_request_token(),
            "https://us.etrade.com/e/t/etws/authorize?key=xyz321&token=abc123",
        )
        self.assertTrue(MockOAuthClient.return_value.fetch_request_token.called)

    # Mock out OAuth1Client
    @patch("pyetrade.authorization.OAuth1Client")
    def test_get_access_token(self, MockOAuthClient):
        """test_get_access_token(self, MockOAuthClient)"""
        
        # Define side effect to update token when fetch_access_token is called
        def fetch_access_token_side_effect(*args, **kwargs):
            MockOAuthClient.return_value.token = {
                "oauth_token": "abc",
                "oauth_token_secret": "xyz",
            }
            return MockOAuthClient.return_value.token

        MockOAuthClient.return_value.fetch_access_token.side_effect = fetch_access_token_side_effect

        # Initial state (request token)
        MockOAuthClient.return_value.fetch_request_token.return_value = None
        MockOAuthClient.return_value.token = {"oauth_token": "abc123"} 
        
        oauth = authorization.ETradeOAuth("xyz321", "secret")
        
        # This uses the initial token
        oauth.get_request_token()
        
        # This triggers the side effect, verifying that get_access_token returns the NEW token
        self.assertEqual(
            oauth.get_access_token("abcxyz"),
            {"oauth_token": "abc", "oauth_token_secret": "xyz"},
        )
        self.assertTrue(MockOAuthClient.return_value.fetch_access_token.called)


class TestETradeAccessManager(unittest.TestCase):
    @patch("pyetrade.authorization.OAuth1Client")
    def test_renew_access_token(self, MockOAuthClient):
        # httpx Client returns a Response object
        MockOAuthClient.return_value.get.return_value.status_code = 200
        MockOAuthClient.return_value.get.return_value.text = "success"

        oauth = authorization.ETradeAccessManager(
            "xyz321", "secret", "abc123", "super_secret"
        )
        self.assertTrue(oauth.renew_access_token())
        self.assertTrue(MockOAuthClient.return_value.get.called)

    @patch("pyetrade.authorization.OAuth1Client")
    def test_revoke_access_token(self, MockOAuthClient):
        # httpx Client returns a Response object
        MockOAuthClient.return_value.get.return_value.status_code = 200
        MockOAuthClient.return_value.get.return_value.text = "success"
        
        oauth = authorization.ETradeAccessManager(
            "xyz321", "secret", "abc123", "super_secret"
        )
        self.assertTrue(oauth.revoke_access_token())
        self.assertTrue(MockOAuthClient.return_value.get.called)
