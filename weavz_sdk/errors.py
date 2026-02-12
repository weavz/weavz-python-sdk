"""Weavz API error classes."""

from __future__ import annotations
from typing import Any


class WeavzError(Exception):
    """Error returned by the Weavz API."""

    def __init__(
        self,
        message: str,
        *,
        code: str = "UNKNOWN",
        status: int = 0,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status = status
        self.details = details

    def __repr__(self) -> str:
        return f"WeavzError(code={self.code!r}, status={self.status}, message={str(self)!r})"
