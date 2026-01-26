"""Async Order Builder for PyETrade.

This module re-exports the OrderBuilder from the main package,
as the builder itself doesn't perform I/O - only the final
submission through ETradeOrder does.
"""

from pyetrade.order_builder import OrderBuilder, OrderBuilderError

# Re-export for convenience - the builder itself is synchronous
# Only the API calls need to be async
__all__ = ["OrderBuilder", "OrderBuilderError"]
