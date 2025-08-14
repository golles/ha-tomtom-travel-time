"""Test setup."""

from homeassistant.core import HomeAssistant

from custom_components.tomtom_travel_time import async_unload_entry
from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator

from . import setup_integration


async def test_setup_and_unload_entry(hass: HomeAssistant) -> None:
    """Test entry setup and unload."""
    config_entry = await setup_integration(hass)

    # Check that the client is stored as runtime_data
    assert isinstance(config_entry.runtime_data, TomTomDataUpdateCoordinator)

    # Unload the entry
    assert await async_unload_entry(hass, config_entry)
