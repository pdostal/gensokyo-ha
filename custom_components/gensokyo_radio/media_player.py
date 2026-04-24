"""Gensokyo Radio media_player entity."""

from __future__ import annotations

from homeassistant.components.logbook import (
    EVENT_LOGBOOK_ENTRY,
    LOGBOOK_ENTRY_DOMAIN,
    LOGBOOK_ENTRY_ENTITY_ID,
    LOGBOOK_ENTRY_MESSAGE,
    LOGBOOK_ENTRY_NAME,
)
from homeassistant.components.media_player import (
    MediaPlayerEntity,
    MediaPlayerEntityFeature,
    MediaPlayerState,
    MediaType,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ALBUM_ART_BASE_URL,
    DEFAULT_STREAM_URL,
    DOMAIN,
    SONG_DETAIL_BASE_URL,
)
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
    """Read-only media player that mirrors what is currently playing on Gensokyo Radio."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:radio"
    _attr_supported_features = MediaPlayerEntityFeature(0)

    def __init__(self, coordinator: GensokyoRadioCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_media_player"
        self._attr_name = "Gensokyo Radio"
        self._last_song_id: int | None = None

    async def async_added_to_hass(self) -> None:
        """Stamp position timestamp immediately so the progress bar works on boot."""
        await super().async_added_to_hass()
        self._attr_media_position_updated_at = self.coordinator.last_update_success_time
        self.async_write_ha_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Mark position timestamp and log song changes on every coordinator refresh."""
        self._attr_media_position_updated_at = self.coordinator.last_update_success_time
        new_song_id = self._songdata.get("SONGID")
        if new_song_id is not None and new_song_id != self._last_song_id:
            self._last_song_id = new_song_id
            title = self._songinfo.get("TITLE", "Unknown")
            artist = self._songinfo.get("ARTIST", "Unknown")
            self.hass.bus.async_fire(
                EVENT_LOGBOOK_ENTRY,
                {
                    LOGBOOK_ENTRY_NAME: "Gensokyo Radio",
                    LOGBOOK_ENTRY_MESSAGE: f"Now playing: {title} by {artist}",
                    LOGBOOK_ENTRY_DOMAIN: DOMAIN,
                    LOGBOOK_ENTRY_ENTITY_ID: self.entity_id,
                },
            )
        super()._handle_coordinator_update()

    # ------------------------------------------------------------------
    # MediaPlayerEntity properties
    # ------------------------------------------------------------------

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.PLAYING

    @property
    def media_content_id(self) -> str:
        return DEFAULT_STREAM_URL

    @property
    def media_content_type(self) -> MediaType:
        return MediaType.MUSIC

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
        duration = self._songtimes.get("DURATION")
        return duration if duration is not None else 60

    @property
    def media_position(self) -> int | None:
        return self._songtimes.get("PLAYED")

    @property
    def entity_picture(self) -> str | None:
        albumart = self._misc.get("ALBUMART", "")
        if not albumart:
            return None
        return f"{ALBUM_ART_BASE_URL}{albumart}"

    @property
    def extra_state_attributes(self) -> dict:
        song_id = self._songdata.get("SONGID")
        return {
            "rating": self._songdata.get("RATING"),
            "times_rated": self._songdata.get("TIMESRATED"),
            "year": self._songinfo.get("YEAR"),
            "song_id": song_id,
            "album_id": self._songdata.get("ALBUMID"),
            "listeners": self._serverinfo.get("LISTENERS"),
            "circle_link": self._misc.get("CIRCLELINK"),
            "song_url": f"{SONG_DETAIL_BASE_URL}{song_id}/" if song_id else None,
            "stream_url": DEFAULT_STREAM_URL,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @property
    def _data(self) -> dict:
        """Return the last payload, or empty if the last fetch failed.

        We deliberately drop stale data on failure — better to show nothing
        than a track that may no longer be playing.
        """
        if not self.coordinator.last_update_success:
            return {}
        return self.coordinator.data or {}

    @property
    def _songinfo(self) -> dict:
        return self._data.get("SONGINFO", {})

    @property
    def _songtimes(self) -> dict:
        return self._data.get("SONGTIMES", {})

    @property
    def _songdata(self) -> dict:
        return self._data.get("SONGDATA", {})

    @property
    def _misc(self) -> dict:
        return self._data.get("MISC", {})

    @property
    def _serverinfo(self) -> dict:
        return self._data.get("SERVERINFO", {})
