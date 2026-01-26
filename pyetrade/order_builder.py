"""Order Builder for PyETrade.

This module provides a fluent API for building complex order types including
multi-leg options orders (spreads, butterflies, iron condors, box spreads).

Adapted from laravel-etrade's EtradeOrderBuilder pattern.
"""
from typing import Optional, List, Dict, Any, Union
from datetime import date
import logging

from .types import (
    OrderType,
    OrderAction,
    PriceType,
    MarketSession,
    OrderTerm,
    CallPut,
    SecurityType,
    QuantityType,
    ProductDict,
    InstrumentDict,
    OrderDetailDict,
    PreviewOrderRequestDict,
    PlaceOrderRequestDict,
    PreviewIdDict,
)

LOGGER = logging.getLogger(__name__)

# Valid values for validation
VALID_QUANTITY_TYPES = ("QUANTITY", "DOLLAR", "ALL_I_OWN")
VALID_ORDER_TERMS = (
    "GOOD_UNTIL_CANCEL",
    "GOOD_FOR_DAY",
    "GOOD_TILL_DATE",
    "IMMEDIATE_OR_CANCEL",
    "FILL_OR_KILL",
)
VALID_ORDER_TYPES = (
    "EQ",
    "OPTN",
    "SPREADS",
    "BUY_WRITES",
    "BUTTERFLY",
    "IRON_BUTTERFLY",
    "CONDOR",
    "IRON_CONDOR",
    "MF",
    "MMF",
)
VALID_PRICE_TYPES = (
    "MARKET",
    "LIMIT",
    "STOP",
    "STOP_LIMIT",
    "NET_DEBIT",
    "NET_CREDIT",
    "NET_EVEN",
    "MARKET_ON_OPEN",
    "MARKET_ON_CLOSE",
    "LIMIT_ON_OPEN",
    "LIMIT_ON_CLOSE",
)
VALID_MARKET_SESSIONS = ("REGULAR", "EXTENDED")
VALID_ORDER_ACTIONS = (
    "BUY",
    "SELL",
    "BUY_TO_COVER",
    "SELL_SHORT",
    "BUY_OPEN",
    "BUY_CLOSE",
    "SELL_OPEN",
    "SELL_CLOSE",
    "EXCHANGE",
)
VALID_SECURITY_TYPES = ("EQ", "OPTN", "MF", "MMF")


class OrderBuilderError(Exception):
    """Exception raised when order builder validation fails."""
    pass


class OrderBuilder:
    """Fluent builder for complex order types.

    This class provides a fluent API for constructing orders, particularly
    multi-leg options orders like spreads, butterflies, and iron condors.

    Example usage for a bull call spread:
        >>> builder = (OrderBuilder.for_account("account123")
        ...     .order_type("SPREADS")
        ...     .client_order_id("my-order-001")
        ...     .with_symbol("SPY")
        ...     .with_expiry(2024, 12, 20)
        ...     .add_long_call(450.0, qty=1)
        ...     .add_short_call(455.0, qty=1)
        ...     .net_debit(2.50)
        ...     .gfd())
        >>> preview_request = builder.build_preview_request()

    Example usage for a box spread on SPX:
        >>> builder = (OrderBuilder.for_account("account123")
        ...     .client_order_id("box-001")
        ...     .with_symbol("SPX")
        ...     .with_expiry(2024, 12, 20)
        ...     .box_spread(lower_strike=4500.0, upper_strike=4600.0))
        >>> preview_request = builder.build_preview_request()
    """

    def __init__(self) -> None:
        self._account_id_key: Optional[str] = None
        self._order_type: Optional[OrderType] = None
        self._client_order_id: Optional[str] = None
        self._order_id: Optional[int] = None
        self._default_symbol: Optional[str] = None
        self._default_expiry_year: Optional[int] = None
        self._default_expiry_month: Optional[int] = None
        self._default_expiry_day: Optional[int] = None
        self._default_security_type: SecurityType = "OPTN"
        self._default_quantity_type: QuantityType = "QUANTITY"
        self._instruments: List[InstrumentDict] = []
        self._order_detail_fields: Dict[str, Any] = {}

    @classmethod
    def for_account(cls, account_id_key: str) -> "OrderBuilder":
        """Create an OrderBuilder for the specified account.

        Args:
            account_id_key: The account ID key from list_accounts.

        Returns:
            A new OrderBuilder instance.
        """
        instance = cls()
        instance._account_id_key = account_id_key
        return instance

    # =========================================================================
    # Order Configuration Methods
    # =========================================================================

    def order_type(self, order_type: OrderType) -> "OrderBuilder":
        """Set the order type.

        Args:
            order_type: One of EQ, OPTN, SPREADS, BUY_WRITES, BUTTERFLY,
                       IRON_BUTTERFLY, CONDOR, IRON_CONDOR, MF, MMF.

        Returns:
            Self for method chaining.
        """
        self._assert_valid_enum(order_type, VALID_ORDER_TYPES, "order_type")
        self._order_type = order_type
        return self

    def client_order_id(self, client_order_id: str) -> "OrderBuilder":
        """Set a unique client order ID to prevent duplicate submissions.

        Args:
            client_order_id: Unique alphanumeric identifier.

        Returns:
            Self for method chaining.
        """
        self._client_order_id = client_order_id
        return self

    def order_id(self, order_id: int) -> "OrderBuilder":
        """Set the order ID for change order requests.

        Args:
            order_id: Existing order ID to modify.

        Returns:
            Self for method chaining.
        """
        self._order_id = order_id
        return self

    def with_symbol(self, symbol: str) -> "OrderBuilder":
        """Set the default symbol for all legs.

        Args:
            symbol: Stock/ETF/index symbol (e.g., "SPY", "SPX", "AAPL").

        Returns:
            Self for method chaining.
        """
        self._default_symbol = symbol.upper()
        return self

    def with_expiry(self, year: int, month: int, day: int) -> "OrderBuilder":
        """Set the default expiration date for option legs.

        Args:
            year: Expiration year (e.g., 2024).
            month: Expiration month (1-12).
            day: Expiration day (1-31).

        Returns:
            Self for method chaining.
        """
        self._assert_valid_expiry_date(year, month, day)
        self._default_expiry_year = year
        self._default_expiry_month = month
        self._default_expiry_day = day
        return self

    def with_expiry_date(self, expiry_date: date) -> "OrderBuilder":
        """Set the default expiration date using a date object.

        Args:
            expiry_date: Expiration date.

        Returns:
            Self for method chaining.
        """
        return self.with_expiry(expiry_date.year, expiry_date.month, expiry_date.day)

    # =========================================================================
    # Order Detail Methods
    # =========================================================================

    def term(self, order_term: OrderTerm) -> "OrderBuilder":
        """Set the order term (duration).

        Args:
            order_term: One of GOOD_UNTIL_CANCEL, GOOD_FOR_DAY, GOOD_TILL_DATE,
                       IMMEDIATE_OR_CANCEL, FILL_OR_KILL.

        Returns:
            Self for method chaining.
        """
        self._assert_valid_enum(order_term, VALID_ORDER_TERMS, "order_term")
        self._order_detail_fields["orderTerm"] = order_term
        return self

    def gfd(self) -> "OrderBuilder":
        """Set order term to Good For Day.

        Returns:
            Self for method chaining.
        """
        return self.term("GOOD_FOR_DAY")

    def gtc(self) -> "OrderBuilder":
        """Set order term to Good Until Cancel.

        Returns:
            Self for method chaining.
        """
        return self.term("GOOD_UNTIL_CANCEL")

    def price_type(self, price_type: PriceType) -> "OrderBuilder":
        """Set the price type.

        Args:
            price_type: Price type (MARKET, LIMIT, NET_DEBIT, NET_CREDIT, etc.).

        Returns:
            Self for method chaining.
        """
        self._assert_valid_enum(price_type, VALID_PRICE_TYPES, "price_type")
        self._order_detail_fields["priceType"] = price_type
        return self

    def limit_price(self, price: float) -> "OrderBuilder":
        """Set the limit price.

        Args:
            price: Limit price (must be positive).

        Returns:
            Self for method chaining.
        """
        self._assert_positive_float(price, "limit_price")
        self._order_detail_fields["limitPrice"] = price
        return self

    def stop_price(self, price: float) -> "OrderBuilder":
        """Set the stop price.

        Args:
            price: Stop price (must be non-negative).

        Returns:
            Self for method chaining.
        """
        self._assert_non_negative_float(price, "stop_price")
        self._order_detail_fields["stopPrice"] = price
        return self

    def net_credit(self, price: float) -> "OrderBuilder":
        """Set order as NET_CREDIT with the specified limit price.

        Use for credit spreads (receiving premium).

        Args:
            price: Credit amount to receive.

        Returns:
            Self for method chaining.
        """
        return self.price_type("NET_CREDIT").limit_price(price)

    def net_debit(self, price: float) -> "OrderBuilder":
        """Set order as NET_DEBIT with the specified limit price.

        Use for debit spreads (paying premium).

        Args:
            price: Debit amount to pay.

        Returns:
            Self for method chaining.
        """
        return self.price_type("NET_DEBIT").limit_price(price)

    def market(self) -> "OrderBuilder":
        """Set price type to MARKET.

        Warning: Market orders on options can result in poor fills.

        Returns:
            Self for method chaining.
        """
        return self.price_type("MARKET")

    def market_session(self, session: MarketSession) -> "OrderBuilder":
        """Set the market session.

        Args:
            session: REGULAR or EXTENDED.

        Returns:
            Self for method chaining.
        """
        self._assert_valid_enum(session, VALID_MARKET_SESSIONS, "market_session")
        self._order_detail_fields["marketSession"] = session
        return self

    def all_or_none(self, value: bool = True) -> "OrderBuilder":
        """Set all-or-none flag.

        Args:
            value: If True, order must fill completely or not at all.

        Returns:
            Self for method chaining.
        """
        self._order_detail_fields["allOrNone"] = value
        return self

    # =========================================================================
    # Add Individual Legs
    # =========================================================================

    def add_instrument(self, instrument: InstrumentDict) -> "OrderBuilder":
        """Add a raw instrument (leg) to the order.

        Args:
            instrument: Instrument dictionary.

        Returns:
            Self for method chaining.
        """
        self._instruments.append(instrument)
        return self

    def add_long_call(
        self,
        strike_price: float,
        qty: int = 1,
        symbol: Optional[str] = None,
        expiry_year: Optional[int] = None,
        expiry_month: Optional[int] = None,
        expiry_day: Optional[int] = None,
    ) -> "OrderBuilder":
        """Add a long call option leg (BUY_OPEN).

        Args:
            strike_price: Strike price of the call.
            qty: Number of contracts.
            symbol: Override default symbol.
            expiry_year: Override default expiry year.
            expiry_month: Override default expiry month.
            expiry_day: Override default expiry day.

        Returns:
            Self for method chaining.
        """
        return self._add_option_leg(
            "CALL", "BUY_OPEN", strike_price, qty,
            symbol, expiry_year, expiry_month, expiry_day
        )

    def add_short_call(
        self,
        strike_price: float,
        qty: int = 1,
        symbol: Optional[str] = None,
        expiry_year: Optional[int] = None,
        expiry_month: Optional[int] = None,
        expiry_day: Optional[int] = None,
    ) -> "OrderBuilder":
        """Add a short call option leg (SELL_OPEN).

        Args:
            strike_price: Strike price of the call.
            qty: Number of contracts.
            symbol: Override default symbol.
            expiry_year: Override default expiry year.
            expiry_month: Override default expiry month.
            expiry_day: Override default expiry day.

        Returns:
            Self for method chaining.
        """
        return self._add_option_leg(
            "CALL", "SELL_OPEN", strike_price, qty,
            symbol, expiry_year, expiry_month, expiry_day
        )

    def add_long_put(
        self,
        strike_price: float,
        qty: int = 1,
        symbol: Optional[str] = None,
        expiry_year: Optional[int] = None,
        expiry_month: Optional[int] = None,
        expiry_day: Optional[int] = None,
    ) -> "OrderBuilder":
        """Add a long put option leg (BUY_OPEN).

        Args:
            strike_price: Strike price of the put.
            qty: Number of contracts.
            symbol: Override default symbol.
            expiry_year: Override default expiry year.
            expiry_month: Override default expiry month.
            expiry_day: Override default expiry day.

        Returns:
            Self for method chaining.
        """
        return self._add_option_leg(
            "PUT", "BUY_OPEN", strike_price, qty,
            symbol, expiry_year, expiry_month, expiry_day
        )

    def add_short_put(
        self,
        strike_price: float,
        qty: int = 1,
        symbol: Optional[str] = None,
        expiry_year: Optional[int] = None,
        expiry_month: Optional[int] = None,
        expiry_day: Optional[int] = None,
    ) -> "OrderBuilder":
        """Add a short put option leg (SELL_OPEN).

        Args:
            strike_price: Strike price of the put.
            qty: Number of contracts.
            symbol: Override default symbol.
            expiry_year: Override default expiry year.
            expiry_month: Override default expiry month.
            expiry_day: Override default expiry day.

        Returns:
            Self for method chaining.
        """
        return self._add_option_leg(
            "PUT", "SELL_OPEN", strike_price, qty,
            symbol, expiry_year, expiry_month, expiry_day
        )

    def add_equity(
        self,
        order_action: OrderAction,
        qty: int,
        symbol: Optional[str] = None,
    ) -> "OrderBuilder":
        """Add an equity leg (for buy-writes, etc.).

        Args:
            order_action: BUY, SELL, BUY_TO_COVER, SELL_SHORT.
            qty: Number of shares.
            symbol: Override default symbol.

        Returns:
            Self for method chaining.
        """
        self._assert_valid_enum(order_action, VALID_ORDER_ACTIONS, "order_action")
        self._assert_positive_float(float(qty), "qty")

        sym = symbol or self._default_symbol
        if not sym:
            raise OrderBuilderError("Symbol is required. Use with_symbol() or pass symbol parameter.")

        instrument: InstrumentDict = {
            "orderAction": order_action,
            "quantityType": self._default_quantity_type,
            "quantity": qty,
            "orderedQuantity": qty,
            "Product": {
                "symbol": sym,
                "securityType": "EQ",
            },
        }
        return self.add_instrument(instrument)

    # =========================================================================
    # Strategy Helpers (Multi-Leg Shortcuts)
    # =========================================================================

    def bull_call_spread(
        self,
        long_strike: float,
        short_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a bull call spread (debit spread).

        Buys the lower strike call, sells the higher strike call.

        Args:
            long_strike: Strike price for the long call (lower).
            short_strike: Strike price for the short call (higher).
            qty: Number of spreads.

        Returns:
            Self for method chaining.
        """
        if short_strike <= long_strike:
            raise OrderBuilderError("short_strike must be greater than long_strike for bull call spread")
        self.order_type("SPREADS")
        self.add_long_call(long_strike, qty)
        self.add_short_call(short_strike, qty)
        return self

    def bear_call_spread(
        self,
        short_strike: float,
        long_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a bear call spread (credit spread).

        Sells the lower strike call, buys the higher strike call.

        Args:
            short_strike: Strike price for the short call (lower).
            long_strike: Strike price for the long call (higher).
            qty: Number of spreads.

        Returns:
            Self for method chaining.
        """
        if long_strike <= short_strike:
            raise OrderBuilderError("long_strike must be greater than short_strike for bear call spread")
        self.order_type("SPREADS")
        self.add_short_call(short_strike, qty)
        self.add_long_call(long_strike, qty)
        return self

    def bull_put_spread(
        self,
        short_strike: float,
        long_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a bull put spread (credit spread).

        Sells the higher strike put, buys the lower strike put.

        Args:
            short_strike: Strike price for the short put (higher).
            long_strike: Strike price for the long put (lower).
            qty: Number of spreads.

        Returns:
            Self for method chaining.
        """
        if short_strike <= long_strike:
            raise OrderBuilderError("short_strike must be greater than long_strike for bull put spread")
        self.order_type("SPREADS")
        self.add_short_put(short_strike, qty)
        self.add_long_put(long_strike, qty)
        return self

    def bear_put_spread(
        self,
        long_strike: float,
        short_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a bear put spread (debit spread).

        Buys the higher strike put, sells the lower strike put.

        Args:
            long_strike: Strike price for the long put (higher).
            short_strike: Strike price for the short put (lower).
            qty: Number of spreads.

        Returns:
            Self for method chaining.
        """
        if long_strike <= short_strike:
            raise OrderBuilderError("long_strike must be greater than short_strike for bear put spread")
        self.order_type("SPREADS")
        self.add_long_put(long_strike, qty)
        self.add_short_put(short_strike, qty)
        return self

    def iron_condor(
        self,
        put_long_strike: float,
        put_short_strike: float,
        call_short_strike: float,
        call_long_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create an iron condor (4-leg credit strategy).

        Structure (from low to high strike):
        - Long put at put_long_strike
        - Short put at put_short_strike
        - Short call at call_short_strike
        - Long call at call_long_strike

        Args:
            put_long_strike: Lower put (protection).
            put_short_strike: Higher put (sold).
            call_short_strike: Lower call (sold).
            call_long_strike: Higher call (protection).
            qty: Number of iron condors.

        Returns:
            Self for method chaining.
        """
        # Validate strike ordering
        if not (put_long_strike < put_short_strike < call_short_strike < call_long_strike):
            raise OrderBuilderError(
                "Strikes must be in ascending order: put_long < put_short < call_short < call_long"
            )
        self.order_type("IRON_CONDOR")
        self.add_long_put(put_long_strike, qty)
        self.add_short_put(put_short_strike, qty)
        self.add_short_call(call_short_strike, qty)
        self.add_long_call(call_long_strike, qty)
        return self

    def box_spread(
        self,
        lower_strike: float,
        upper_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a box spread (4-leg arbitrage strategy).

        A box spread is commonly used on cash-settled index options like SPX
        for financing purposes. It creates a synthetic loan.

        Structure:
        - Long call at lower strike
        - Short call at upper strike
        - Long put at upper strike
        - Short put at lower strike

        The value at expiration equals (upper_strike - lower_strike) * 100 * qty.

        Args:
            lower_strike: Lower strike price for the box.
            upper_strike: Upper strike price for the box.
            qty: Number of box spreads.

        Returns:
            Self for method chaining.

        Example for SPX:
            >>> builder = (OrderBuilder.for_account("acct123")
            ...     .client_order_id("box-001")
            ...     .with_symbol("SPX")
            ...     .with_expiry(2024, 12, 20)
            ...     .box_spread(4500.0, 4600.0)
            ...     .net_debit(99.50)  # Borrow at ~0.5% implied rate
            ...     .gfd())
        """
        if upper_strike <= lower_strike:
            raise OrderBuilderError("upper_strike must be greater than lower_strike for box spread")

        # Box spread uses IRON_CONDOR order type in E*Trade API
        self.order_type("IRON_CONDOR")

        # Bull call spread component
        self.add_long_call(lower_strike, qty)
        self.add_short_call(upper_strike, qty)

        # Bear put spread component
        self.add_long_put(upper_strike, qty)
        self.add_short_put(lower_strike, qty)

        return self

    def call_butterfly(
        self,
        lower_strike: float,
        middle_strike: float,
        upper_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a call butterfly spread (3-leg).

        Structure:
        - Long 1 call at lower strike
        - Short 2 calls at middle strike
        - Long 1 call at upper strike

        Args:
            lower_strike: Lower wing strike.
            middle_strike: Body strike (ATM).
            upper_strike: Upper wing strike.
            qty: Number of butterflies.

        Returns:
            Self for method chaining.
        """
        if not (lower_strike < middle_strike < upper_strike):
            raise OrderBuilderError("Strikes must be in ascending order: lower < middle < upper")
        self.order_type("BUTTERFLY")
        self.add_long_call(lower_strike, qty)
        self.add_short_call(middle_strike, qty * 2)
        self.add_long_call(upper_strike, qty)
        return self

    def put_butterfly(
        self,
        lower_strike: float,
        middle_strike: float,
        upper_strike: float,
        qty: int = 1,
    ) -> "OrderBuilder":
        """Create a put butterfly spread (3-leg).

        Structure:
        - Long 1 put at lower strike
        - Short 2 puts at middle strike
        - Long 1 put at upper strike

        Args:
            lower_strike: Lower wing strike.
            middle_strike: Body strike (ATM).
            upper_strike: Upper wing strike.
            qty: Number of butterflies.

        Returns:
            Self for method chaining.
        """
        if not (lower_strike < middle_strike < upper_strike):
            raise OrderBuilderError("Strikes must be in ascending order: lower < middle < upper")
        self.order_type("BUTTERFLY")
        self.add_long_put(lower_strike, qty)
        self.add_short_put(middle_strike, qty * 2)
        self.add_long_put(upper_strike, qty)
        return self

    def buy_write(
        self,
        shares: int,
        call_strike: float,
        contracts: int = 1,
    ) -> "OrderBuilder":
        """Create a buy-write (covered call) order.

        Buys stock and sells calls against it.

        Args:
            shares: Number of shares to buy (usually 100 per contract).
            call_strike: Strike price of calls to sell.
            contracts: Number of call contracts to sell.

        Returns:
            Self for method chaining.
        """
        self.order_type("BUY_WRITES")
        self.add_equity("BUY", shares)
        self.add_short_call(call_strike, contracts)
        return self

    # =========================================================================
    # Build Methods
    # =========================================================================

    def build_preview_request(self) -> PreviewOrderRequestDict:
        """Build the preview order request payload.

        Returns:
            Dictionary suitable for preview order API call.

        Raises:
            OrderBuilderError: If required fields are missing.
        """
        self._assert_required_for_preview()

        order_detail: OrderDetailDict = {
            **self._order_detail_fields,
            "Instrument": self._instruments,
        }

        request: PreviewOrderRequestDict = {
            "orderType": self._order_type,
            "clientOrderId": self._client_order_id,
            "Order": [order_detail],
        }

        return request

    def build_place_request(
        self,
        preview_ids: List[Union[int, PreviewIdDict]],
    ) -> PlaceOrderRequestDict:
        """Build the place order request payload.

        Args:
            preview_ids: List of preview IDs from the preview response.

        Returns:
            Dictionary suitable for place order API call.

        Raises:
            OrderBuilderError: If required fields are missing.
        """
        self._assert_required_for_preview()
        if not preview_ids:
            raise OrderBuilderError("At least one preview_id is required to place an order.")

        # Normalize preview IDs
        normalized_ids: List[PreviewIdDict] = []
        for pid in preview_ids:
            if isinstance(pid, int):
                normalized_ids.append({"previewId": pid})
            else:
                normalized_ids.append(pid)

        order_detail: OrderDetailDict = {
            **self._order_detail_fields,
            "Instrument": self._instruments,
        }

        request: PlaceOrderRequestDict = {
            "orderType": self._order_type,
            "clientOrderId": self._client_order_id,
            "Order": [order_detail],
            "PreviewIds": normalized_ids,
        }

        return request

    def get_account_id_key(self) -> Optional[str]:
        """Get the account ID key for this order."""
        return self._account_id_key

    def get_order_id(self) -> Optional[int]:
        """Get the order ID for change order requests."""
        return self._order_id

    # =========================================================================
    # Private Helper Methods
    # =========================================================================

    def _add_option_leg(
        self,
        call_put: CallPut,
        order_action: OrderAction,
        strike_price: float,
        qty: int,
        symbol: Optional[str],
        expiry_year: Optional[int],
        expiry_month: Optional[int],
        expiry_day: Optional[int],
    ) -> "OrderBuilder":
        """Internal method to add an option leg."""
        self._assert_valid_enum(order_action, VALID_ORDER_ACTIONS, "order_action")
        self._assert_positive_float(strike_price, "strike_price")
        self._assert_positive_float(float(qty), "qty")

        sym = symbol or self._default_symbol
        year = expiry_year or self._default_expiry_year
        month = expiry_month or self._default_expiry_month
        day = expiry_day or self._default_expiry_day

        if not sym:
            raise OrderBuilderError("Symbol is required. Use with_symbol() or pass symbol parameter.")
        if year is None or month is None or day is None:
            raise OrderBuilderError("Expiry date is required. Use with_expiry() or pass expiry parameters.")

        self._assert_valid_expiry_date(year, month, day)

        instrument: InstrumentDict = {
            "orderAction": order_action,
            "quantityType": self._default_quantity_type,
            "quantity": qty,
            "orderedQuantity": qty,
            "Product": {
                "symbol": sym,
                "securityType": self._default_security_type,
                "callPut": call_put,
                "expiryYear": year,
                "expiryMonth": month,
                "expiryDay": day,
                "strikePrice": strike_price,
            },
        }
        return self.add_instrument(instrument)

    def _assert_valid_enum(self, value: str, allowed: tuple, field: str) -> None:
        """Validate that a value is in the allowed set."""
        if value not in allowed:
            raise OrderBuilderError(
                f"{field} must be one of: {', '.join(allowed)}"
            )

    def _assert_valid_expiry_date(self, year: int, month: int, day: int) -> None:
        """Validate expiry date is valid."""
        try:
            date(year, month, day)
        except ValueError as e:
            raise OrderBuilderError(f"Invalid expiry date: {e}")

    def _assert_positive_float(self, value: float, field: str) -> None:
        """Validate that a value is positive."""
        if value <= 0:
            raise OrderBuilderError(f"{field} must be greater than 0")

    def _assert_non_negative_float(self, value: float, field: str) -> None:
        """Validate that a value is non-negative."""
        if value < 0:
            raise OrderBuilderError(f"{field} must be 0 or greater")

    def _assert_required_for_preview(self) -> None:
        """Validate required fields for preview."""
        if not self._account_id_key:
            raise OrderBuilderError("account_id_key is required. Use for_account().")
        if not self._order_type:
            raise OrderBuilderError("order_type is required. Use order_type() or a strategy helper.")
        if not self._client_order_id:
            raise OrderBuilderError("client_order_id is required. Use client_order_id().")
        if not self._instruments:
            raise OrderBuilderError("At least one instrument/leg is required.")
