"""Tests for GensokyoRadioMediaPlayer entity."""
from __future__ import annotations

import pytest
from unittest.mock import patch, MagicMock
from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant

from custom_components.gensokyo_radio.const import (
    ALBUM_ART_BASE_URL,
    DOMAIN,
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
    """Return a media player entity with coordinator data."""
    return GensokyoRadioMediaPlayer(coordinator)


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


def test_supported_features_zero(media_player):
    """No media controls — it's a read-only radio stream."""
    assert media_player.supported_features == 0


def test_unique_id(media_player):
    """Entity has a stable unique_id."""
    assert media_player.unique_id == f"{DOMAIN}_media_player"


def test_name(media_player):
    """Entity name is 'Gensokyo Radio'."""
    assert media_player.name == "Gensokyo Radio"
