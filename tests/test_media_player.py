"""Tests for GensokyoRadioMediaPlayer entity."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from homeassistant.components.media_player import (
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.core import HomeAssistant

from custom_components.gensokyo_radio.const import (
    ALBUM_ART_BASE_URL,
    CONF_STREAM_QUALITY,
    CONF_TARGET_PLAYER,
    DEFAULT_STREAM_QUALITY,
    DOMAIN,
    STREAM_URLS,
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
    """Return a read-only media player entity (no target player)."""
    return GensokyoRadioMediaPlayer(coordinator)


@pytest.fixture
def media_player_with_target(coordinator, hass):
    """Return a media player entity with a target speaker configured."""
    player = GensokyoRadioMediaPlayer(
        coordinator,
        target_player="media_player.living_room",
    )
    player.hass = hass
    return player


# ------------------------------------------------------------------
# Basic state
# ------------------------------------------------------------------

def test_state_is_playing(media_player):
    """Media player is always in PLAYING state (it's a radio stream)."""
    assert media_player.state == MediaPlayerState.PLAYING


def test_media_title(media_player):
    """media_title reflects SONGINFO.TITLE."""
    assert media_player.media_title == "月齢11.3のキャンドルマジック"


def test_media_artist(media_player):
    """media_artist reflects SONGINFO.ARTIST."""
    assert media_player.media_artist == "3L"


def test_media_album_name(media_player):
    """media_album_name reflects SONGINFO.ALBUM."""
    assert media_player.media_album_name == "ココロバイブレーション"


def test_media_album_artist(media_player):
    """media_album_artist reflects SONGINFO.CIRCLE (the doujin circle)."""
    assert media_player.media_album_artist == "Shibayan Records"


def test_media_duration(media_player):
    """media_duration reflects SONGTIMES.DURATION."""
    assert media_player.media_duration == 394


def test_media_position(media_player):
    """media_position reflects SONGTIMES.PLAYED."""
    assert media_player.media_position == 203


def test_entity_picture_url_built_correctly(media_player):
    """entity_picture is base URL + MISC.ALBUMART filename."""
    expected = f"{ALBUM_ART_BASE_URL}STAL-1002_06266feabc.jpg"
    assert media_player.entity_picture == expected


def test_entity_picture_none_when_no_albumart(coordinator):
    """entity_picture is None when ALBUMART is empty."""
    coordinator.data = {
        **coordinator.data,
        "MISC": {**coordinator.data["MISC"], "ALBUMART": ""},
    }
    player = GensokyoRadioMediaPlayer(coordinator)
    assert player.entity_picture is None


def test_extra_attributes_contain_rating(media_player):
    """extra_state_attributes includes rating."""
    attrs = media_player.extra_state_attributes
    assert attrs["rating"] == "4.36/5"
    assert attrs["times_rated"] == 131


def test_extra_attributes_contain_listeners(media_player):
    """extra_state_attributes includes listener count."""
    attrs = media_player.extra_state_attributes
    assert attrs["listeners"] == 45


def test_extra_attributes_contain_song_metadata(media_player):
    """extra_state_attributes includes year, song_id, album_id."""
    attrs = media_player.extra_state_attributes
    assert attrs["year"] == "2010"
    assert attrs["song_id"] == 109311
    assert attrs["album_id"] == 10976


def test_unique_id(media_player):
    """Entity has a stable unique_id."""
    assert media_player.unique_id == f"{DOMAIN}_media_player"


def test_name(media_player):
    """Entity name is 'Gensokyo Radio'."""
    assert media_player.name == "Gensokyo Radio"


def test_icon_is_radio(media_player):
    """Entity has a radio MDI icon."""
    assert media_player.icon == "mdi:radio"


# ------------------------------------------------------------------
# media_position_updated_at
# ------------------------------------------------------------------

def test_media_position_updated_at_tracks_coordinator_timestamp(coordinator, hass):
    """_handle_coordinator_update stamps _attr_media_position_updated_at from coordinator."""
    from datetime import datetime, timezone

    fake_time = datetime(2026, 4, 14, 12, 0, 0, tzinfo=timezone.utc)
    coordinator.last_update_success_time = fake_time

    player = GensokyoRadioMediaPlayer(coordinator)
    player.hass = hass
    # Patch super()._handle_coordinator_update so we don't need a full platform setup
    with patch.object(
        type(player).__mro__[2],  # CoordinatorEntity
        "_handle_coordinator_update",
    ):
        player._handle_coordinator_update()

    assert player._attr_media_position_updated_at == fake_time


# ------------------------------------------------------------------
# Stream URL / media content
# ------------------------------------------------------------------

def test_media_content_id_default_stream(media_player):
    """Default media_content_id points to stream 1 (128 kbps)."""
    assert media_player.media_content_id == STREAM_URLS[DEFAULT_STREAM_QUALITY]


def test_media_content_id_respects_quality(coordinator):
    """Stream URL reflects the configured stream quality."""
    player = GensokyoRadioMediaPlayer(coordinator, stream_quality="4")
    assert player.media_content_id == STREAM_URLS["4"]


def test_media_content_type_is_music(media_player):
    """media_content_type is MUSIC."""
    assert media_player.media_content_type == MediaType.MUSIC


def test_extra_attributes_contain_stream_url(media_player):
    """extra_state_attributes exposes the stream_url."""
    assert "stream_url" in media_player.extra_state_attributes
    assert media_player.extra_state_attributes["stream_url"].startswith("https://stream.gensokyoradio.net/")


# ------------------------------------------------------------------
# Supported features
# ------------------------------------------------------------------

def test_supported_features_zero_without_target(media_player):
    """No target player → no supported features."""
    assert media_player.supported_features == 0


def test_supported_features_play_stop_with_target(coordinator):
    """With a target player, PLAY and STOP are supported."""
    player = GensokyoRadioMediaPlayer(coordinator, target_player="media_player.speaker")
    assert player.supported_features & MediaPlayerEntityFeature.PLAY
    assert player.supported_features & MediaPlayerEntityFeature.STOP


def test_target_player_exposed_in_attributes(media_player_with_target):
    """target_player entity_id is exposed as an extra attribute."""
    assert media_player_with_target.extra_state_attributes["target_player"] == "media_player.living_room"


def test_target_player_not_in_attributes_when_unset(media_player):
    """target_player key is absent when no target is configured."""
    assert "target_player" not in media_player.extra_state_attributes


# ------------------------------------------------------------------
# Play / stop delegation
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_media_play_calls_play_media_on_target(media_player_with_target, hass):
    """async_media_play sends play_media to the configured target player."""
    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_call:
        await media_player_with_target.async_media_play()

    mock_call.assert_called_once_with(
        "media_player",
        "play_media",
        {
            "media_content_id": media_player_with_target.media_content_id,
            "media_content_type": "music",
        },
        target={"entity_id": "media_player.living_room"},
    )


@pytest.mark.asyncio
async def test_media_stop_calls_media_stop_on_target(media_player_with_target, hass):
    """async_media_stop sends media_stop to the configured target player."""
    with patch("homeassistant.core.ServiceRegistry.async_call", new_callable=AsyncMock) as mock_call:
        await media_player_with_target.async_media_stop()

    mock_call.assert_called_once_with(
        "media_player",
        "media_stop",
        {},
        target={"entity_id": "media_player.living_room"},
    )


# ------------------------------------------------------------------
# Boot-time position stamping
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_async_added_to_hass_stamps_position_on_boot(coordinator):
    """async_added_to_hass stamps _attr_media_position_updated_at from coordinator on boot."""
    from datetime import datetime, timezone

    fake_time = datetime(2026, 4, 14, 10, 0, 0, tzinfo=timezone.utc)
    coordinator.last_update_success_time = fake_time

    player = GensokyoRadioMediaPlayer(coordinator)

    # Simulate adding to hass — super().async_added_to_hass needs hass set
    with patch.object(type(player).__mro__[2], "async_added_to_hass", new_callable=AsyncMock):
        with patch.object(player, "async_write_ha_state"):
            await player.async_added_to_hass()

    assert player._attr_media_position_updated_at == fake_time


# ------------------------------------------------------------------
# Logbook events
# ------------------------------------------------------------------

def test_song_change_fires_logbook_event(coordinator, hass):
    """_handle_coordinator_update fires a logbook event when SONGID changes."""
    from homeassistant.components.logbook import EVENT_LOGBOOK_ENTRY

    player = GensokyoRadioMediaPlayer(coordinator)
    player.hass = hass

    fired_events = []
    hass.bus.listen(EVENT_LOGBOOK_ENTRY, lambda e: fired_events.append(e))

    # First update — _last_song_id starts as None so this always fires
    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()

    assert len(fired_events) == 1
    assert "月齢11.3のキャンドルマジック" in fired_events[0].data["message"]

    # Second update with same SONGID — should NOT fire again
    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()

    assert len(fired_events) == 1  # still 1

    # Change SONGID in coordinator data
    coordinator.data = {
        **coordinator.data,
        "SONGDATA": {**coordinator.data["SONGDATA"], "SONGID": 999999},
        "SONGINFO": {**coordinator.data["SONGINFO"], "TITLE": "New Song", "ARTIST": "New Artist"},
    }

    with patch.object(type(player).__mro__[2], "_handle_coordinator_update"):
        player._handle_coordinator_update()

    assert len(fired_events) == 2
    assert "New Song" in fired_events[1].data["message"]
    assert "New Artist" in fired_events[1].data["message"]
