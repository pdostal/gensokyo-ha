"""Gensokyo Radio Home Assistant integration."""
from __future__ import annotations

import logging

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, PLATFORMS, SERVICE_PLAY, SERVICE_STOP
from .coordinator import GensokyoRadioCoordinator

_LOGGER = logging.getLogger(__name__)

_SERVICE_SCHEMA = vol.Schema({
    vol.Optional("entity_id"): cv.entity_ids,
})


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Gensokyo Radio from a config entry."""
    session = async_get_clientsession(hass)
    coordinator = GensokyoRadioCoordinator(hass, session)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    async def _handle_play(call: ServiceCall) -> None:
        entity_ids = call.data.get("entity_id", [])
        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if not state:
                continue
            target = state.attributes.get("target_player")
            stream_url = state.attributes.get("stream_url")
            if target and stream_url:
                await hass.services.async_call(
                    "media_player",
                    "play_media",
                    {
                        "entity_id": target,
                        "media_content_id": stream_url,
                        "media_content_type": "music",
                    },
                )

    async def _handle_stop(call: ServiceCall) -> None:
        entity_ids = call.data.get("entity_id", [])
        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if not state:
                continue
            target = state.attributes.get("target_player")
            if target:
                await hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": target},
                )

    hass.services.async_register(DOMAIN, SERVICE_PLAY, _handle_play, schema=_SERVICE_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_STOP, _handle_stop, schema=_SERVICE_SCHEMA)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    coordinator: GensokyoRadioCoordinator = hass.data[DOMAIN][entry.entry_id]
    await coordinator.async_shutdown()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        hass.services.async_remove(DOMAIN, SERVICE_PLAY)
        hass.services.async_remove(DOMAIN, SERVICE_STOP)

    return unload_ok
