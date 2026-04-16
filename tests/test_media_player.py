"""Tests for GensokyoRadioMediaPlayer entity."""

from __future__ import annotations

import pytest
from unittest.mock import patch, AsyncMock
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)

from custom_components.gensokyo_radio.const import (
    ALBUM_ART_BASE_URL,
    DEFAULT_STREAM_URL,
    DOMAIN,
    SONG_DETAIL_BASE_URL,
)
from custom_components.gensokyo_radio.coordinator import GensokyoRadioCoordinator
from custom_components.gensokyo_radio.media_player import GensokyoRadioMediaPlayer


@pytest.fixture
def coordinator(hass, mock_api_response):
    """Return a coordinator pre-loaded with mock data."""
    coord = GensokyoRadioCoordinator(hass)
    coord.data = mock_api_response
    return coord


@pytest.fixture
def media_player(coordinator):
    """Return a media player entity."""
    return GensokyoRadioMediaPlayer(coordinator)


# ------------------------------------------------------------------
# Basic state
# ------------------------------------------------------------------


def test_state_is_playing(media_player):
    assert media_player.state == MediaPlayerState.PLAYING


def test_media_title(media_player):
    assert media_player.media_title == "月齢11.3のキャンドルマジック"


def test_media_artist(media_player):
    assert media_player.media_artist == "3L"


def test_media_album_name(media_player):
    assert media_player.media_album_name == "ココロバイブレーション"


def test_media_album_artist(media_player):
    assert media_player.media_album_artist == "Shibayan Records"


def test_media_duration(media_player):
    assert media_player.media_duration == 394


def test_media_duration_defaults_to_one_minute_when_missing(coordinator):
    coordinator.data = {
        **coordinator.data,
        "SONGTIMES": {
            k: v for k, v in coordinator.data["SONGTIMES"].items() if k != "DURATION"
        },
    }

    assert GensokyoRadioMediaPlayer(coordinator).media_duration == 60


def test_media_position(media_player):
    assert media_player.media_position == 203


def test_entity_picture_url_built_correctly(media_player):
    expected = f"{ALBUM_ART_BASE_URL}STAL-1002_06266feabc.jpg"
    assert media_player.entity_picture == expected


def test_entity_picture_none_when_no_albumart(coordinator):
    coordinator.data = {
        **coordinator.data,
        "MISC": {**coordinator.data["MISC"], "ALBUMART": ""},
    }
    assert GensokyoRadioMediaPlayer(coordinator).entity_picture is None


def test_extra_attributes_contain_rating(media_player):
    attrs = media_player.extra_state_attributes
    assert attrs["rating"] == "4.36/5"
    assert attrs["times_rated"] == 131


def test_extra_attributes_contain_listeners(media_player):
    assert media_player.extra_state_attributes["listeners"] == 45


def test_extra_attributes_contain_song_metadata(media_player):
    attrs = media_player.extra_state_attributes
    assert attrs["year"] == "2010"
    assert attrs["song_id"] == 109311
    assert attrs["album_id"] == 10976


def test_extra_attributes_contain_song_url(media_player):
    expected = f"{SONG_DETAIL_BASE_URL}109311/"
    assert media_player.extra_state_attributes["song_url"] == expected


def test_unique_id(media_player):
    assert media_player.unique_id == f"{DOMAIN}_media_player"


def test_name(media_player):
    assert media_player.name == "Gensokyo Radio"


def test_icon_is_radio(media_player):
    assert media_player.icon == "mdi:radio"


def test_supported_features_zero(media_player):
    assert media_player.supported_features == 0


def test_media_content_id_is_default_stream(media_player):
    assert media_player.media_content_id == DEFAULT_STREAM_URL


def test_media_content_type_is_music(media_player):
    assert media_player.media_content_type == MediaType.MUSIC


# ------------------------------------------------------------------
# media_position_updated_at
# ------------------------------------------------------------------


def test_media_position_updated_at_tracks_coordinator_timestamp(coordinator, hass):
    from datetime import datetime, timezone

    fake_time = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)
    coordinator.last_update_success_time = fake_time

    player = GensokyoRadioMediaPlayer(coordinator)
    player.hass = hass
    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()

    assert player._attr_media_position_updated_at == fake_time


# ------------------------------------------------------------------
# Boot-time position stamping
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_async_added_to_hass_stamps_position_on_boot(coordinator):
    from datetime import datetime, timezone

    fake_time = datetime(2026, 4, 14, 10, 0, 0, tzinfo=timezone.utc)
    coordinator.last_update_success_time = fake_time

    player = GensokyoRadioMediaPlayer(coordinator)
    with patch.object(
        type(player).__mro__[2], "async_added_to_hass", new_callable=AsyncMock
    ):
        with patch.object(player, "async_write_ha_state"):
            await player.async_added_to_hass()

    assert player._attr_media_position_updated_at == fake_time


# ------------------------------------------------------------------
# Logbook events
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_song_change_fires_logbook_event(coordinator, hass):
    from homeassistant.components.logbook import EVENT_LOGBOOK_ENTRY

    player = GensokyoRadioMediaPlayer(coordinator)
    player.hass = hass

    fired = []
    hass.bus.async_listen(EVENT_LOGBOOK_ENTRY, lambda e: fired.append(e))

    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()
    await hass.async_block_till_done()

    assert len(fired) == 1
    assert "月齢11.3のキャンドルマジック" in fired[0].data["message"]

    # Same song ID — no second event
    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()
    await hass.async_block_till_done()
    assert len(fired) == 1

    # New song ID — fires again
    coordinator.data = {
        **coordinator.data,
        "SONGDATA": {**coordinator.data["SONGDATA"], "SONGID": 999},
        "SONGINFO": {
            **coordinator.data["SONGINFO"],
            "TITLE": "New Song",
            "ARTIST": "DJ Test",
        },
    }
    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()
    await hass.async_block_till_done()

    assert len(fired) == 2
    assert "New Song" in fired[1].data["message"]
