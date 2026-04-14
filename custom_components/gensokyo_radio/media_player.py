"""Gensokyo Radio media_player entity."""
from __future__ import annotations

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
    CONF_STREAM_QUALITY,
    CONF_TARGET_PLAYER,
    DEFAULT_STREAM_QUALITY,
    DOMAIN,
    STREAM_URLS,
)
from .coordinator import GensokyoRadioCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Gensokyo Radio media player from a config entry."""
    coordinator: GensokyoRadioCoordinator = hass.data[DOMAIN][entry.entry_id]
    target_player = entry.data.get(CONF_TARGET_PLAYER)
    stream_quality = entry.data.get(CONF_STREAM_QUALITY, DEFAULT_STREAM_QUALITY)
    async_add_entities([GensokyoRadioMediaPlayer(coordinator, target_player, stream_quality)])


class GensokyoRadioMediaPlayer(CoordinatorEntity, MediaPlayerEntity):
    """Represents the currently playing track on Gensokyo Radio.

    When a target_player is configured, the entity gains PLAY and STOP
    support: pressing play sends the stream URL to the target media player;
    pressing stop halts playback on that player.  Without a target player
    the entity is read-only.
    """

    _attr_has_entity_name = True
    _attr_icon = "mdi:radio"

    def __init__(
        self,
        coordinator: GensokyoRadioCoordinator,
        target_player: str | None = None,
        stream_quality: str = DEFAULT_STREAM_QUALITY,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{DOMAIN}_media_player"
        self._attr_name = "Gensokyo Radio"
        self._target_player = target_player
        self._stream_url = STREAM_URLS.get(stream_quality, STREAM_URLS[DEFAULT_STREAM_QUALITY])

    @callback
    def _handle_coordinator_update(self) -> None:
        """Mark position timestamp on every coordinator refresh."""
        self._attr_media_position_updated_at = self.coordinator.last_update_success_time
        super()._handle_coordinator_update()

    # ------------------------------------------------------------------
    # MediaPlayerEntity properties
    # ------------------------------------------------------------------

    @property
    def supported_features(self) -> MediaPlayerEntityFeature:
        if self._target_player:
            return MediaPlayerEntityFeature.PLAY | MediaPlayerEntityFeature.STOP
        return MediaPlayerEntityFeature(0)

    @property
    def state(self) -> MediaPlayerState:
        return MediaPlayerState.PLAYING

    @property
    def media_content_id(self) -> str:
        return self._stream_url

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
        return self._songtimes.get("DURATION")

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
        attrs: dict = {
            "rating": self._songdata.get("RATING"),
            "times_rated": self._songdata.get("TIMESRATED"),
            "year": self._songinfo.get("YEAR"),
            "song_id": self._songdata.get("SONGID"),
            "album_id": self._songdata.get("ALBUMID"),
            "listeners": self._serverinfo.get("LISTENERS"),
            "circle_link": self._misc.get("CIRCLELINK"),
            "stream_url": self._stream_url,
        }
        if self._target_player:
            attrs["target_player"] = self._target_player
        return attrs

    # ------------------------------------------------------------------
    # Playback control (only active when target_player is configured)
    # ------------------------------------------------------------------

    async def async_media_play(self) -> None:
        """Start playing the Gensokyo Radio stream on the target player."""
        await self.hass.services.async_call(
            "media_player",
            "play_media",
            {
                "media_content_id": self._stream_url,
                "media_content_type": "music",
            },
            target={"entity_id": self._target_player},
        )

    async def async_media_stop(self) -> None:
        """Stop playback on the target player."""
        await self.hass.services.async_call(
            "media_player",
            "media_stop",
            {},
            target={"entity_id": self._target_player},
        )

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
