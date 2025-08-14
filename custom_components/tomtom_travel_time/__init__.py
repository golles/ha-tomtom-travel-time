"""The TomTom Travel Time component."""

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY, Platform
from homeassistant.core import HomeAssistant

from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry[TomTomDataUpdateCoordinator]) -> bool:
    """Setup a config entry."""
    api_key = config_entry.data[CONF_API_KEY]
    coordinator = TomTomDataUpdateCoordinator(hass, config_entry, api_key)
    config_entry.runtime_data = coordinator

    await coordinator.async_config_entry_first_refresh()
    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry[TomTomDataUpdateCoordinator]) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)
