"""TomTom Travel Time helpers."""

import logging
import re

from homeassistant.const import STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant, valid_entity_id
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.location import find_coordinates

from custom_components.tomtom_travel_time.model import UserInputLatLan
from tomtom_apis import ApiOptions
from tomtom_apis.models import LatLon, LatLonList
from tomtom_apis.places import GeocodingApi
from tomtom_apis.routing import RoutingApi
from tomtom_apis.routing.models import CalculateRouteParams

_LOGGER = logging.getLogger(__name__)

# States that find_coordinates can return for an entity without a location, these should never be geocoded.
UNRESOLVABLE_STATES = {STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN}


async def lat_lon_from_user_input(hass: HomeAssistant, api_key: str, user_input: str) -> UserInputLatLan | None:
    """Attempt to make a LatLon object from user input."""
    # Step 1: Check if user_input is already 'float,float' or 'float, float'.
    match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", user_input)
    if match:
        lat, lon = map(float, match.groups())
        return UserInputLatLan(location=LatLon(lat=lat, lon=lon))

    # Step 2: Try Home Assistant's find_coordinates.
    coords_str = find_coordinates(hass, user_input)
    if coords_str:
        match = re.match(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$", coords_str)
        if match:
            lat, lon = map(float, match.groups())
            return UserInputLatLan(location=LatLon(lat=lat, lon=lon))

    # Never geocode an entity ID, only what find_coordinates resolved it to, e.g. an address in the state of a sensor.
    query = user_input
    if valid_entity_id(user_input):
        if not coords_str or valid_entity_id(coords_str):
            _LOGGER.debug("Cannot determine location of %s, the entity (or the entity its state refers to) does not exist (yet)", user_input)
            return None
        if coords_str in UNRESOLVABLE_STATES:
            _LOGGER.debug("Cannot determine location of %s, the entity has no location and its state is '%s'", user_input, coords_str)
            return None
        query = coords_str

    # Step 3: Fallback to geocoding API to determine the location.
    async with GeocodingApi(ApiOptions(api_key=api_key), async_get_clientsession(hass)) as geo_coding_api:
        response = await geo_coding_api.get_geocode(query=query)

        if len(response.results) > 0:
            _LOGGER.info("Geocoding location response: %s", response.results[0].position)
            return UserInputLatLan(response.results[0].position, geocoded=True)

    return None


async def is_valid_config_entry(hass: HomeAssistant, api_key: str, locations: list[LatLon]) -> bool:
    """Return whether the config entry data is valid."""
    async with RoutingApi(ApiOptions(api_key=api_key), async_get_clientsession(hass)) as routing_api:
        response = await routing_api.get_calculate_route(
            locations=LatLonList(locations=locations),
            params=CalculateRouteParams(
                maxAlternatives=0,
            ),
        )

    if len(response.routes) > 0:
        return True

    _LOGGER.error("No routes found for the provided origin and destination.")
    raise ValidationError("cannot_plan_route")  # noqa: EM101


class ValidationError(Exception):
    """Exception raised when user input validation fails."""

    def __init__(self, error_key: str, description_placeholders: dict[str, str] | None = None) -> None:
        """Initialize the ValidationError."""
        self.error_key = error_key
        self.description_placeholders = description_placeholders
        super().__init__("Validation error occurred.")
