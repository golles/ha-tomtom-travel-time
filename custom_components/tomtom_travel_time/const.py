"""Constants."""

from typing import Final

from tomtom_apis.models import TravelModeType
from tomtom_apis.routing.models import AvoidType, RouteType

DOMAIN: Final = "tomtom_travel_time"
ATTRIBUTION = "Powered by TomTom"

CONF_LOCATIONS = "locations"
CONF_VEHICLE_TYPE = "vehicle_type"
CONF_ROUTE_TYPE = "route_type"
CONF_AVOID_TYPE = "avoid_type"

DEFAULT_NAME = "TomTom Travel Time"
DEFAULT_SCAN_INTERVAL = 600
DEFAULT_VEHICLE_TYPE = TravelModeType.CAR.name.lower()
DEFAULT_ROUTE_TYPE = RouteType.FASTEST.name.lower()
DEFAULT_AVOID_TYPE: list[str] = []

VEHICLE_TYPES = [item.name.lower() for item in TravelModeType]
ROUTE_TYPES = [item.name.lower() for item in RouteType]
AVOID_TYPES = [item.name.lower() for item in AvoidType]

DEFAULT_OPTIONS: dict[str, str | bool | list[str]] = {
    CONF_VEHICLE_TYPE: DEFAULT_VEHICLE_TYPE,
    CONF_ROUTE_TYPE: DEFAULT_ROUTE_TYPE,
    CONF_AVOID_TYPE: DEFAULT_AVOID_TYPE,
}
