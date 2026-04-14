"""DataUpdateCoordinator with smart per-song polling for Gensokyo Radio."""
from __future__ import annotations

import logging
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    DOMAIN,
    ERROR_RETRY_DELAY,
    REQUEST_TIMEOUT,
    UPDATE_DELAY_AFTER_SONG,
)

_LOGGER = logging.getLogger(__name__)


class GensokyoRadioCoordinator(DataUpdateCoordinator):
    """Coordinator that polls only when the current track ends.

    Instead of a fixed interval, each successful fetch reads
    SONGTIMES.REMAINING from the API and schedules the next refresh for
    (remaining + UPDATE_DELAY_AFTER_SONG) seconds later.  On error it
    falls back to ERROR_RETRY_DELAY seconds.
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
            _LOGGER.warning("Gensokyo Radio API error: %s — retrying in %ss", err, ERROR_RETRY_DELAY)
            self._schedule_next(ERROR_RETRY_DELAY)
            raise UpdateFailed(f"Error fetching Gensokyo Radio data: {err}") from err
        finally:
            if own_session:
                await session.close()

        remaining = data.get("SONGTIMES", {}).get("REMAINING", ERROR_RETRY_DELAY)
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

    def _schedule_next(self, delay: float) -> None:
        """Cancel any existing wakeup and schedule a new one."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        self._unsub = async_call_later(self.hass, delay, self._handle_wakeup)

    def _handle_wakeup(self, _now: Any) -> None:
        """Called by async_call_later; triggers the next data refresh."""
        self.hass.async_create_task(self.async_refresh())

    async def async_shutdown(self) -> None:
        """Cancel pending timer on integration unload."""
        if self._unsub is not None:
            self._unsub()
            self._unsub = None
        await super().async_shutdown()
