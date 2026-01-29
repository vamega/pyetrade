from __future__ import annotations

from typing import Any, Dict, Optional


def clean_params(params: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """Drop None-valued params to mirror requests behavior with HTTPX."""
    if not params:
        return None
    cleaned = {k: v for k, v in params.items() if v is not None}
    return cleaned or None
