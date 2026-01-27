# pyetrade (Python E-Trade API Wrapper)

[![PyPI](https://img.shields.io/pypi/v/pyetrade.svg)](https://pypi.python.org/pypi/pyetrade)
[![PyPI](https://img.shields.io/pypi/l/pyetrade.svg)]()
[![PyPI](https://img.shields.io/pypi/pyversions/pyetrade.svg)](https://pypi.python.org/pypi/pyetrade)
[![Build Status](https://github.com/jessecooper/pyetrade/actions/workflows/build.yml/badge.svg?branch=master)](https://github.com/jessecooper/pyetrade/actions/workflows/build.yml/badge.svg?branch=master)
[![codecov](https://codecov.io/gh/jessecooper/pyetrade/branch/master/graph/badge.svg)](https://codecov.io/gh/jessecooper/pyetrade)

Python E-Trade API Wrapper with support for both **synchronous** and **asynchronous** operations using `httpx` and `authlib`.

## Completed

* Authorization API (OAuth)
  * get_request_token
  * get_access_token
  * renew_access_token
  * revoke_access_token


* Alerts API
  * list_alerts
  * list_alert_details
  * delete_alert


* Accounts API
  * list_accounts
  * get_account_balance
  * get_account_portfolio
  * get_portfolio_position_lot
  * list_transactions
  * list_transaction_details


* Order API
  * list_orders
  * list_order_details
  * find_option_orders
  * preview_equity_order
  * change_preview_equity_order
  * place_equity_order
  * place_changed_equity_order
  * place_changed_option_order
  * cancel_order


* Market API
  * look_up_product
  * get_quote
  * get_option_chains
  * get_option_expire_date

* **NEW: Multi-Leg Options via OrderBuilder**
  * Spreads (bull/bear call/put)
  * Butterflies (call/put)
  * Iron Condors
  * Box Spreads (for SPX financing)
  * Buy-Writes (covered calls)

## Install

```bash
pip install pyetrade
```

**Dependencies:**
- `httpx` - Modern HTTP client with sync and async support
- `authlib` - OAuth 1.0a authentication
- `xmltodict` - XML parsing
- `jxmlease` - XML generation (for orders)

OR install from source:
```bash
git clone https://github.com/jessecooper/pyetrade.git
cd pyetrade
sudo make init
sudo make install
```

## Example Usage

### Synchronous API

To create the OAuth tokens:

```python
import pyetrade

consumer_key = "<CONSUMER_KEY>"
consumer_secret = "<SECRET_KEY>"

oauth = pyetrade.ETradeOAuth(consumer_key, consumer_secret)
print(oauth.get_request_token())  # Use the printed URL

verifier_code = input("Enter verification code: ")
tokens = oauth.get_access_token(verifier_code)

print(tokens)
```

Using the API:

```python
import pyetrade

consumer_key = "<CONSUMER_KEY>"
consumer_secret = "<SECRET_KEY>"
tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
          'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

accounts = pyetrade.ETradeAccounts(
    consumer_key,
    consumer_secret,
    tokens['oauth_token'],
    tokens['oauth_token_secret']
)

print(accounts.list_accounts())
```

### Asynchronous API

For async operations, import from `pyetrade.async_api`:

```python
import asyncio
from pyetrade.async_api.authorization import ETradeOAuth
from pyetrade.async_api.accounts import ETradeAccounts

async def main():
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"
    
    # OAuth flow
    oauth = ETradeOAuth(consumer_key, consumer_secret)
    print(await oauth.get_request_token())  # Use the printed URL
    
    verifier_code = input("Enter verification code: ")
    tokens = await oauth.get_access_token(verifier_code)
    
    # Use the API
    accounts = ETradeAccounts(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret']
    )
    
    account_list = await accounts.list_accounts()
    print(account_list)

asyncio.run(main())
```

**Available async modules:**
- `pyetrade.async_api.authorization` - OAuth and access management
- `pyetrade.async_api.accounts` - Account information and transactions
- `pyetrade.async_api.market` - Market data and quotes
- `pyetrade.async_api.order` - Order management
- `pyetrade.async_api.alerts` - Alert management

### Multi-Leg Options with OrderBuilder

Use the `OrderBuilder` class for complex multi-leg options orders:

```python
from pyetrade import OrderBuilder

# Create a bull call spread
builder = (
    OrderBuilder.for_account(account_id_key)
    .client_order_id("spread-001")
    .with_symbol("SPY")
    .with_expiry(2024, 12, 20)
    .bull_call_spread(long_strike=450.0, short_strike=455.0)
    .net_debit(2.50)
    .gfd()
    .market_session("REGULAR")
)

# Build the preview request
preview_request = builder.build_preview_request()

# Use with ETradeOrder to submit
orders = pyetrade.ETradeOrder(consumer_key, consumer_secret, token, token_secret)
# ... submit using perform_request with the preview_request payload
```

**Box Spread Example (SPX Financing):**

```python
from pyetrade import OrderBuilder

# Create a box spread on SPX for synthetic borrowing
builder = (
    OrderBuilder.for_account(account_id_key)
    .client_order_id("spx-box-001")
    .with_symbol("SPX")
    .with_expiry(2024, 12, 20)
    .box_spread(lower_strike=4500.0, upper_strike=4600.0)
    .net_debit(99.50)  # Pay $9,950 to receive $10,000 at expiry
    .gfd()
)

preview_request = builder.build_preview_request()
```

**Available Strategies:**
- `bull_call_spread()`, `bear_call_spread()`, `bull_put_spread()`, `bear_put_spread()`
- `iron_condor()` - 4-leg credit strategy
- `box_spread()` - 4-leg arbitrage/financing (ideal for SPX)
- `call_butterfly()`, `put_butterfly()` - 3-leg strategies
- `buy_write()` - Covered call (stock + short call)

## Documentation

[PyEtrade Documentation](https://pyetrade.readthedocs.io/en/latest/)

## Contribute to pyetrade

[ETrade API Docs](https://apisb.etrade.com/docs/api/account/api-account-v1.html)

### Development Setup:

* Fork pyetrade
* Setup development environment

```bash
make init
make devel
```
OR
```bash
pip install -r requirements.txt
pip install -r requirements_dev.txt
pip install -e .
pre-commit install --hook-type pre-commit --hook-type pre-push --install-hooks -t post-checkout -t post-merge
```

* Lint (Run analysis - pre-commit-config)

```bash
make analysis
```

* Test (Coverage >= 90%)

```bash
make test
```

* Push Changes
  * Push changes to a branch on your forked repo


* Create pull request
  * Open a pull request on pyetrade and put your fork as the source of your changes
