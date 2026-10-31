"""Test coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock

import pytest
from aiohttp import ClientResponseError, RequestInfo
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import UpdateFailed
from multidict import CIMultiDict, CIMultiDictProxy
from pytest_homeassistant_custom_component.common import MockConfigEntry
from yarl import URL

from custom_components.tomtom_travel_time.const import CONF_LOCATIONS, CONF_UPDATE_INTERVAL, DEFAULT_OPTIONS, DEFAULT_UPDATE_INTERVAL, DOMAIN
from custom_components.tomtom_travel_time.coordinator import TomTomDataUpdateCoordinator
from custom_components.tomtom_travel_time.model import TomTomTravelTimeData
from tomtom_apis.exceptions import TomTomAPIClientError, TomTomAPIConnectionError, TomTomAPIRequestTimeoutError

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
    with pytest.raises(UpdateFailed, match="Exception: API error"):
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001


async def test_async_update_data_api_failure_http_status(hass: HomeAssistant, mock_routing_api: AsyncMock) -> None:
    """Test API failure message includes the HTTP status but not the API key from the request URL."""
    request_info = RequestInfo(
        url=URL("https://api.tomtom.com/routing/1/calculateRoute/1,2:3,4/json?key=dummy_api"),
        method="GET",
        headers=CIMultiDictProxy(CIMultiDict()),
    )
    error = TomTomAPIClientError("Client error")
    error.__cause__ = ClientResponseError(request_info, (), status=403, message="Forbidden")
    mock_routing_api.get_calculate_route.side_effect = error
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=get_mock_config_entry(),
        api_key="dummy_api",
    )
    with pytest.raises(UpdateFailed, match=r"^TomTom API returned HTTP 403 Forbidden\. Check in the TomTom Developer Portal"):
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001


async def test_async_update_data_api_failure_redacts_api_key(hass: HomeAssistant, mock_routing_api: AsyncMock) -> None:
    """Test API failure message never contains the API key."""
    error = TomTomAPIConnectionError("Connection error")
    error.__cause__ = ValueError("https://api.tomtom.com/?key=dummy_api")
    mock_routing_api.get_calculate_route.side_effect = error
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=get_mock_config_entry(),
        api_key="dummy_api",
    )
    with pytest.raises(UpdateFailed) as exc_info:
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001
    assert "dummy_api" not in str(exc_info.value)
    assert str(exc_info.value) == "TomTomAPIConnectionError: Connection error (ValueError: https://api.tomtom.com/?key=**REDACTED**)"


async def test_async_update_data_api_failure_timeout(hass: HomeAssistant, mock_routing_api: AsyncMock) -> None:
    """Test API failure message omits an empty cause."""
    error = TomTomAPIRequestTimeoutError("Timeout occurred while connecting to the API")
    error.__cause__ = TimeoutError()
    mock_routing_api.get_calculate_route.side_effect = error
    coordinator = TomTomDataUpdateCoordinator(
        hass=hass,
        config_entry=get_mock_config_entry(),
        api_key="dummy_api",
    )
    with pytest.raises(UpdateFailed, match=r"^TomTomAPIRequestTimeoutError: Timeout occurred while connecting to the API$"):
        await coordinator._async_update_data()  # pylint: disable=protected-access # noqa: SLF001


async def test_update_interval(hass: HomeAssistant) -> None:
    """Test the update interval comes from the options."""
    config_entry = MockConfigEntry(domain=DOMAIN, data=get_mock_config_data(), options={**DEFAULT_OPTIONS, CONF_UPDATE_INTERVAL: 15})
    coordinator = TomTomDataUpdateCoordinator(hass=hass, config_entry=config_entry, api_key="dummy_api")
    assert coordinator.update_interval == timedelta(minutes=15)


async def test_update_interval_default(hass: HomeAssistant) -> None:
    """Test the default update interval for entries created before the option existed."""
    options = {key: value for key, value in DEFAULT_OPTIONS.items() if key != CONF_UPDATE_INTERVAL}
    config_entry = MockConfigEntry(domain=DOMAIN, data=get_mock_config_data(), options=options)
    coordinator = TomTomDataUpdateCoordinator(hass=hass, config_entry=config_entry, api_key="dummy_api")
    assert coordinator.update_interval == timedelta(minutes=DEFAULT_UPDATE_INTERVAL)
