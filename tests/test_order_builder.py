"""Tests for OrderBuilder class."""
import pytest
from datetime import date

from pyetrade.order_builder import OrderBuilder, OrderBuilderError


class TestOrderBuilderBasics:
    """Test basic OrderBuilder functionality."""

    def test_for_account_creates_instance(self):
        builder = OrderBuilder.for_account("test-account-123")
        assert builder.get_account_id_key() == "test-account-123"

    def test_client_order_id(self):
        builder = OrderBuilder.for_account("acct123").client_order_id("order-001")
        # Verify it's set (will be validated in build)
        assert builder._client_order_id == "order-001"

    def test_with_symbol(self):
        builder = OrderBuilder.for_account("acct123").with_symbol("SPY")
        assert builder._default_symbol == "SPY"

    def test_with_symbol_uppercase(self):
        builder = OrderBuilder.for_account("acct123").with_symbol("spy")
        assert builder._default_symbol == "SPY"

    def test_with_expiry(self):
        builder = OrderBuilder.for_account("acct123").with_expiry(2024, 12, 20)
        assert builder._default_expiry_year == 2024
        assert builder._default_expiry_month == 12
        assert builder._default_expiry_day == 20

    def test_with_expiry_date(self):
        expiry = date(2024, 12, 20)
        builder = OrderBuilder.for_account("acct123").with_expiry_date(expiry)
        assert builder._default_expiry_year == 2024
        assert builder._default_expiry_month == 12
        assert builder._default_expiry_day == 20

    def test_invalid_expiry_date_raises(self):
        builder = OrderBuilder.for_account("acct123")
        with pytest.raises(OrderBuilderError, match="Invalid expiry date"):
            builder.with_expiry(2024, 13, 1)  # Invalid month

    def test_order_type(self):
        builder = OrderBuilder.for_account("acct123").order_type("SPREADS")
        assert builder._order_type == "SPREADS"

    def test_invalid_order_type_raises(self):
        builder = OrderBuilder.for_account("acct123")
        with pytest.raises(OrderBuilderError, match="order_type must be one of"):
            builder.order_type("INVALID")


class TestOrderDetails:
    """Test order detail configuration."""

    def test_term_gfd(self):
        builder = OrderBuilder.for_account("acct123").gfd()
        assert builder._order_detail_fields["orderTerm"] == "GOOD_FOR_DAY"

    def test_term_gtc(self):
        builder = OrderBuilder.for_account("acct123").gtc()
        assert builder._order_detail_fields["orderTerm"] == "GOOD_UNTIL_CANCEL"

    def test_limit_price(self):
        builder = OrderBuilder.for_account("acct123").limit_price(5.50)
        assert builder._order_detail_fields["limitPrice"] == 5.50

    def test_limit_price_negative_raises(self):
        builder = OrderBuilder.for_account("acct123")
        with pytest.raises(OrderBuilderError, match="limit_price must be greater than 0"):
            builder.limit_price(-1.0)

    def test_net_credit(self):
        builder = OrderBuilder.for_account("acct123").net_credit(2.50)
        assert builder._order_detail_fields["priceType"] == "NET_CREDIT"
        assert builder._order_detail_fields["limitPrice"] == 2.50

    def test_net_debit(self):
        builder = OrderBuilder.for_account("acct123").net_debit(3.00)
        assert builder._order_detail_fields["priceType"] == "NET_DEBIT"
        assert builder._order_detail_fields["limitPrice"] == 3.00

    def test_market(self):
        builder = OrderBuilder.for_account("acct123").market()
        assert builder._order_detail_fields["priceType"] == "MARKET"

    def test_market_session(self):
        builder = OrderBuilder.for_account("acct123").market_session("EXTENDED")
        assert builder._order_detail_fields["marketSession"] == "EXTENDED"

    def test_all_or_none(self):
        builder = OrderBuilder.for_account("acct123").all_or_none(True)
        assert builder._order_detail_fields["allOrNone"] is True


class TestAddLegs:
    """Test adding individual legs."""

    def test_add_long_call(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0, qty=2)
        )
        assert len(builder._instruments) == 1
        leg = builder._instruments[0]
        assert leg["orderAction"] == "BUY_OPEN"
        assert leg["quantity"] == 2
        assert leg["Product"]["symbol"] == "SPY"
        assert leg["Product"]["callPut"] == "CALL"
        assert leg["Product"]["strikePrice"] == 450.0

    def test_add_short_call(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_short_call(455.0)
        )
        leg = builder._instruments[0]
        assert leg["orderAction"] == "SELL_OPEN"
        assert leg["Product"]["callPut"] == "CALL"

    def test_add_long_put(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_put(440.0)
        )
        leg = builder._instruments[0]
        assert leg["orderAction"] == "BUY_OPEN"
        assert leg["Product"]["callPut"] == "PUT"

    def test_add_short_put(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_short_put(435.0)
        )
        leg = builder._instruments[0]
        assert leg["orderAction"] == "SELL_OPEN"
        assert leg["Product"]["callPut"] == "PUT"

    def test_add_equity(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("AAPL")
            .add_equity("BUY", 100)
        )
        leg = builder._instruments[0]
        assert leg["orderAction"] == "BUY"
        assert leg["quantity"] == 100
        assert leg["Product"]["securityType"] == "EQ"

    def test_add_leg_without_symbol_raises(self):
        builder = OrderBuilder.for_account("acct123").with_expiry(2024, 12, 20)
        with pytest.raises(OrderBuilderError, match="Symbol is required"):
            builder.add_long_call(450.0)

    def test_add_leg_without_expiry_raises(self):
        builder = OrderBuilder.for_account("acct123").with_symbol("SPY")
        with pytest.raises(OrderBuilderError, match="Expiry date is required"):
            builder.add_long_call(450.0)


class TestStrategies:
    """Test strategy helper methods."""

    def test_bull_call_spread(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .client_order_id("test-001")
            .bull_call_spread(long_strike=450.0, short_strike=455.0)
        )
        assert builder._order_type == "SPREADS"
        assert len(builder._instruments) == 2
        # First leg is long call at lower strike
        assert builder._instruments[0]["orderAction"] == "BUY_OPEN"
        assert builder._instruments[0]["Product"]["strikePrice"] == 450.0
        # Second leg is short call at higher strike
        assert builder._instruments[1]["orderAction"] == "SELL_OPEN"
        assert builder._instruments[1]["Product"]["strikePrice"] == 455.0

    def test_bull_call_spread_invalid_strikes_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
        )
        with pytest.raises(OrderBuilderError, match="short_strike must be greater"):
            builder.bull_call_spread(long_strike=455.0, short_strike=450.0)

    def test_bear_put_spread(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .client_order_id("test-001")
            .bear_put_spread(long_strike=450.0, short_strike=445.0)
        )
        assert builder._order_type == "SPREADS"
        assert len(builder._instruments) == 2

    def test_iron_condor(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .client_order_id("ic-001")
            .iron_condor(
                put_long_strike=430.0,
                put_short_strike=440.0,
                call_short_strike=460.0,
                call_long_strike=470.0,
            )
        )
        assert builder._order_type == "IRON_CONDOR"
        assert len(builder._instruments) == 4

    def test_iron_condor_invalid_strikes_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
        )
        with pytest.raises(OrderBuilderError, match="Strikes must be in ascending order"):
            # Invalid: put_short > call_short
            builder.iron_condor(
                put_long_strike=430.0,
                put_short_strike=470.0,  # Wrong!
                call_short_strike=440.0,
                call_long_strike=480.0,
            )

    def test_box_spread(self):
        """Test box spread construction for SPX."""
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPX")
            .with_expiry(2024, 12, 20)
            .client_order_id("box-001")
            .box_spread(lower_strike=4500.0, upper_strike=4600.0)
        )
        assert builder._order_type == "IRON_CONDOR"  # Box uses IC order type
        assert len(builder._instruments) == 4

        # Verify structure: long call at lower, short call at upper,
        # long put at upper, short put at lower
        actions = [(i["orderAction"], i["Product"]["callPut"], i["Product"]["strikePrice"])
                   for i in builder._instruments]

        assert ("BUY_OPEN", "CALL", 4500.0) in actions
        assert ("SELL_OPEN", "CALL", 4600.0) in actions
        assert ("BUY_OPEN", "PUT", 4600.0) in actions
        assert ("SELL_OPEN", "PUT", 4500.0) in actions

    def test_box_spread_invalid_strikes_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPX")
            .with_expiry(2024, 12, 20)
        )
        with pytest.raises(OrderBuilderError, match="upper_strike must be greater"):
            builder.box_spread(lower_strike=4600.0, upper_strike=4500.0)

    def test_call_butterfly(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .client_order_id("bf-001")
            .call_butterfly(lower_strike=445.0, middle_strike=450.0, upper_strike=455.0)
        )
        assert builder._order_type == "BUTTERFLY"
        assert len(builder._instruments) == 3
        # Middle strike should have qty=2
        middle_leg = [i for i in builder._instruments if i["Product"]["strikePrice"] == 450.0][0]
        assert middle_leg["quantity"] == 2

    def test_buy_write(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .with_symbol("AAPL")
            .with_expiry(2024, 12, 20)
            .client_order_id("bw-001")
            .buy_write(shares=100, call_strike=180.0)
        )
        assert builder._order_type == "BUY_WRITES"
        assert len(builder._instruments) == 2
        # First is equity buy
        assert builder._instruments[0]["Product"]["securityType"] == "EQ"
        assert builder._instruments[0]["orderAction"] == "BUY"
        # Second is short call
        assert builder._instruments[1]["Product"]["securityType"] == "OPTN"
        assert builder._instruments[1]["orderAction"] == "SELL_OPEN"


class TestBuildRequest:
    """Test building preview and place requests."""

    def test_build_preview_request(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("SPREADS")
            .client_order_id("test-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
            .add_short_call(455.0)
            .net_debit(2.50)
            .gfd()
            .market_session("REGULAR")
        )
        request = builder.build_preview_request()

        assert request["orderType"] == "SPREADS"
        assert request["clientOrderId"] == "test-001"
        assert len(request["Order"]) == 1
        order = request["Order"][0]
        assert order["priceType"] == "NET_DEBIT"
        assert order["limitPrice"] == 2.50
        assert order["orderTerm"] == "GOOD_FOR_DAY"
        assert len(order["Instrument"]) == 2

    def test_build_preview_request_missing_account_raises(self):
        builder = OrderBuilder()
        with pytest.raises(OrderBuilderError, match="account_id_key is required"):
            builder.build_preview_request()

    def test_build_preview_request_missing_order_type_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .client_order_id("test-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
        )
        with pytest.raises(OrderBuilderError, match="order_type is required"):
            builder.build_preview_request()

    def test_build_preview_request_missing_client_order_id_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("OPTN")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
        )
        with pytest.raises(OrderBuilderError, match="client_order_id is required"):
            builder.build_preview_request()

    def test_build_preview_request_missing_instruments_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("OPTN")
            .client_order_id("test-001")
        )
        with pytest.raises(OrderBuilderError, match="At least one instrument"):
            builder.build_preview_request()

    def test_build_place_request(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("SPREADS")
            .client_order_id("test-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
            .add_short_call(455.0)
            .net_debit(2.50)
            .gfd()
        )
        request = builder.build_place_request([12345])

        assert request["orderType"] == "SPREADS"
        assert request["clientOrderId"] == "test-001"
        assert len(request["PreviewIds"]) == 1
        assert request["PreviewIds"][0]["previewId"] == 12345

    def test_build_place_request_with_dict_preview_id(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("OPTN")
            .client_order_id("test-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
        )
        request = builder.build_place_request([{"previewId": 67890}])
        assert request["PreviewIds"][0]["previewId"] == 67890

    def test_build_place_request_missing_preview_ids_raises(self):
        builder = (
            OrderBuilder.for_account("acct123")
            .order_type("OPTN")
            .client_order_id("test-001")
            .with_symbol("SPY")
            .with_expiry(2024, 12, 20)
            .add_long_call(450.0)
        )
        with pytest.raises(OrderBuilderError, match="At least one preview_id is required"):
            builder.build_place_request([])


class TestFluentChaining:
    """Test that fluent chaining works correctly."""

    def test_full_fluent_chain(self):
        """Test a complete fluent chain for a box spread on SPX."""
        request = (
            OrderBuilder.for_account("my-account-key")
            .client_order_id("spx-box-001")
            .with_symbol("SPX")
            .with_expiry(2024, 12, 20)
            .box_spread(4500.0, 4600.0)
            .net_debit(99.50)
            .gfd()
            .market_session("REGULAR")
            .build_preview_request()
        )

        assert request["orderType"] == "IRON_CONDOR"
        assert request["clientOrderId"] == "spx-box-001"
        order = request["Order"][0]
        assert order["priceType"] == "NET_DEBIT"
        assert order["limitPrice"] == 99.50
        assert order["orderTerm"] == "GOOD_FOR_DAY"
        assert order["marketSession"] == "REGULAR"
        assert len(order["Instrument"]) == 4
