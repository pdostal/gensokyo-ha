"""Config flow for Gensokyo Radio integration."""
from __future__ import annotations

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


class GensokyoRadioConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Single-step config flow — no options required."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Gensokyo Radio", data={})

        return self.async_show_form(step_id="user")
