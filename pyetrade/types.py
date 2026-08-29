"""Type definitions for PyETrade.

This module provides comprehensive type hints using Literals and TypedDicts
for improved IDE autocomplete and type safety.
"""

from typing import Literal, TypedDict, Optional, List, Union
from datetime import datetime

# ============================================================================
# Literal Types for API Enums
# ============================================================================

# Response format
ResponseFormat = Literal["xml", "json"]

# Order actions
OrderAction = Literal[
    "BUY",
    "SELL",
    "BUY_TO_COVER",
    "SELL_SHORT",
    "BUY_OPEN",
    "BUY_CLOSE",
    "SELL_OPEN",
    "SELL_CLOSE",
    "EXCHANGE",
]

# Order types
OrderType = Literal[
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
]

# Price types
PriceType = Literal[
    "MARKET",
    "LIMIT",
    "STOP",
    "STOP_LIMIT",
    "TRAILING_STOP_CNST_BY_LOWER_TRIGGER",
    "UPPER_TRIGGER_BY_TRAILING_STOP_CNST",
    "TRAILING_STOP_PRCT_BY_LOWER_TRIGGER",
    "UPPER_TRIGGER_BY_TRAILING_STOP_PRCT",
    "TRAILING_STOP_CNST",
    "TRAILING_STOP_PRCT",
    "HIDDEN_STOP",
    "HIDDEN_STOP_BY_LOWER_TRIGGER",
    "UPPER_TRIGGER_BY_HIDDEN_STOP",
    "NET_DEBIT",
    "NET_CREDIT",
    "NET_EVEN",
    "MARKET_ON_OPEN",
    "MARKET_ON_CLOSE",
    "LIMIT_ON_OPEN",
    "LIMIT_ON_CLOSE",
]

# Market session
MarketSession = Literal["REGULAR", "EXTENDED"]

# Order term
OrderTerm = Literal[
    "GOOD_UNTIL_CANCEL",
    "GOOD_FOR_DAY",
    "GOOD_TILL_DATE",
    "IMMEDIATE_OR_CANCEL",
    "FILL_OR_KILL",
]

# Call/Put
CallPut = Literal["CALL", "PUT"]

# Security type
SecurityType = Literal["EQ", "OPTN", "MF", "MMF"]

# Quantity type
QuantityType = Literal["QUANTITY", "DOLLAR", "ALL_I_OWN"]

# Order status
OrderStatus = Literal[
    "OPEN",
    "EXECUTED",
    "CANCELLED",
    "INDIVIDUAL_FILLS",
    "CANCEL_REQUESTED",
    "EXPIRED",
    "REJECTED",
    "PARTIAL",
    "DO_NOT_EXERCISE",
    "DONE_TRADE_EXECUTED",
]

# Transaction type
TransactionType = Literal[
    "APTS",
    "BOUGHT",
    "SOLD",
    "SOLD_SHORT",
    "COVER",
    "ASSIGN",
    "EXERCISE",
    "EXPIRE",
    "DIVIDEND",
    "INTEREST",
    "TRANSFER",
    "MARGIN_INTEREST",
    "OTHER",
]

# Sort order
SortOrder = Literal["ASC", "DESC"]

# Portfolio view
PortfolioView = Literal[
    "PERFORMANCE",
    "FUNDAMENTAL",
    "OPTIONSWATCH",
    "QUICK",
    "COMPLETE",
]

# Detail flag for quotes
DetailFlag = Literal[
    "FUNDAMENTAL",
    "INTRADAY",
    "OPTIONS",
    "WEEK_52",
    "MF_DETAIL",
    "ALL",
]

# Alert status
AlertStatus = Literal["READ", "UNREAD", "DELETED"]


# ============================================================================
# TypedDicts for API Request/Response Structures
# ============================================================================


class ProductDict(TypedDict, total=False):
    """Product information for an instrument."""

    symbol: str
    securityType: SecurityType
    callPut: CallPut
    expiryYear: int
    expiryMonth: int
    expiryDay: int
    strikePrice: float


class InstrumentDict(TypedDict, total=False):
    """Instrument (leg) in an order."""

    Product: ProductDict
    orderAction: OrderAction
    quantity: int
    orderedQuantity: int
    quantityType: QuantityType
    symbolDescription: str
    cancelQuantity: int
    reserveOrder: bool
    reserveQuantity: int


class OrderDetailDict(TypedDict, total=False):
    """Order detail fields."""

    orderTerm: OrderTerm
    priceType: PriceType
    limitPrice: float
    stopPrice: float
    stopLimitPrice: float
    marketSession: MarketSession
    allOrNone: bool
    Instrument: List[InstrumentDict]


class PreviewIdDict(TypedDict):
    """Preview ID for placing orders."""

    previewId: int


class PreviewOrderRequestDict(TypedDict, total=False):
    """Request structure for preview order."""

    orderType: OrderType
    clientOrderId: str
    Order: List[OrderDetailDict]


class PlaceOrderRequestDict(TypedDict, total=False):
    """Request structure for place order."""

    orderType: OrderType
    clientOrderId: str
    Order: List[OrderDetailDict]
    PreviewIds: List[PreviewIdDict]


class AccountDict(TypedDict, total=False):
    """Account information."""

    accountId: str
    accountIdKey: str
    accountMode: str
    accountDesc: str
    accountName: str
    accountType: str
    institutionType: str
    accountStatus: str
    closedDate: int


class BalanceDict(TypedDict, total=False):
    """Account balance information."""

    accountId: str
    accountType: str
    optionLevel: str
    accountDescription: str
    quoteMode: int
    dayTraderStatus: str
    accountMode: str
    cashAvailableForInvestment: float
    cashAvailableForWithdrawal: float
    totalAccountValue: float
    netCash: float
    cashBalance: float
    marginBuyingPower: float
    cashBuyingPower: float
    dtMarginBuyingPower: float
    dtCashBuyingPower: float
    marginBalance: float
    shortAdjustBalance: float
    regtEquity: float
    regtEquityPercent: float
    accountBalance: float


class PositionDict(TypedDict, total=False):
    """Portfolio position."""

    positionId: int
    symbolDescription: str
    dateAcquired: int
    pricePaid: float
    commissions: float
    otherFees: float
    quantity: float
    positionIndicator: str
    positionType: str
    daysGain: float
    daysGainPct: float
    marketValue: float
    totalCost: float
    totalGain: float
    totalGainPct: float
    pctOfPortfolio: float
    Product: ProductDict


class QuoteDataDict(TypedDict, total=False):
    """Quote data for a symbol."""

    symbol: str
    dateTime: str
    quoteStatus: str
    ahFlag: str
    lastTrade: float
    lastTradeTime: int
    change: float
    changePct: float
    previousClose: float
    bid: float
    ask: float
    bidSize: int
    askSize: int
    volume: int
    high: float
    low: float
    high52: float
    low52: float


class OptionChainDict(TypedDict, total=False):
    """Option chain information."""

    timeStamp: int
    quoteType: str
    nearPrice: float
    OptionPair: List[dict]  # Complex nested structure


class TransactionDict(TypedDict, total=False):
    """Transaction information."""

    transactionId: int
    accountId: str
    transactionDate: int
    postDate: int
    amount: float
    description: str
    transactionType: str
    memo: str


class AlertDict(TypedDict, total=False):
    """Alert information."""

    id: int
    createTime: int
    subject: str
    msgText: str
    readTime: int
    deleteTime: int
    status: AlertStatus


class MessageDict(TypedDict, total=False):
    """API message (warning/error)."""

    description: str
    code: int
    type: str


class OrderResponseDict(TypedDict, total=False):
    """Order response structure."""

    orderType: OrderType
    totalOrderValue: float
    previewTime: int
    accountId: str
    optionLevelCd: int
    marginLevelCd: str
    Order: List[dict]
    PreviewIds: List[PreviewIdDict]
    messages: dict
