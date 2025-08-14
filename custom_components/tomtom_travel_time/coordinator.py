"""TomTom Travel Time coordinator."""

from __future__ import annotations

import logging
import math
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from custom_components.tomtom_travel_time.const import (
    CONF_AVOID_TYPE,
    CONF_LOCATIONS,
    CONF_ROUTE_TYPE,
    CONF_VEHICLE_TYPE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.tomtom_travel_time.helpers import lat_lon_from_user_input
from custom_components.tomtom_travel_time.model import TomTomTravelTimeData, UserInputLatLan
from tomtom_apis import ApiOptions
from tomtom_apis.models import LatLon, LatLonList, TravelModeType
from tomtom_apis.routing import RoutingApi
from tomtom_apis.routing.models import AvoidType, CalculateRouteParams, RouteType

_LOGGER = logging.getLogger(__name__)


class TomTomDataUpdateCoordinator(DataUpdateCoordinator[TomTomTravelTimeData]):
    """DataUpdateCoordinator."""

    config_entry: ConfigEntry[DataUpdateCoordinator]

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        api_key: str,
    ) -> None:
        """Initialize."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=config_entry,
            name=DOMAIN,
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._api_key = api_key
        self._api = RoutingApi(ApiOptions(api_key=api_key))

    async def _async_update_data(self) -> TomTomTravelTimeData:
        """Get the latest data from the Routing API."""
        _LOGGER.debug("Fetching Route")

        locations: list[LatLon] = []
        for location in self.config_entry.data[CONF_LOCATIONS]:
            lat_lon = await lat_lon_from_user_input(self.hass, self._api_key, location)
            if not isinstance(lat_lon, UserInputLatLan):
                _LOGGER.error("Cannot determine location: %s", location)
            else:
                locations.append(lat_lon.location)

        travel_mode = TravelModeType[self.config_entry.options[CONF_VEHICLE_TYPE].upper()]
        route_type = RouteType[self.config_entry.options[CONF_ROUTE_TYPE].upper()]
        avoids: list[AvoidType] = [AvoidType[avoid.upper()] for avoid in self.config_entry.options[CONF_AVOID_TYPE]]

        _LOGGER.debug("Planning route with locations: %s travel_mode: %s, route_type: %s, avoids: %s", locations, travel_mode, route_type, avoids)

        try:
            response = await self._api.get_calculate_route(
                locations=LatLonList(locations=locations),
                params=CalculateRouteParams(
                    maxAlternatives=0,
                    routeType=route_type,
                    travelMode=travel_mode,
                    avoid=avoids,
                ),
            )

            return TomTomTravelTimeData(
                duration=math.ceil(response.routes[0].summary.travelTimeInSeconds / 60),
                distance=response.routes[0].summary.lengthInMeters / 1000,
                delay=math.ceil(response.routes[0].summary.trafficDelayInSeconds / 60),
            )
        except Exception as exception:
            raise UpdateFailed from exception
