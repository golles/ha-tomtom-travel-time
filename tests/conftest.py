"""Global fixtures."""

from collections.abc import Generator
from unittest.mock import AsyncMock, Mock, PropertyMock, patch

import pytest
from pytest_homeassistant_custom_component.common import load_fixture

from tomtom_apis.places import GeocodingApi
from tomtom_apis.routing import RoutingApi
from tomtom_apis.routing.models import CalculatedRouteResponse


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations: Generator) -> Generator[None]:
    """Enable custom integrations."""
    return enable_custom_integrations


@pytest.fixture(name="enable_all_entities", autouse=True)
def fixture_enable_all_entities() -> Generator[None]:
    """Make sure all entities are enabled."""
    with patch(
        "homeassistant.helpers.entity.Entity.entity_registry_enabled_default",
        PropertyMock(return_value=True),
    ):
        yield


@pytest.fixture(autouse=True, name="mock_geocoding_api")
def fixture_mock_geocoding_api() -> Generator[AsyncMock]:
    """Auto-patch GeocodingApi in all tests and return the mock for configuration."""
    mock_client = AsyncMock(spec=GeocodingApi)
    mock_client_class = Mock(return_value=mock_client)

    with (
        patch("custom_components.tomtom_travel_time.helpers.GeocodingApi", mock_client_class),
    ):
        yield mock_client


@pytest.fixture(autouse=True, name="mock_routing_api")
def fixture_mock_routing_api() -> Generator[AsyncMock]:
    """Auto-patch RoutingApi in all tests and return the mock for configuration."""
    mock_client = AsyncMock(spec=RoutingApi)
    mock_client_class = Mock(return_value=mock_client)

    with (
        patch("custom_components.tomtom_travel_time.coordinator.RoutingApi", mock_client_class),
        patch("custom_components.tomtom_travel_time.helpers.RoutingApi", mock_client_class),
    ):
        yield mock_client


@pytest.fixture(name="mocked_data")
def fixture_mocked_data(request: pytest.FixtureRequest, mock_routing_api: AsyncMock) -> None:
    """Fixture for mocking a response with a configurable JSON file."""
    json_file = getattr(request, "param", "response.json")
    response_json = load_fixture(json_file)
    mock_response = CalculatedRouteResponse.from_json(response_json)
    mock_routing_api.get_calculate_route.return_value = mock_response
