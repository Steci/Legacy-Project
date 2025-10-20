"""Compatibility shim exposing domain event types via legacy absolute imports."""

from models.event import Event, Place, Witness, WitnessType

__all__ = ["Event", "Place", "Witness", "WitnessType"]



