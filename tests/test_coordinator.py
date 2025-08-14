"""Test coordinator."""

from unittest.mock import AsyncMock, patch

import pytest
from _pytest.logging import LogCaptureFixture
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator
from custom_components.tomtom_travel_time.model import TomTomTravelTimeData

from . import get_mock_config_entry


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


async def test_async_update_data_api_invalid_location(hass: HomeAssistant, caplog: LogCaptureFixture) -> None:
    """Test failure due to invalid location."""
    with patch("custom_components.tomtom_travel_time.coordinator.lat_lon_from_user_input", return_value=None):
        coordinator = TomTomDataUpdateCoordinator(
            hass=hass,
            config_entry=get_mock_config_entry(),
            api_key="dummy_api",
        )

        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001
    assert "Cannot determine location" in caplog.text


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
