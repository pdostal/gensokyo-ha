"""DataUpdateCoordinator with smart per-song polling for Gensokyo Radio."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import (
    TimestampDataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    API_URL,
    DOMAIN,
    ERROR_RETRY_DELAYS,
    REQUEST_TIMEOUT,
    UPDATE_DELAY_AFTER_SONG,
)

_LOGGER = logging.getLogger(__name__)

_PLACEHOLDERS = {"", "unknown", "none", "null"}


def _is_placeholder(value: Any) -> bool:
    """True when the API field is missing, empty, or a known placeholder string."""
    if value is None:
        return True
    if isinstance(value, str) and value.strip().lower() in _PLACEHOLDERS:
        return True
    return False


def _looks_valid(data: dict) -> bool:
    """Sanity-check an API payload before trusting it.

    The API occasionally returns a 200 with all fields set to "Unknown"/empty
    (e.g. during stream hiccups). Treat those as errors so we retry instead of
    surfacing a bogus "Unknown track" to the UI.
    """
    if not isinstance(data, dict):
        return False
    songinfo = data.get("SONGINFO") or {}
    songdata = data.get("SONGDATA") or {}
    if _is_placeholder(songinfo.get("TITLE")):
        return False
    if _is_placeholder(songinfo.get("ARTIST")):
        return False
    if _is_placeholder(songdata.get("SONGID")):
        return False
    return True


class GensokyoRadioCoordinator(TimestampDataUpdateCoordinator):
    """Coordinator that polls only when the current track ends.

    After each successful fetch it reads SONGTIMES.REMAINING and schedules
    the next refresh via async_call_later for (remaining + UPDATE_DELAY_AFTER_SONG)
    seconds.  On error (or placeholder/"Unknown" payload) it backs off through
    ERROR_RETRY_DELAYS.

    Inherits from TimestampDataUpdateCoordinator so that last_update_success_time
    is always a valid datetime — required for media_position_updated_at.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=None,  # We own the schedule
        )
        self._session = session
        self._unsub: Any = None  # cancellable returned by async_call_later
        self._error_count = 0

    # ------------------------------------------------------------------
    # DataUpdateCoordinator interface
    # ------------------------------------------------------------------

    async def _async_update_data(self) -> dict:
        """Fetch current playing data from the Gensokyo Radio API."""
        session = self._session or aiohttp.ClientSession()
        own_session = self._session is None
        try:
            async with session.get(
                API_URL,
                timeout=aiohttp.ClientTimeout(total=REQUEST_TIMEOUT),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json(content_type=None)
        except Exception as err:
            self._fail(f"Gensokyo Radio API error: {err}")
            raise UpdateFailed(f"Error fetching Gensokyo Radio data: {err}") from err
        finally:
            if own_session:
                await session.close()

        if not _looks_valid(data):
            self._fail("Gensokyo Radio API returned placeholder/empty track data")
            raise UpdateFailed("Gensokyo Radio API returned placeholder/empty track data")

        self._error_count = 0
        remaining = data.get("SONGTIMES", {}).get("REMAINING", UPDATE_DELAY_AFTER_SONG)
        delay = max(float(remaining) + UPDATE_DELAY_AFTER_SONG, UPDATE_DELAY_AFTER_SONG)
        _LOGGER.debug(
            "Now playing: %s — next poll in %.0fs",
            data.get("SONGINFO", {}).get("TITLE", "unknown"),
            delay,
        )
        self._schedule_next(delay)
        return data

    # ------------------------------------------------------------------
    # Internal scheduling
    # ------------------------------------------------------------------

    def _fail(self, reason: str) -> None:
        """Log, schedule a backoff retry, and bump the error counter."""
        retry_delay = ERROR_RETRY_DELAYS[
            min(self._error_count, len(ERROR_RETRY_DELAYS) - 1)
        ]
        self._error_count += 1
        _LOGGER.warning("%s — retrying in %ss", reason, retry_delay)
        self._schedule_next(retry_delay)

    def _schedule_next(self, delay: float) -> None:
        """Cancel any existing wakeup and schedule a new one."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._unsub = async_call_later(self.hass, delay, self._handle_wakeup)

    @callback
    def _handle_wakeup(self, _now: Any) -> None:
        """Called by async_call_later; triggers the next data refresh."""
        self.hass.async_create_background_task(
            self.async_refresh(),
            name=f"{DOMAIN}_scheduled_refresh",
        )

    async def async_shutdown(self) -> None:
        """Cancel pending timer on integration unload."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await super().async_shutdown()
