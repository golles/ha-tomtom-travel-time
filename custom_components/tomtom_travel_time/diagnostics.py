"""TomTom Travel Time diagnostics."""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant

from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator

TO_REDACT = {CONF_API_KEY}


async def async_get_config_entry_diagnostics(_hass: HomeAssistant, config_entry: ConfigEntry[TomTomDataUpdateCoordinator]) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = config_entry.runtime_data

    data: dict[str, Any] = {
        "config_entry": config_entry.as_dict(),
        "data": asdict(coordinator.data) if coordinator.data else {},
    }

    return async_redact_data(data, TO_REDACT)
