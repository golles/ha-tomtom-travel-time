"""Test helpers."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
