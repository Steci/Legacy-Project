"""Compatibility package for parsers module.

This module exposes the legacy GW parser entry points so older code paths
can keep importing from ``parsers`` without adjusting their import
statements.
"""

from .parser import GWParser

__all__ = ["GWParser"]
