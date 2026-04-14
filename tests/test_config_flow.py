"""Tests for Gensokyo Radio config flow."""
from __future__ import annotations

import pytest
from unittest.mock import patch
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from aioresponses import aioresponses

from custom_components.gensokyo_radio.const import DOMAIN, API_URL
from tests.conftest import MOCK_API_RESPONSE


@pytest.mark.asyncio
async def test_flow_creates_entry(hass, mock_api_response):
    """User flow completes and creates a config entry."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ):
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )

    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "user"

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ):
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={}
            )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "Gensokyo Radio"
    assert result2["data"] == {}


@pytest.mark.asyncio
async def test_duplicate_entry_aborts(hass, mock_api_response):
    """Second attempt to add the integration is aborted."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ):
            # Create first entry
            result = await hass.config_entries.flow.async_init(
                DOMAIN, context={"source": config_entries.SOURCE_USER}
            )
            result2 = await hass.config_entries.flow.async_configure(
                result["flow_id"], user_input={}
            )
    assert result2["type"] == FlowResultType.CREATE_ENTRY

    # Attempt second entry
    result3 = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result3["type"] == FlowResultType.ABORT
    assert result3["reason"] == "single_instance_allowed"
