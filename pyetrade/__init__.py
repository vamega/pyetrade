"""Init for pyetrade module"""
__version__ = "2.2.0"

from . import authorization  # noqa: F401
from .authorization import ETradeOAuth, ETradeAccessManager  # noqa: F401
from . import accounts  # noqa: F401
from .accounts import ETradeAccounts  # noqa: F401
from . import market  # noqa: F401
from .market import ETradeMarket  # noqa: F401
from . import order  # noqa: F401
from .order import ETradeOrder  # noqa: F401
from . import alerts  # noqa: F401
from .alerts import ETradeAlerts  # noqa: F401

# New modules for enhanced functionality
from . import types  # noqa: F401
from .order_builder import OrderBuilder, OrderBuilderError  # noqa: F401
