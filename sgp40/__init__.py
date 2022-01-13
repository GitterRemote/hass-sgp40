"""The Sensirion SGP40 integration."""
from __future__ import annotations
import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from sgp40 import service

from . import const

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sensirion SGP40 from a config entry."""
    _LOGGER.debug("async_setup_entry")
    domain_data = hass.data.setdefault(const.DOMAIN, {})

    # TODO: move init into config flow and store serial_id in entry, and set
    # the unique id of the flow
    # TODO: fix reload cause init -21 error
    serial_id = service.init()

    domain_data[entry.entry_id] = {
        const.SERIAL_ID: serial_id,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    data = domain_data[entry.entry_id]

    temperature_entity_id = "sensor.zhimi_airpurifier_va1_temperature"
    humidity_entity_id = "sensor.zhimi_airpurifier_va1_humidity"

    async def run_service():
        def rh_t_getter():
            temp: State | None = hass.states.get(temperature_entity_id)
            rh: State | None = hass.states.get(humidity_entity_id)
            if temp is None:
                raise Exception("temperature state is None")
            if rh is None:
                raise Exception("humidity state is None")
            return float(rh.state) * 1000, float(temp.state) * 1000

        def value_update_callback(*args, **kwargs):
            callback = data.get(const.VALUE_UPDATE_CALLBACK)
            if callback is not None:
                callback(*args, **kwargs)

        def error_callback(*args, **kwargs):
            callback = data.get(const.ERROR_CALLBACK)
            if callback is not None:
                callback(*args, **kwargs)

        def run():
            _LOGGER.debug("start run_service")
            try:
                service.run(rh_t_getter, value_update_callback, error_callback)
            except Exception as e:
                _LOGGER.exception(f"service failed with {e}")

        return await asyncio.to_thread(run)

    task = asyncio.create_task(run_service())
    data["task"] = task
    # TODO:
    # entry.async_on_unload(
#         hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, service.stop)
#     )
    _LOGGER.debug(f"async_setup_entry {serial_id}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS)
    if unload_ok:
        data = hass.data[const.DOMAIN].pop(entry.entry_id)
        data["task"].cancel()
        service.stop()

    _LOGGER.debug(f"async_unload_entry: {unload_ok}")
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("async_remove_entry")
