"""Compatibility shim exposing domain date types via legacy absolute imports."""

from models.date import Calendar, Date, DMY, Precision

__all__ = ["Calendar", "Date", "DMY", "Precision"]



