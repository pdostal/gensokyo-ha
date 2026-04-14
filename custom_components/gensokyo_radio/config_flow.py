"""Config flow for Gensokyo Radio integration."""
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_STREAM_QUALITY,
    CONF_TARGET_PLAYER,
    DEFAULT_STREAM_QUALITY,
    DOMAIN,
)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Optional(CONF_TARGET_PLAYER): selector.EntitySelector(
            selector.EntitySelectorConfig(domain="media_player")
        ),
        vol.Optional(CONF_STREAM_QUALITY, default=DEFAULT_STREAM_QUALITY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=[
                    selector.SelectOptionDict(value="1", label="128 kbps"),
                    selector.SelectOptionDict(value="3", label="256 kbps"),
                    selector.SelectOptionDict(value="4", label="1000 kbps / Lossless"),
                ]
            )
        ),
    }
)


class GensokyoRadioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Gensokyo Radio.

    The only user-supplied configuration is an optional target media player
    to play the stream on, and stream quality.
    """

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            data: dict = {
                CONF_STREAM_QUALITY: user_input.get(CONF_STREAM_QUALITY, DEFAULT_STREAM_QUALITY),
            }
            if user_input.get(CONF_TARGET_PLAYER):
                data[CONF_TARGET_PLAYER] = user_input[CONF_TARGET_PLAYER]
            return self.async_create_entry(title="Gensokyo Radio", data=data)

        return self.async_show_form(step_id="user", data_schema=STEP_USER_SCHEMA)
