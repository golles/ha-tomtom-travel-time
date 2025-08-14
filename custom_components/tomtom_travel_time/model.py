"""TomTom Travel Time models."""

from __future__ import annotations

from dataclasses import dataclass

from tomtom_apis.models import LatLon


@dataclass
class TomTomTravelTimeData:
    """Routing information."""

    duration: float
    distance: float
    delay: float


@dataclass
class UserInputLatLan:
    """Dataclass to handle user input for LatLon."""

    location: LatLon
    geocoded: bool = False
