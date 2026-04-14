"""Tests for GensokyoRadioCoordinator."""
from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from datetime import datetime, timezone
from aioresponses import aioresponses

from custom_components.gensokyo_radio.const import (
    API_URL,
    ERROR_RETRY_DELAY,
    UPDATE_DELAY_AFTER_SONG,
)
from custom_components.gensokyo_radio.coordinator import GensokyoRadioCoordinator


@pytest.mark.asyncio
async def test_initial_fetch_succeeds(hass, mock_api_response):
    """Coordinator fetches and parses API data correctly."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ):
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()

    assert coordinator.data["SONGINFO"]["TITLE"] == "月齢11.3のキャンドルマジック"
    assert coordinator.data["SONGINFO"]["ARTIST"] == "3L"
    assert coordinator.data["SONGTIMES"]["REMAINING"] == 191
    assert coordinator.data["MISC"]["ALBUMART"] == "STAL-1002_06266feabc.jpg"


@pytest.mark.asyncio
async def test_schedules_next_poll_at_remaining_plus_2(hass, mock_api_response):
    """Next poll is scheduled at SONGTIMES.REMAINING + UPDATE_DELAY_AFTER_SONG seconds."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ) as mock_call_later:
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()

    # REMAINING=191, UPDATE_DELAY_AFTER_SONG=2 → expected delay = 193
    expected_delay = mock_api_response["SONGTIMES"]["REMAINING"] + UPDATE_DELAY_AFTER_SONG
    mock_call_later.assert_called_once()
    _, args, _ = mock_call_later.mock_calls[0]
    assert args[0] is hass
    assert args[1] == expected_delay


@pytest.mark.asyncio
async def test_api_error_schedules_retry_in_30s(hass):
    """HTTP error triggers a retry after ERROR_RETRY_DELAY seconds."""
    with aioresponses() as m:
        m.get(API_URL, status=500)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ) as mock_call_later:
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()

    mock_call_later.assert_called_once()
    _, args, _ = mock_call_later.mock_calls[0]
    assert args[1] == ERROR_RETRY_DELAY


@pytest.mark.asyncio
async def test_network_error_schedules_retry(hass):
    """Network/connection error also triggers a retry after ERROR_RETRY_DELAY."""
    import aiohttp

    with aioresponses() as m:
        m.get(API_URL, exception=aiohttp.ClientConnectionError("connection refused"))
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later"
        ) as mock_call_later:
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()

    mock_call_later.assert_called_once()
    _, args, _ = mock_call_later.mock_calls[0]
    assert args[1] == ERROR_RETRY_DELAY


@pytest.mark.asyncio
async def test_unsub_called_on_new_schedule(hass, mock_api_response):
    """Previous timer is cancelled when a new schedule is created."""
    mock_unsub = MagicMock()

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later",
            return_value=mock_unsub,
        ):
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()
            await coordinator.async_refresh()

    # First unsub should have been called when second schedule was set
    mock_unsub.assert_called_once()


@pytest.mark.asyncio
async def test_song_change_detected_between_refreshes(hass, mock_api_response):
    """Coordinator reflects new song data after SONGID changes."""
    second_response = {
        **mock_api_response,
        "SONGDATA": {**mock_api_response["SONGDATA"], "SONGID": 999999},
        "SONGINFO": {**mock_api_response["SONGINFO"], "TITLE": "New Song"},
    }

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        m.get(API_URL, payload=second_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()
            first_song_id = coordinator.data["SONGDATA"]["SONGID"]
            first_title = coordinator.data["SONGINFO"]["TITLE"]

            await coordinator.async_refresh()
            second_song_id = coordinator.data["SONGDATA"]["SONGID"]
            second_title = coordinator.data["SONGINFO"]["TITLE"]

    assert first_song_id == 109311
    assert first_title == "月齢11.3のキャンドルマジック"
    assert second_song_id == 999999
    assert second_title == "New Song"


@pytest.mark.asyncio
async def test_async_shutdown_cancels_pending_timer(hass, mock_api_response):
    """async_shutdown() cancels any scheduled wakeup."""
    mock_unsub = MagicMock()

    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch(
            "custom_components.gensokyo_radio.coordinator.async_call_later",
            return_value=mock_unsub,
        ):
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()
            await coordinator.async_shutdown()

    mock_unsub.assert_called_once()


@pytest.mark.asyncio
async def test_last_update_success_time_is_set_after_refresh(hass, mock_api_response):
    """TimestampDataUpdateCoordinator sets last_update_success_time after a successful fetch."""
    with aioresponses() as m:
        m.get(API_URL, payload=mock_api_response)
        with patch("custom_components.gensokyo_radio.coordinator.async_call_later"):
            coordinator = GensokyoRadioCoordinator(hass)
            await coordinator.async_refresh()

    assert coordinator.last_update_success_time is not None
    assert isinstance(coordinator.last_update_success_time, datetime)


def test_handle_wakeup_is_callback(hass):
    """_handle_wakeup must be decorated with @callback for HA safety."""
    from homeassistant.core import is_callback
    coordinator = GensokyoRadioCoordinator(hass)
    assert is_callback(coordinator._handle_wakeup)
