"""The Sensirion SGP40 integration."""
from __future__ import annotations
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from sgp40 import service

from . import const

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Sensirion SGP40 from a config entry."""
    _LOGGER.debug("async_setup_entry")
    domain_data = hass.data.setdefault(const.DOMAIN, {})

    # TODO: move init into config flow and store serial_id in daa
    serial_id = service.init()

    domain_data[entry.entry_id] = {
        const.SERIAL_ID: serial_id,
    }

    hass.config_entries.async_setup_platforms(entry, PLATFORMS)

    data = domain_data[entry.entry_id]

    def run_service():
        _LOGGER.debug("start run_service")
        service.run(
            None,
            data.get(const.VALUE_UPDATE_CALLBACK),
            data.get(const.ERROR_CALLBACK),
        )

    hass.add_job(run_service)
    _LOGGER.debug(f"async_setup_entry {serial_id}")

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
