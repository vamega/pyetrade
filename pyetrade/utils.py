from __future__ import annotations

import re
from typing import Any, Dict, Optional

_CLIENT_ORDER_ID_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def clean_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Drop None-valued params to mirror requests behavior with HTTPX."""
    if not params:
        return None
    cleaned = {k: v for k, v in params.items() if v is not None}
    return cleaned or None


def validate_client_order_id(value: str) -> None:
    """Validate clientOrderId format (ASCII alnum/underscore/hyphen) and length."""
    if len(value) >= 20:
        raise ValueError("clientOrderId must be fewer than 20 characters.")
    if not _CLIENT_ORDER_ID_RE.match(value):
        raise ValueError("clientOrderId must match ^[A-Za-z0-9_-]+$.")
