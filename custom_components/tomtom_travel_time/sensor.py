"""TomTom Travel Time sensor."""

from __future__ import annotations

from datetime import timedelta

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorEntityDescription, SensorStateClass, StateType
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, UnitOfLength, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ATTRIBUTION, DEFAULT_NAME, DEFAULT_SCAN_INTERVAL, DOMAIN
from .coordinator import TomTomDataUpdateCoordinator

SCAN_INTERVAL = timedelta(seconds=DEFAULT_SCAN_INTERVAL)


SENSOR_DESCRIPTIONS: list[SensorEntityDescription] = [
    SensorEntityDescription(
        translation_key="duration",
        icon="mdi:car-clock",
        key="duration",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        translation_key="delay",
        icon="mdi:car-multiple",
        key="delay",
        state_class=SensorStateClass.MEASUREMENT,
        native_unit_of_measurement=UnitOfTime.MINUTES,
    ),
    SensorEntityDescription(
        translation_key="distance",
        icon="mdi:map-marker-distance",
        key="distance",
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.KILOMETERS,
    ),
]


async def async_setup_entry(
    _: HomeAssistant,
    config_entry: ConfigEntry[TomTomDataUpdateCoordinator],
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up a TomTom travel time sensor entry."""
    name = config_entry.data.get(CONF_NAME, DEFAULT_NAME)
    coordinator = config_entry.runtime_data

    sensors: list[TomTomSensor] = [
        TomTomSensor(
            config_entry,
            name,
            sensor_description,
            coordinator,
        )
        for sensor_description in SENSOR_DESCRIPTIONS
    ]

    async_add_entities(sensors)


class TomTomSensor(CoordinatorEntity[TomTomDataUpdateCoordinator], SensorEntity):
    """Representation of a TomTom travel time sensor."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(
        self,
        config_entry: ConfigEntry,
        name: str,
        sensor_description: SensorEntityDescription,
        coordinator: TomTomDataUpdateCoordinator,
    ) -> None:
        """Initialize the TomTom travel time sensor."""
        super().__init__(coordinator)
        self.entity_description = sensor_description
        self._attr_unique_id = f"{config_entry.entry_id}_{sensor_description.key}"
        self._config_entry = config_entry
        self._attr_device_info = DeviceInfo(
            entry_type=DeviceEntryType.SERVICE,
            identifiers={(DOMAIN, config_entry.entry_id)},
            name=name,
            configuration_url="https://developer.tomtom.com/user/login",
            manufacturer="TomTom",
        )

    @property
    def native_value(self) -> StateType:
        """Return the value reported by the sensor."""
        return getattr(self.coordinator.data, self.entity_description.key, None)
