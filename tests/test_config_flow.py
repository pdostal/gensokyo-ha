"""Tests for Gensokyo Radio config flow."""
from __future__ import annotations

import pytest
from unittest.mock import patch
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from aioresponses import aioresponses

from custom_components.gensokyo_radio.const import (
    API_URL,
    CONF_STREAM_QUALITY,
    CONF_TARGET_PLAYER,
    DEFAULT_STREAM_QUALITY,
    DOMAIN,
    STREAM_URLS,
)
from tests.conftest import MOCK_API_RESPONSE


@pytest.mark.asyncio
async def test_flow_creates_entry_no_target(hass, mock_api_response):
    """User flow without a target player creates entry with default stream quality."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={}
            )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Gensokyo Radio"
    assert result2["data"][CONF_STREAM_QUALITY] == DEFAULT_STREAM_QUALITY
    assert CONF_TARGET_PLAYER not in result2["data"]


@pytest.mark.asyncio
async def test_flow_creates_entry_with_target_player(hass, mock_api_response):
    """User flow with a target player stores it in entry data."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={
                    CONF_TARGET_PLAYER: "media_player.living_room",
                    CONF_STREAM_QUALITY: "3",
                },
            )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["data"][CONF_TARGET_PLAYER] == "media_player.living_room"
    assert result2["data"][CONF_STREAM_QUALITY] == "3"


@pytest.mark.asyncio
async def test_flow_stream_quality_selects_correct_url(hass, mock_api_response):
    """Chosen stream quality is stored and maps to the right URL."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"],
                user_input={CONF_STREAM_QUALITY: "4"},
            )

    quality = result2["data"][CONF_STREAM_QUALITY]
    assert STREAM_URLS[quality] == "https://stream.gensokyoradio.net/4/"


@pytest.mark.asyncio
async def test_duplicate_entry_aborts(hass, mock_api_response):
    """Second attempt to add the integration is aborted."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={}
            )
    assert result2["type"] == FlowResultType.CREATE_ENTRY

    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "single_instance_allowed"
