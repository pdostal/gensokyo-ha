"""Shared fixtures for Gensokyo Radio tests."""
from __future__ import annotations

import pytest
from unittest.mock import patch

pytest_plugins = "pytest_homeassistant_custom_component"


MOCK_API_RESPONSE = {
    "SERVERINFO": {
        "LASTUPDATE": 1776180881,
        "SERVERS": 5,
        "STATUS": "OK",
        "LISTENERS": 45,
        "STREAMS": {
            "1": {"BITRATE": 128, "LISTENERS": 31},
            "2": {"BITRATE": 64, "LISTENERS": 1},
            "3": {"BITRATE": 256, "LISTENERS": 11},
            "4": {"BITRATE": 1000, "LISTENERS": 2},
            "5": {"BITRATE": "", "LISTENERS": 0},
        },
        "MODE": "RADIO",
    },
    "SONGINFO": {
        "TITLE": "月齢11.3のキャンドルマジック",
        "ARTIST": "3L",
        "ALBUM": "ココロバイブレーション",
        "YEAR": "2010",
        "CIRCLE": "Shibayan Records",
    },
    "SONGTIMES": {
        "DURATION": 394,
        "PLAYED": 203,
        "REMAINING": 191,
        "SONGSTART": 1776180678,
        "SONGEND": 1776181072,
    },
    "SONGDATA": {
        "SONGID": 109311,
        "ALBUMID": 10976,
        "RATING": "4.36/5",
        "TIMESRATED": 131,
    },
    "MISC": {
        "CIRCLELINK": "",
        "ALBUMART": "STAL-1002_06266feabc.jpg",
        "CIRCLEART": "",
        "OFFSET": "0",
        "OFFSETTIME": 1776180881,
    },
}


@pytest.fixture
def mock_api_response():
    """Return a copy of the mock API response."""
    return dict(MOCK_API_RESPONSE)


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    yield
