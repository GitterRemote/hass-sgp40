"""The Sensirion SGP40 integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from sgp40 import service

from . import const

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sersor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sensirion SGP40 from a config entry."""
    _LOGGER.debug("async_setup_entry")
    # TODO Store an API object for your platforms to access
    # hass.data[DOMAIN][entry.entry_id] = MyApi(...)

    serial_id = service.init()

    hass.data[const.DOMAIN][entry.entry_id] = {
        const.SERIAL_ID: serial_id,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    data = hass.data[const.DOMAIN][entry.entry_id]
    value_update_callback = data[const.VALUE_UPDATE_CALLBACK]
    error_callback = data[const.ERROR_CALLBACK]
    res = value_update_callback and error_callback
    _LOGGER.debug(f"async_setup_entry {serial_id} {res}")
    if res:
        hass.add_job(service.run, None, value_update_callback, error_callback)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry")
    unload_ok = await hass.config_entries.async_unload_platforms(
        entry, PLATFORMS)
    if unload_ok:
        hass.data[const.DOMAIN].pop(entry.entry_id)
        service.stop()

    _LOGGER.debug(f"async_unload_entry: {unload_ok}")
    return unload_ok


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    _LOGGER.debug("async_remove_entry")
