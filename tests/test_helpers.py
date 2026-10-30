"""Test helpers."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from homeassistant.const import STATE_HOME, STATE_NOT_HOME, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.location import find_coordinates

from custom_components.tomtom_travel_time.helpers import UserInputLatLan, ValidationError, is_valid_config_entry, lat_lon_from_user_input
from tomtom_apis.models import LatLon


@pytest.fixture(autouse=True, name="mock_find_coordinates")
def fixture_mock_find_coordinates() -> Generator[MagicMock]:
    """Prevent actual setup of the integration during tests."""
    with patch("custom_components.tomtom_travel_time.helpers.find_coordinates", return_value=None) as mock:
        yield mock


async def test_lat_lon_from_user_input_float() -> None:
    """Test lat_lon_from_user_input with float input."""
    hass = MagicMock()
    api_key = "dummy"
    # Direct float input
    result = await lat_lon_from_user_input(hass, api_key, "52.1,4.2")
    assert isinstance(result, UserInputLatLan)
    assert result.location.lat == 52.1
    assert result.location.lon == 4.2
    assert not result.geocoded


async def test_lat_lon_from_user_input_find_coordinates(mock_find_coordinates: MagicMock) -> None:
    """Test lat_lon_from_user_input with find_coordinates."""
    hass = MagicMock()
    api_key = "dummy"
    mock_find_coordinates.return_value = "51.2,5.3"
    result = await lat_lon_from_user_input(hass, api_key, "Some Place")
    assert isinstance(result, UserInputLatLan)
    assert result.location.lat == 51.2
    assert result.location.lon == 5.3
    assert not result.geocoded


@patch("custom_components.tomtom_travel_time.helpers.GeocodingApi")
async def test_lat_lon_from_user_input_geocode(mock_geocoding_api: AsyncMock) -> None:
    """Test lat_lon_from_user_input with geocoding."""
    hass = MagicMock()
    api_key = "dummy"
    mock_api_instance = AsyncMock()
    mock_api_instance.__aenter__.return_value = mock_api_instance
    mock_api_instance.get_geocode.return_value.results = [MagicMock(position=LatLon(lat=40.0, lon=-3.0))]
    mock_geocoding_api.return_value = mock_api_instance
    result = await lat_lon_from_user_input(hass, api_key, "Madrid")
    assert isinstance(result, UserInputLatLan)
    assert result.location.lat == 40.0
    assert result.location.lon == -3.0
    assert result.geocoded


async def test_lat_lon_from_user_input_none(mock_geocoding_api: AsyncMock) -> None:
    """Test lat_lon_from_user_input returns None if all location resolution fails."""
    hass = MagicMock()
    api_key = "dummy"
    mock_api_instance = AsyncMock()
    mock_api_instance.__aenter__.return_value = mock_api_instance
    mock_api_instance.get_geocode.return_value.results = []
    mock_geocoding_api.return_value = mock_api_instance
    result = await lat_lon_from_user_input(hass, api_key, "Unknown Place")
    assert result is None


@pytest.fixture(name="real_find_coordinates")
def fixture_real_find_coordinates(mock_find_coordinates: MagicMock) -> MagicMock:
    """Use Home Assistant's real find_coordinates, while still being able to assert calls."""
    mock_find_coordinates.side_effect = find_coordinates
    return mock_find_coordinates


@pytest.fixture(name="geocoding_result")
def fixture_geocoding_result(mock_geocoding_api: AsyncMock) -> AsyncMock:
    """Configure the geocoding API mock to return a single result."""
    mock_geocoding_api.__aenter__.return_value = mock_geocoding_api
    mock_geocoding_api.get_geocode.return_value.results = [MagicMock(position=LatLon(lat=52.373, lon=4.893))]
    return mock_geocoding_api


@pytest.mark.usefixtures("real_find_coordinates")
async def test_lat_lon_from_user_input_entity_with_location(hass: HomeAssistant, mock_geocoding_api: AsyncMock) -> None:
    """Test an entity with latitude and longitude attributes resolves without geocoding."""
    hass.states.async_set("device_tracker.phone", STATE_NOT_HOME, {"latitude": 51.5, "longitude": 4.5})
    result = await lat_lon_from_user_input(hass, "dummy", "device_tracker.phone")
    assert result == UserInputLatLan(location=LatLon(lat=51.5, lon=4.5))
    mock_geocoding_api.get_geocode.assert_not_called()


@pytest.mark.usefixtures("real_find_coordinates")
@pytest.mark.parametrize("state", ["person.does_not_exist", "device_tracker.does_not_exist"])
async def test_lat_lon_from_user_input_entity_does_not_exist(hass: HomeAssistant, mock_geocoding_api: AsyncMock, state: str) -> None:
    """Test a non-existing entity, or an entity referring to a non-existing entity, is not geocoded."""
    hass.states.async_set("sensor.location", state)
    assert await lat_lon_from_user_input(hass, "dummy", "person.does_not_exist") is None
    assert await lat_lon_from_user_input(hass, "dummy", "sensor.location") is None
    mock_geocoding_api.get_geocode.assert_not_called()


@pytest.mark.usefixtures("real_find_coordinates")
async def test_lat_lon_from_user_input_entity_circular_reference(hass: HomeAssistant, mock_geocoding_api: AsyncMock) -> None:
    """Test entities referring to each other are not geocoded."""
    hass.states.async_set("sensor.a", "sensor.b")
    hass.states.async_set("sensor.b", "sensor.a")
    assert await lat_lon_from_user_input(hass, "dummy", "sensor.a") is None
    mock_geocoding_api.get_geocode.assert_not_called()


@pytest.mark.usefixtures("real_find_coordinates")
@pytest.mark.parametrize("state", [STATE_NOT_HOME, STATE_UNKNOWN, STATE_UNAVAILABLE, STATE_HOME])
async def test_lat_lon_from_user_input_entity_without_location(hass: HomeAssistant, mock_geocoding_api: AsyncMock, state: str) -> None:
    """Test an entity without location (and no matching zone) is not geocoded."""
    hass.states.async_set("person.someone", state)
    assert await lat_lon_from_user_input(hass, "dummy", "person.someone") is None
    mock_geocoding_api.get_geocode.assert_not_called()


@pytest.mark.usefixtures("real_find_coordinates")
@pytest.mark.parametrize("state", [STATE_HOME, "work", "Office"])
async def test_lat_lon_from_user_input_entity_in_zone(hass: HomeAssistant, mock_geocoding_api: AsyncMock, state: str) -> None:
    """Test an entity in a zone resolves to the coordinates of that zone."""
    hass.states.async_set("zone.home", "0", {"latitude": 52.1, "longitude": 4.2})
    hass.states.async_set("zone.work", "0", {"latitude": 51.9, "longitude": 4.4, "friendly_name": "Office"})
    hass.states.async_set("person.someone", state)
    expected = LatLon(lat=52.1, lon=4.2) if state == STATE_HOME else LatLon(lat=51.9, lon=4.4)
    result = await lat_lon_from_user_input(hass, "dummy", "person.someone")
    assert result == UserInputLatLan(location=expected)
    mock_geocoding_api.get_geocode.assert_not_called()


@pytest.mark.usefixtures("real_find_coordinates")
async def test_lat_lon_from_user_input_entity_address_state(hass: HomeAssistant, geocoding_result: AsyncMock) -> None:
    """Test the address in the state of a sensor is geocoded, not the entity ID."""
    hass.states.async_set("sensor.address", "Dam 1, Amsterdam")
    result = await lat_lon_from_user_input(hass, "dummy", "sensor.address")
    assert result == UserInputLatLan(location=LatLon(lat=52.373, lon=4.893), geocoded=True)
    geocoding_result.get_geocode.assert_awaited_once_with(query="Dam 1, Amsterdam")


@pytest.mark.usefixtures("real_find_coordinates")
async def test_lat_lon_from_user_input_address(hass: HomeAssistant, geocoding_result: AsyncMock) -> None:
    """Test a plain address (not an entity ID) is still geocoded."""
    result = await lat_lon_from_user_input(hass, "dummy", "Dam 1, Amsterdam")
    assert result == UserInputLatLan(location=LatLon(lat=52.373, lon=4.893), geocoded=True)
    geocoding_result.get_geocode.assert_awaited_once_with(query="Dam 1, Amsterdam")


@patch("custom_components.tomtom_travel_time.helpers.RoutingApi")
async def test_is_valid_config_entry_success(mock_routing_api: AsyncMock) -> None:
    """Test is_valid_config_entry with valid locations."""
    hass = MagicMock()
    api_key = "dummy"
    locations = [LatLon(lat=1.0, lon=2.0), LatLon(lat=3.0, lon=4.0)]
    mock_api_instance = AsyncMock()
    mock_api_instance.__aenter__.return_value = mock_api_instance
    mock_api_instance.get_calculate_route.return_value.routes = [MagicMock()]
    mock_routing_api.return_value = mock_api_instance
    result = await is_valid_config_entry(hass, api_key, locations)
    assert result is True


async def test_is_valid_config_entry_failure(mock_routing_api: AsyncMock) -> None:
    """Test is_valid_config_entry with invalid locations."""
    hass = MagicMock()
    api_key = "dummy"
    locations = [LatLon(lat=1.0, lon=2.0), LatLon(lat=3.0, lon=4.0)]
    mock_api_instance = AsyncMock()
    mock_api_instance.__aenter__.return_value = mock_api_instance
    mock_api_instance.get_calculate_route.return_value.routes = []
    mock_routing_api.return_value = mock_api_instance
    with pytest.raises(ValidationError) as exc:
        await is_valid_config_entry(hass, api_key, locations)
    assert exc.value.error_key == "cannot_plan_route"


def test_validation_error() -> None:
    """Test ValidationError initialization and string representation."""
    err = ValidationError("key", {"foo": "bar"})
    assert err.error_key == "key"
    assert err.description_placeholders == {"foo": "bar"}
    assert str(err) == "Validation error occurred."
