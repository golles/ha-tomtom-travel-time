"""Test coordinator."""

from unittest.mock import AsyncMock

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tomtom_travel_time.const import CONF_LOCATIONS, DEFAULT_OPTIONS, DOMAIN
from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator
from custom_components.tomtom_travel_time.model import TomTomTravelTimeData

from . import get_mock_config_data, get_mock_config_entry


async def test_async_update_data_success(hass: HomeAssistant, mock_routing_api: AsyncMock) -> None:
    """Test successful data update."""
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=get_mock_config_entry(),
        api_key="dummy_api",
    )
    result = await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001
    assert isinstance(result, TomTomTravelTimeData)
    mock_routing_api.get_calculate_route.assert_awaited_once()


async def test_async_update_data_api_invalid_location(hass: HomeAssistant, mock_routing_api: AsyncMock, mock_geocoding_api: AsyncMock) -> None:
    """Test failure due to a location that cannot be determined, no route should be planned."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={**get_mock_config_data(), CONF_LOCATIONS: ["52.377956, 4.897071", "person.does_not_exist"]},
        options=DEFAULT_OPTIONS,
    )
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=config_entry,
        api_key="dummy_api",
    )

    with pytest.raises(UpdateFailed, match=r"^Cannot determine location 2: person\.does_not_exist$"):
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001
    mock_geocoding_api.get_geocode.assert_not_called()
    mock_routing_api.get_calculate_route.assert_not_called()


async def test_async_update_data_api_failure(hass: HomeAssistant, mock_routing_api: AsyncMock) -> None:
    """Test API failure."""
    mock_routing_api.get_calculate_route.side_effect = Exception("API error")
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=get_mock_config_entry(),
        api_key="dummy_api",
    )
    with pytest.raises(UpdateFailed):
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001
