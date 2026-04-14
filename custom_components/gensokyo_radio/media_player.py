"""Gensokyo Radio media_player entity."""
from __future__ import annotations

from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerState,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import ALBUM_ART_BASE_URL, DOMAIN
from .coordinator import GensokyoRadioCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gensokyo Radio media player from a config entry."""
    coordinator: GensokyoRadioCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GensokyoRadioMediaPlayer(coordinator)])


class GensokyoRadioMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Represents the currently playing track on Gensokyo Radio.

    The entity is always in PLAYING state — the station never stops.
    All media controls are unsupported; this is a read-only view of a
    live internet radio stream.
    """

    _attr_has_entity_name = True
    _attr_supported_features = 0

    def __init__(self, coordinator: GensokyoRadioCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_media_player"
        self._attr_name = "Gensokyo Radio"

    # ------------------------------------------------------------------
    # MediaPlayerEntity properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.PLAYING

    @property
    def media_title(self) -> str | None:
        return self._songinfo.get("TITLE")

    @property
    def media_artist(self) -> str | None:
        return self._songinfo.get("ARTIST")

    @property
    def media_album_name(self) -> str | None:
        return self._songinfo.get("ALBUM")

    @property
    def media_album_artist(self) -> str | None:
        """CIRCLE is the doujin circle / label."""
        return self._songinfo.get("CIRCLE")

    @property
    def media_duration(self) -> int | None:
        return self._songtimes.get("DURATION")

    @property
    def media_position(self) -> int | None:
        return self._songtimes.get("PLAYED")

    @property
    def media_position_updated_at(self):
        """Timestamp of the last coordinator refresh, used by HA to tick position."""
        return self.coordinator.last_update_success_time if hasattr(self.coordinator, "last_update_success_time") else None

    @property
    def entity_picture(self) -> str | None:
        albumart = self._misc.get("ALBUMART", "")
        if not albumart:
            return None
        return f"{ALBUM_ART_BASE_URL}{albumart}"

    @property
    def extra_state_attributes(self) -> dict:
        return {
            "rating": self._songdata.get("RATING"),
            "times_rated": self._songdata.get("TIMESRATED"),
            "year": self._songinfo.get("YEAR"),
            "song_id": self._songdata.get("SONGID"),
            "album_id": self._songdata.get("ALBUMID"),
            "listeners": self._serverinfo.get("LISTENERS"),
            "circle_link": self._misc.get("CIRCLELINK"),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _songinfo(self) -> dict:
        return (self.coordinator.data or {}).get("SONGINFO", {})

    @property
    def _songtimes(self) -> dict:
        return (self.coordinator.data or {}).get("SONGTIMES", {})

    @property
    def _songdata(self) -> dict:
        return (self.coordinator.data or {}).get("SONGDATA", {})

    @property
    def _misc(self) -> dict:
        return (self.coordinator.data or {}).get("MISC", {})

    @property
    def _serverinfo(self) -> dict:
        return (self.coordinator.data or {}).get("SERVERINFO", {})
