"""Test config flow."""

from collections.abc import Generator
from unittest.mock import patch

import pytest
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from custom_components.tomtom_travel_time.const import CONF_AVOID_TYPE, CONF_LOCATIONS, CONF_ROUTE_TYPE, CONF_VEHICLE_TYPE, DOMAIN
from custom_components.tomtom_travel_time.model import UserInputLatLan
from tomtom_apis import TomTomAPIClientError, TomTomAPIConnectionError, TomTomAPIRequestTimeoutError, TomTomAPIServerError
from tomtom_apis.models import LatLon, TravelModeType
from tomtom_apis.routing.models import AvoidType, RouteType

from . import get_mock_config_data, setup_integration, unload_integration

MOCK_UPDATE_CONFIG = {
    CONF_VEHICLE_TYPE: TravelModeType.BICYCLE.name.lower(),
    CONF_ROUTE_TYPE: RouteType.ECO.name.lower(),
    CONF_AVOID_TYPE: [AvoidType.TOLL_ROADS.name.lower()],
}


@pytest.fixture(autouse=True, name="bypass_setup")
def fixture_bypass_setup_fixture() -> Generator[None]:
    """Prevent actual setup of the integration during tests."""
    with patch("custom_components.tomtom_travel_time.async_setup_entry", return_value=True):
        yield


@pytest.fixture(autouse=False, name="bypass_validation")
def fixture_bypass_validation() -> Generator[None]:
    """Prevent actual setup of the integration during tests."""
    with patch("custom_components.tomtom_travel_time.helpers.is_valid_config_entry", return_value=True):
        yield


@pytest.mark.usefixtures("bypass_validation")
async def test_successful_config_flow(hass: HomeAssistant) -> None:
    """Test a successful config flow."""
    config_data = get_mock_config_data()
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # If a user were to fill in all fields, it would result in this function call
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=config_data)

    # Check that the config flow is complete and a new entry is created with
    # the input data
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == config_data[CONF_NAME]
    assert result2["data"] == config_data
    assert result2["result"]


@pytest.mark.usefixtures("bypass_validation")
async def test_successful_config_flow_geocoded(hass: HomeAssistant) -> None:
    """Test a successful config flow, location was geocoded."""
    with patch(
        "custom_components.tomtom_travel_time.config_flow.lat_lon_from_user_input",
        return_value=UserInputLatLan(location=LatLon(lat=52.377956, lon=4.897071), geocoded=True),
    ):
        config_data = get_mock_config_data()
        config_data[CONF_LOCATIONS] = [
            "52.377956,4.897071",
            "52.377956,4.897071",
        ]
        # Initialize a config flow
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        # Check that the config flow shows the user form as the first step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # If a user were to fill in all fields, it would result in this function call
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=config_data)

        # Check that the config flow is complete and a new entry is created with
        # the input data
        assert result2["type"] == FlowResultType.CREATE_ENTRY
        assert result2["title"] == config_data[CONF_NAME]
        assert result2["data"] == config_data
        assert result2["result"]


async def test_unsuccessful_config_flow_locations_length(hass: HomeAssistant) -> None:
    """Test an unsuccessful config flow due to locations length."""
    config_data = get_mock_config_data()
    config_data[CONF_LOCATIONS] = ["52.377956, 4.897070"]
    # Initialize a config flow
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

    # Check that the config flow shows the user form as the first step
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    # If a user were to fill in all fields, it would result in this function call
    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=config_data)

    # Check that the config flow returns the error
    assert result2["type"] == FlowResultType.FORM
    assert result2["errors"] == {"base": "at_least_two_locations"}


async def test_unsuccessful_config_flow_cannot_determine_location(hass: HomeAssistant) -> None:
    """Test an unsuccessful config flow due to not determining a location."""
    with patch("custom_components.tomtom_travel_time.config_flow.lat_lon_from_user_input", return_value=None):
        config_data = get_mock_config_data()
        # Initialize a config flow
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        # Check that the config flow shows the user form as the first step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # If a user were to fill in all fields, it would result in this function call
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=config_data)

        # Check that the config flow returns the error
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": "cannot_determine_locations"}


@pytest.mark.parametrize(
    ("side_effect", "error"),
    [
        (TomTomAPIClientError, "client_error"),
        (TomTomAPIRequestTimeoutError, "timeout_connect"),
        (TomTomAPIServerError, "server_error"),
        (TomTomAPIConnectionError, "cannot_connect"),
    ],
)
async def test_unsuccessful_config_flow_api_errors(side_effect: Exception, error: str, hass: HomeAssistant) -> None:
    """Test an unsuccessful config flow due to API errors."""
    config_data = get_mock_config_data()
    with patch("custom_components.tomtom_travel_time.config_flow.is_valid_config_entry") as mock_validation:
        mock_validation.side_effect = side_effect

        # Initialize a config flow
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})

        # Check that the config flow shows the user form as the first step
        assert result["type"] == FlowResultType.FORM
        assert result["step_id"] == "user"

        # If a user were to fill in an incomplete form, it would result in this function call
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input=config_data)

        # Check that the config flow returns the error
        assert result2["type"] == FlowResultType.FORM
        assert result2["errors"] == {"base": error}


@pytest.mark.usefixtures("bypass_validation")
async def test_step_reconfigure(hass: HomeAssistant) -> None:
    """Test for reconfigure step."""
    updated_data = {
        CONF_API_KEY: "1234567890",
        CONF_LOCATIONS: [
            "52.477956, 4.797070",
            "51.826517, 4.562456",
        ],
        CONF_NAME: "From B to C",
    }
    config_entry = await setup_integration(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=updated_data,
    )
    assert result2["type"] == FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"

    assert config_entry.title == updated_data[CONF_NAME]
    assert config_entry.data == {**updated_data}


async def test_options_flow(hass: HomeAssistant) -> None:
    """Test an options flow."""
    # Create a new MockConfigEntry and add to HASS (we're bypassing config
    # flow entirely)
    config_entry = await setup_integration(hass)

    # Initialize an options flow
    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    # Verify that the first options step is a user form
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"

    # Enter some fake data into the form
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input=MOCK_UPDATE_CONFIG,
    )

    # Verify that the flow finishes
    assert result2["type"] == FlowResultType.CREATE_ENTRY

    # Verify that the options were updated
    assert config_entry.options == MOCK_UPDATE_CONFIG

    await unload_integration(hass, config_entry)
