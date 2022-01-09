import logging
import time
from homeassistant.config_entries import ConfigEntry
from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers import config_entry_flow
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from . import const


_LOGGER = logging.getLogger(__name__)

# TODO: add stop heating
PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
})


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up entities with config from configuration.yml"""
    _LOGGER.debug(f"async_setup_platform {config}")


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    """Set up with config entry forwarded from __init__"""
    _LOGGER.debug("sensor async_setup_entry")
    data = hass.data[const.DOMAIN][entry.entry_id]
    sensor = SGPSensor(data[const.SERIAL_ID])
    data[const.VALUE_UPDATE_CALLBACK] = sensor.on_value_updated
    data[const.ERROR_CALLBACK] = sensor.on_error
    async_add_entities([sensor])


class SGPSensor(SensorEntity):

    _attr_name = "VOC Index"
    _attr_state_class = SensorStateClass.MEASUREMENT

    def __init__(self, serial_id: str):
        self._serial_id = serial_id
        self._value = None

    @property
    def native_value(self):
        return self._value

    @property
    def unique_id(self):
        return f"sgp40_{self._serial_id}_voc"

    def on_value_updated(self, new_value, old_value, temp, rh):
        self._value = new_value
        start = time.time()
        self.schedule_update_ha_state()
        end = time.time()
        _LOGGER.debug(f"schedule_update_ha_state time {end - start}")

    def on_error(self, err):
        _LOGGER.error(f"update error: {err}")
        self._value = None
        self.schedule_update_ha_state()

    @property
    def should_poll(self) -> bool:
        return False

    @property
    def available(self) -> bool:
        return self._value is not None
