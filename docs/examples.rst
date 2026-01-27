PyEtrade Examples
==================

PyEtrade provides both synchronous and asynchronous APIs for interacting with E*TRADE.

Important requirements
-----------------------

Getting access tokens requires the users `Consumer key` and `Consumer Secret`
obtained from E*TRADE. This applies equally to both the sandbox and Live
environments.

For the sandbox key, request a Sandbox consumer key via
`<https://us.etrade.com/etx/ris/apikey>`_ and for the Live/Production environment,
request a key through the E*TRADE secure message. Please refer
`E*TRADE Developer <https://developer.etrade.com/getting-started>`_ for
more information

The following examples assume you were successfully able to obtain the
`Consumer key` and `Consumer Secret` from E*TRADE.

Synchronous API Examples
=========================

Primary Authorization
----------------------

0.  Creating tokens (This step is required before performing any action
    on Etrade via PyEtrade

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade
    from pyetrade import OrderBuilder
    from pyetrade import OrderBuilder

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    # Using the EtradeOAuth object to retrive the URL to request tokens
    oauth = pyetrade.ETradeOAuth(consumer_key, consumer_secret)
    print(oauth.get_request_token())  # Use the printed URL

    # Use the printed URL to retrive Verification code
    verifier_code = input("Enter verification code: ")
    tokens = oauth.get_access_token(verifier_code)
    print(tokens)


Access Management
------------------

0.  Renewing access tokens

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    # Generated token from Step 0.
    tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
              'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

    # Setting up the object used for Access Management
    authManager = pyetrade.authorization.ETradeAccessManager(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret']
    )

    # Triggering a renew
    authManager.renew_access_token()

    # Triggering a Revoke
    authManager.revoke_access_token()


Accounts Management
--------------------

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
              'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

    # Setting up the object used for Accounts activity
    # Arg dev determines the environment Sandbox (dev=True)
    # or Live/Production (dev=False)
    accounts = pyetrade.ETradeAccounts(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret'],
        dev=True
    )

    # lists all the accounts for
    print(accounts.list_accounts(resp_format='json'))

    # The above produces a json with all the accounts and their
    # respective accountIDKeys

    accountIDKey = '<Key for the chosen account from list_accounts>'

    # Prints account balance
    print(accounts.get_account_balance(accountIDKey, resp_format='json'))

    # Gets account portfolio
    print(accounts.get_account_portfolio(accountIDKey, resp_format='json'))

    # Gets all transactions for an account
    print(accounts.list_transactions(accountIDKey, resp_format='json'))

    # The above produces a json with all the transactions for an account
    # and all their transaction IDs
    transactionID = '<Transaction ID for a specific transaction>'

    # Gets all transaction details for a transaction
    print(accounts.list_transaction_details(accountIDKey, transactionID, resp_format='json'))


Alerts Management
------------------

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
              'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

    # Setting up the object used for alerts activity
    # Arg dev determines the environment Sandbox (dev=True)
    # or Live/Production (dev=False)

    alerts = pyetrade.ETradeAlerts(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret'],
        dev=True
    )

    # Get all alerts
    print(alerts.list_alerts(resp_format='json'))

    # The above produces a json with all the alerts
    # and their alert IDs
    alertID = '<Specific alert ID>'

    # Get alert details
    print(alerts.list_alert_details(alert_id=alertID,  resp_format="json"))

    # Delete alert with ID alertID
    alerts.delete_alert(alert_id=alertID,  resp_format="json")


Market Module
--------------

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
              'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

    # Setting up the object used for alerts activity
    # Arg dev determines the environment Sandbox (dev=True)
    # or Live/Production (dev=False)

    market = pyetrade.ETradeMarket(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret'],
        dev=True
    )

    # Getting products symbol with search string
    print(market.look_up_product('alphabet', resp_format='json'))
    print(market.look_up_product('American', resp_format='json'))

    # Getting market quote
    print(market.get_quote(['GOOG'],resp_format='json'))

    # Getting Options chain with expiry_date=None
    print(market.get_option_chains('GOOG', expiry_date=None, resp_format='json'))


    # Getting Options chain with expiry_date specified with datetime
    import datetime as dt
    datt = dt.datetime(year=2020,month=10, day=16)

    print(market.get_option_chains('GOOG', expiry_date=datt, resp_format='json'))


Order Module
-------------

.. code-block:: python

    # Importing the pyetrade module
    import pyetrade

    # Obtained secrets from Etrade for Sandbox or Live
    consumer_key = "<CONSUMER_KEY>"
    consumer_secret = "<SECRET_KEY>"

    tokens = {'oauth_token': '<TOKEN FROM THE SCRIPT ABOVE>',
              'oauth_token_secret': '<TOKEN FROM THE SCRIPT ABOVE>'}

    # Setting up the object used for alerts activity
    # Arg dev determines the environment Sandbox (dev=True)
    # or Live/Production (dev=False)

    order_client = pyetrade.ETradeOrder(
        consumer_key,
        consumer_secret,
        tokens['oauth_token'],
        tokens['oauth_token_secret'],
        dev=True
    )

    # The above produces a json with all the accounts and their
    # respective accountIDKeys

    accountIDKey = '<Key for the chosen account from pyetrade.ETradeAccounts.list_accounts>'

    # Lists orders of a account
    print(order_client.list_orders(accountIDKey, resp_format='json'))

    # place option order via OrderBuilder:
    symbol = "PLTR"
    strikePrice = 23
    quantity = 1
    limitPrice = 1.97
    orderTerm = "GOOD_UNTIL_CANCEL"  # "IMMEDIATE_OR_CANCEL"  # "GOOD_FOR_DAY"
    marketSession = "REGULAR"
    clientOrderId = "ABC123456"  # Unique alphanumeric identifier to prevent duplicate submissions of the same order

    builder = (
        OrderBuilder.for_account(accountIDKey)
        .order_type("OPTN")
        .client_order_id(clientOrderId)
        .with_symbol(symbol)
        .with_expiry(2022, 2, 18)
        .add_long_put(strikePrice, qty=quantity)
        .limit(limitPrice)
        .order_term(orderTerm)
        .market_session(marketSession)
    )
    resp = order_client.preview_order_builder(builder, resp_format="xml")
    preview_id = resp["PreviewOrderResponse"]["PreviewIds"][0]["previewId"]
    resp = order_client.place_order_builder(builder, [preview_id], resp_format="xml")


Asynchronous API Examples
==========================

The async API provides the same functionality as the synchronous API but uses Python's
``async``/``await`` syntax for non-blocking I/O operations. All async classes are available
in the ``pyetrade.async_api`` module.

Primary Authorization (Async)
------------------------------

.. code-block:: python

    # Importing the async modules
    import asyncio
    from pyetrade.async_api.authorization import ETradeOAuth

    async def get_tokens():
        # Obtained secrets from Etrade for Sandbox or Live
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"

        # Using the async EtradeOAuth object
        oauth = ETradeOAuth(consumer_key, consumer_secret)
        print(await oauth.get_request_token())  # Use the printed URL

        # Use the printed URL to retrieve Verification code
        verifier_code = input("Enter verification code: ")
        tokens = await oauth.get_access_token(verifier_code)
        print(tokens)
        return tokens

    # Run the async function
    tokens = asyncio.run(get_tokens())


Access Management (Async)
--------------------------

.. code-block:: python

    import asyncio
    from pyetrade.async_api.authorization import ETradeAccessManager

    async def manage_tokens():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        # Setting up the async Access Manager
        authManager = ETradeAccessManager(
            consumer_key,
            consumer_secret,
            tokens['oauth_token'],
            tokens['oauth_token_secret']
        )

        # Renew access token
        await authManager.renew_access_token()

        # Revoke access token
        await authManager.revoke_access_token()

    asyncio.run(manage_tokens())


Accounts Management (Async)
----------------------------

.. code-block:: python

    import asyncio
    from pyetrade.async_api.accounts import ETradeAccounts

    async def get_account_info():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        # Create async accounts object
        accounts = ETradeAccounts(
            consumer_key,
            consumer_secret,
            tokens['oauth_token'],
            tokens['oauth_token_secret'],
            dev=True
        )

        # List all accounts
        account_list = await accounts.list_accounts(resp_format='json')
        print(account_list)

        accountIDKey = '<Account ID Key>'

        # Get account balance
        balance = await accounts.get_account_balance(accountIDKey, resp_format='json')
        print(balance)

        # Get account portfolio
        portfolio = await accounts.get_account_portfolio(accountIDKey, resp_format='json')
        print(portfolio)

        # List transactions
        transactions = await accounts.list_transactions(accountIDKey, resp_format='json')
        print(transactions)

    asyncio.run(get_account_info())


Market Module (Async)
----------------------

.. code-block:: python

    import asyncio
    import datetime as dt
    from pyetrade.async_api.market import ETradeMarket

    async def get_market_data():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        market = ETradeMarket(
            consumer_key,
            consumer_secret,
            tokens['oauth_token'],
            tokens['oauth_token_secret'],
            dev=True
        )

        # Look up product
        product = await market.look_up_product('alphabet', resp_format='json')
        print(product)

        # Get quote
        quote = await market.get_quote(['GOOG'], resp_format='json')
        print(quote)

        # Get option chains
        expiry = dt.datetime(year=2024, month=12, day=20)
        chains = await market.get_option_chains('GOOG', expiry_date=expiry, resp_format='json')
        print(chains)

    asyncio.run(get_market_data())


Order Module (Async)
---------------------

.. code-block:: python

    import asyncio
    from pyetrade.async_api.order import ETradeOrder

    async def manage_orders():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        order_client = ETradeOrder(
            consumer_key,
            consumer_secret,
            tokens['oauth_token'],
            tokens['oauth_token_secret'],
            dev=True
        )

        accountIDKey = '<Account ID Key>'

        # List orders
        order_list = await order_client.list_orders(accountIDKey, resp_format='json')
        print(order_list)

        # Preview equity order
        preview = await order_client.preview_equity_order(
            accountIdKey=accountIDKey,
            symbol="AAPL",
            orderAction="BUY",
            clientOrderId="ABC123",
            priceType="MARKET",
            quantity=10,
            orderTerm="GOOD_FOR_DAY",
            marketSession="REGULAR"
        )
        print(preview)

        # Place equity order (requires preview ID)
        order_response = await order_client.place_equity_order(
            accountIdKey=accountIDKey,
            symbol="AAPL",
            orderAction="BUY",
            clientOrderId="ABC123",
            priceType="MARKET",
            quantity=10,
            orderTerm="GOOD_FOR_DAY",
            marketSession="REGULAR"
        )
        print(order_response)

    asyncio.run(manage_orders())

Order Builder (Async)
----------------------

.. code-block:: python

    import asyncio
    from pyetrade import OrderBuilder
    from pyetrade.async_api.order import ETradeOrder

    async def manage_order_builder():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        order_client = ETradeOrder(
            consumer_key,
            consumer_secret,
            tokens['oauth_token'],
            tokens['oauth_token_secret'],
            dev=True
        )

        builder = (
            OrderBuilder.for_account("<ACCOUNT_ID_KEY>")
            .order_type("SPREADS")
            .client_order_id("spread-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
            .add_short_call(455.0)
            .net_debit(2.50)
            .gfd()
            .market_session("REGULAR")
        )

        preview = await order_client.preview_order_builder(builder, resp_format="json")
        preview_id = preview["PreviewOrderResponse"]["PreviewIds"][0]["previewId"]
        place = await order_client.place_order_builder(builder, [preview_id], resp_format="json")
        print(place)

    asyncio.run(manage_order_builder())


Concurrent Requests (Async)
----------------------------

One of the main benefits of the async API is the ability to make concurrent requests:

.. code-block:: python

    import asyncio
    from pyetrade.async_api.accounts import ETradeAccounts
    from pyetrade.async_api.market import ETradeMarket

    async def get_multiple_data():
        consumer_key = "<CONSUMER_KEY>"
        consumer_secret = "<SECRET_KEY>"
        tokens = {'oauth_token': '<TOKEN>',
                  'oauth_token_secret': '<TOKEN_SECRET>'}

        # Create clients
        accounts = ETradeAccounts(
            consumer_key, consumer_secret,
            tokens['oauth_token'], tokens['oauth_token_secret'],
            dev=True
        )
        market = ETradeMarket(
            consumer_key, consumer_secret,
            tokens['oauth_token'], tokens['oauth_token_secret'],
            dev=True
        )

        # Make concurrent requests
        account_list, quote_aapl, quote_goog = await asyncio.gather(
            accounts.list_accounts(resp_format='json'),
            market.get_quote(['AAPL'], resp_format='json'),
            market.get_quote(['GOOG'], resp_format='json')
        )

        print("Accounts:", account_list)
        print("AAPL Quote:", quote_aapl)
        print("GOOG Quote:", quote_goog)

    asyncio.run(get_multiple_data())
