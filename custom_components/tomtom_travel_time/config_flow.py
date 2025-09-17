"""TomTom Travel Time config flow."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import SOURCE_RECONFIGURE, ConfigEntry, ConfigFlow, ConfigFlowResult, OptionsFlow
from homeassistant.const import CONF_API_KEY, CONF_NAME
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from custom_components.tomtom_travel_time.const import (
    AVOID_TYPES,
    CONF_AVOID_TYPE,
    CONF_LOCATIONS,
    CONF_ROUTE_TYPE,
    CONF_VEHICLE_TYPE,
    DEFAULT_NAME,
    DEFAULT_OPTIONS,
    DOMAIN,
    ROUTE_TYPES,
    VEHICLE_TYPES,
)
from custom_components.tomtom_travel_time.helpers import UserInputLatLan, ValidationError, is_valid_config_entry, lat_lon_from_user_input
from tomtom_apis import TomTomAPIClientError, TomTomAPIConnectionError, TomTomAPIRequestTimeoutError, TomTomAPIServerError
from tomtom_apis.models import LatLon

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_VEHICLE_TYPE): SelectSelector(
            SelectSelectorConfig(
                options=VEHICLE_TYPES,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_VEHICLE_TYPE,
                sort=True,
            ),
        ),
        vol.Required(CONF_ROUTE_TYPE): SelectSelector(
            SelectSelectorConfig(
                options=ROUTE_TYPES,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_ROUTE_TYPE,
                sort=True,
            ),
        ),
        vol.Optional(CONF_AVOID_TYPE): SelectSelector(
            SelectSelectorConfig(
                options=AVOID_TYPES,
                mode=SelectSelectorMode.DROPDOWN,
                translation_key=CONF_AVOID_TYPE,
                sort=True,
                multiple=True,
            ),
        ),
    },
)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME, default=DEFAULT_NAME): TextSelector(),
        vol.Required(CONF_API_KEY): TextSelector(),
        vol.Required(CONF_LOCATIONS): TextSelector(
            TextSelectorConfig(
                type=TextSelectorType.TEXT,
                multiple=True,
            ),
        ),
    },
)


def default_options() -> dict[str, str | bool | list[str]]:
    """Get the default options."""
    return DEFAULT_OPTIONS.copy()


class TomTomOptionsFlow(OptionsFlow):
    """Handle an options flow for TomTom Travel Time."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle the initial step."""
        if user_input is not None:
            return self.async_create_entry(
                title="",
                data=user_input,
            )

        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(OPTIONS_SCHEMA, self.config_entry.options),
        )


class TomTomConfigFlow(ConfigFlow, domain=DOMAIN):  # pylint: disable=abstract-method
    """Handle a config flow for TomTom Travel Time."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(
        _: ConfigEntry,
    ) -> TomTomOptionsFlow:
        """Get the options flow for this handler."""
        return TomTomOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:  # noqa: C901
        """Handle the initial step."""
        errors = {}
        description_placeholders = {}
        user_input = user_input or {}

        if user_input:
            api_key = user_input[CONF_API_KEY]
            locations = user_input[CONF_LOCATIONS]
            lat_lon_locations: list[LatLon] = []

            try:
                if len(locations) < 2:  # noqa: PLR2004
                    raise ValidationError("at_least_two_locations")  # noqa: EM101, TRY301

                for location in locations:
                    index = user_input[CONF_LOCATIONS].index(location)
                    lat_lon = await lat_lon_from_user_input(self.hass, api_key, location)

                    if not isinstance(lat_lon, UserInputLatLan):
                        raise ValidationError("cannot_determine_locations", {"num": str(index + 1)})  # noqa: EM101, TRY301

                    if lat_lon.geocoded:
                        # If the location was geocoded, we store the lat/lon in the config entry to preserve geocode API calls on state updates.
                        user_input[CONF_LOCATIONS][index] = lat_lon.location.to_comma_separated()
                    lat_lon_locations.append(lat_lon.location)

                if await is_valid_config_entry(self.hass, api_key, lat_lon_locations):
                    if self.source == SOURCE_RECONFIGURE:
                        return self.async_update_reload_and_abort(
                            self._get_reconfigure_entry(),
                            title=user_input[CONF_NAME],
                            data=user_input,
                        )
                    return self.async_create_entry(
                        title=user_input.get(CONF_NAME, DEFAULT_NAME),
                        data=user_input,
                        options=default_options(),
                    )
            except ValidationError as ex:
                errors["base"] = ex.error_key
                description_placeholders = ex.description_placeholders or {}
            except TomTomAPIClientError:
                errors["base"] = "client_error"
            except TomTomAPIRequestTimeoutError:
                errors["base"] = "timeout_connect"
            except TomTomAPIServerError:
                errors["base"] = "server_error"
            except TomTomAPIConnectionError:
                errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, user_input),
            errors=errors,
            description_placeholders=description_placeholders,
        )

    async def async_step_reconfigure(self, _: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Handle reconfiguration."""
        data = self._get_reconfigure_entry().data.copy()

        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(CONFIG_SCHEMA, data),
        )
