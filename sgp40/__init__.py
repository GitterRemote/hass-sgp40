"""The Sensirion SGP40 integration."""
from __future__ import annotations
import asyncio
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STOP
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State
from sgp40 import service as service_mod

from . import const

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sensirion SGP40 from a config entry."""
    _LOGGER.debug("async_setup_entry")
    domain_data = hass.data.setdefault(const.DOMAIN, {})

    data = domain_data.get(entry.entry_id)
    if not data:
        # TODO: move init into config flow and store serial_id in entry, and
        # set the unique id of the flow
        service = service_mod.Service()
        serial_id = await service.init()
        data = domain_data[entry.entry_id] = {
            const.SERIAL_ID: serial_id,
            const.SERVICE: service,
        }
    else:
        service = data[const.SERVICE]
        serial_id = data[const.SERIAL_ID]

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    # TODO: move config to config options
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
            return int(float(rh.state) * 1000), int(float(temp.state) * 1000)

        _LOGGER.debug("start run_service")
        try:
            await service.run(rh_t_getter)
        except Exception as e:
            _LOGGER.exception(f"service failed with {e}")

    data["task"] = asyncio.create_task(run_service())

    async def on_hass_stop(*args):
        # TODO: add option to indicate whether to stop heater when hass stopped
        _LOGGER.debug("stopping sgp40 service")
        await service.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, on_hass_stop)
    )

    _LOGGER.debug(f"async_setup_entry {serial_id}")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS)
    if unload_ok:
        # keep the service for next time reuse, because service init has bug
        # for reconnecting to the sensor
        data = hass.data[const.DOMAIN][entry.entry_id]
        await data[const.SERVICE].stop()
        done = data.pop("task").done()
        _LOGGER.debug(f"async_unload_entry: task done: {done}")

    _LOGGER.debug(f"async_unload_entry: {unload_ok}")
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("async_remove_entry")
