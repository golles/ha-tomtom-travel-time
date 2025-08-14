"""Tests sensor."""

import pytest
from homeassistant.core import HomeAssistant

from . import setup_integration, unload_integration


@pytest.mark.parametrize(
    ("entity", "value"),
    [
        ("sensor.from_a_to_b_duration", "6"),
        ("sensor.from_a_to_b_duration_in_traffic", "2"),
        ("sensor.from_a_to_b_distance", "1.146"),
    ],
)
@pytest.mark.usefixtures("mocked_data")
async def test_state(hass: HomeAssistant, entity: str, value: str) -> None:
    """Test sensor state."""
    config_entry = await setup_integration(hass)

    state = hass.states.get(entity)
    assert state
    assert state.state == value

    await unload_integration(hass, config_entry)
