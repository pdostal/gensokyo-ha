"""Tests for Gensokyo Radio custom services."""
from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock
from aioresponses import aioresponses

from custom_components.gensokyo_radio.const import API_URL, DOMAIN, SERVICE_PLAY, SERVICE_STOP
from tests.conftest import MOCK_API_RESPONSE


async def _setup_entry(hass, mock_api_response):
    """Helper: load the integration entry and return it."""
    from homeassistant import config_entries
    from homeassistant.data_entry_flow import FlowResultType

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    "target_player": "media_player.living_room",
                    "stream_quality": "1",
                },
            )
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    return result2


@pytest.mark.asyncio
async def test_services_registered_after_setup(hass, mock_api_response):
    """play and stop services are registered once the entry is loaded."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            from homeassistant import config_entries

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            await hass.config_entries.flow.async_configure(result["flow_id"], user_input={})

    assert hass.services.has_service(DOMAIN, SERVICE_PLAY)
    assert hass.services.has_service(DOMAIN, SERVICE_STOP)


@pytest.mark.asyncio
async def test_play_service_calls_media_player(hass, mock_api_response):
    """gensokyo_radio.play delegates play_media to the configured target speaker."""
    await _setup_entry(hass, mock_api_response)

    # Inject a fake entity state so the service handler can read stream_url / target_player
    from homeassistant.core import State
    hass.states.async_set(
        "media_player.gensokyo_radio",
        "playing",
        {
            "target_player": "media_player.living_room",
            "stream_url": "https://stream.gensokyoradio.net/1/",
        },
    )

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_call:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_PLAY,
            {"entity_id": "media_player.gensokyo_radio"},
            blocking=True,
        )

    mock_call.assert_called_once_with(
        "media_player",
        "play_media",
        {
            "entity_id": "media_player.living_room",
            "media_content_id": "https://stream.gensokyoradio.net/1/",
            "media_content_type": "music",
        },
    )


@pytest.mark.asyncio
async def test_stop_service_calls_media_stop(hass, mock_api_response):
    """gensokyo_radio.stop delegates media_stop to the configured target speaker."""
    await _setup_entry(hass, mock_api_response)

    from homeassistant.core import State
    hass.states.async_set(
        "media_player.gensokyo_radio",
        "playing",
        {
            "target_player": "media_player.living_room",
            "stream_url": "https://stream.gensokyoradio.net/1/",
        },
    )

    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_call:
        await hass.services.async_call(
            DOMAIN,
            SERVICE_STOP,
            {"entity_id": "media_player.gensokyo_radio"},
            blocking=True,
        )

    mock_call.assert_called_once_with(
        "media_player",
        "media_stop",
        {"entity_id": "media_player.living_room"},
    )


@pytest.mark.asyncio
async def test_services_removed_on_unload(hass, mock_api_response):
    """Services are removed when the config entry is unloaded."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            from homeassistant import config_entries

            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result2 = await hass.config_entries.flow.async_configure(result["flow_id"], user_input={})

    entry_id = result2["result"].entry_id
    assert hass.services.has_service(DOMAIN, SERVICE_PLAY)

    await hass.config_entries.async_unload(entry_id)

    assert not hass.services.has_service(DOMAIN, SERVICE_PLAY)
    assert not hass.services.has_service(DOMAIN, SERVICE_STOP)
