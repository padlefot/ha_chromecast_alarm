"""Config and options flow for Chromecast Alarm."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_DAYS,
    CONF_HOLIDAY_COUNTRY,
    CONF_LIBRARY,
    CONF_SKIP_HOLIDAYS,
    CONF_SNOOZE_MINUTES,
    CONF_STOP_AFTER_MINUTES,
    CONF_TARGET,
    CONF_TIME,
    CONF_VOLUME,
    DAY_CODES,
    DEFAULT_DAYS,
    DEFAULT_HOLIDAY_COUNTRY,
    DEFAULT_SKIP_HOLIDAYS,
    DEFAULT_SNOOZE_MINUTES,
    DEFAULT_STOP_AFTER_MINUTES,
    DEFAULT_TIME,
    DEFAULT_VOLUME,
    DOMAIN,
)
from .media import library_to_text, parse_library_text


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required("name", default=defaults.get("name", "")): str,
            vol.Required(
                CONF_TARGET, default=defaults.get(CONF_TARGET, "")
            ): selector.EntitySelector(
                selector.EntitySelectorConfig(domain="media_player")
            ),
            vol.Required(
                CONF_TIME, default=defaults.get(CONF_TIME, DEFAULT_TIME)
            ): selector.TimeSelector(),
            vol.Required(
                CONF_DAYS, default=defaults.get(CONF_DAYS, list(DEFAULT_DAYS))
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value=d, label=d.capitalize())
                        for d in DAY_CODES
                    ],
                    multiple=True,
                    mode=selector.SelectSelectorMode.LIST,
                )
            ),
            vol.Required(
                CONF_SKIP_HOLIDAYS,
                default=defaults.get(CONF_SKIP_HOLIDAYS, DEFAULT_SKIP_HOLIDAYS),
            ): selector.BooleanSelector(),
            vol.Required(
                CONF_HOLIDAY_COUNTRY,
                default=defaults.get(CONF_HOLIDAY_COUNTRY, DEFAULT_HOLIDAY_COUNTRY),
            ): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=[
                        selector.SelectOptionDict(value="NO", label="Norway"),
                        selector.SelectOptionDict(value="SE", label="Sweden"),
                        selector.SelectOptionDict(value="DK", label="Denmark"),
                        selector.SelectOptionDict(value="FI", label="Finland"),
                        selector.SelectOptionDict(value="DE", label="Germany"),
                        selector.SelectOptionDict(value="GB", label="United Kingdom"),
                        selector.SelectOptionDict(value="US", label="United States"),
                        selector.SelectOptionDict(value="NL", label="Netherlands"),
                        selector.SelectOptionDict(value="FR", label="France"),
                        selector.SelectOptionDict(value="ES", label="Spain"),
                        selector.SelectOptionDict(value="IT", label="Italy"),
                        selector.SelectOptionDict(value="PL", label="Poland"),
                        selector.SelectOptionDict(value="AT", label="Austria"),
                        selector.SelectOptionDict(value="CH", label="Switzerland"),
                        selector.SelectOptionDict(value="PT", label="Portugal"),
                    ],
                    mode=selector.SelectSelectorMode.DROPDOWN,
                )
            ),
            vol.Required(
                CONF_VOLUME, default=defaults.get(CONF_VOLUME, DEFAULT_VOLUME)
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=0.0, max=1.0, step=0.05, mode=selector.NumberSelectorMode.SLIDER
                )
            ),
            vol.Required(
                CONF_SNOOZE_MINUTES,
                default=defaults.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=60, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                CONF_STOP_AFTER_MINUTES,
                default=defaults.get(CONF_STOP_AFTER_MINUTES, DEFAULT_STOP_AFTER_MINUTES),
            ): selector.NumberSelector(
                selector.NumberSelectorConfig(
                    min=1, max=120, step=1, mode=selector.NumberSelectorMode.BOX
                )
            ),
            vol.Required(
                "library_text",
                default=library_to_text(defaults.get(CONF_LIBRARY) or []),
            ): selector.TextSelector(
                selector.TextSelectorConfig(multiline=True)
            ),
        }
    )


def _post_process(user_input: dict[str, Any]) -> tuple[dict[str, Any], dict[str, str]]:
    """Convert library_text → library list. Return (cleaned, errors)."""
    errors: dict[str, str] = {}
    library = parse_library_text(user_input.get("library_text", ""))
    if not library:
        errors["library_text"] = "library_empty"
    cleaned = dict(user_input)
    cleaned[CONF_LIBRARY] = library
    cleaned.pop("library_text", None)
    return cleaned, errors


class ChromecastAlarmConfigFlow(ConfigFlow, domain=DOMAIN):
    """Initial config flow — one entry per alarm."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            cleaned, errors = _post_process(user_input)
            if not errors:
                name = cleaned.pop("name").strip() or "Chromecast Alarm"
                return self.async_create_entry(title=name, data=cleaned)
            return self.async_show_form(
                step_id="user", data_schema=_schema(user_input), errors=errors
            )
        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return ChromecastAlarmOptionsFlow(entry)


class ChromecastAlarmOptionsFlow(OptionsFlow):
    """Options flow — same fields, edits an existing alarm."""

    def __init__(self, entry: ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            cleaned, errors = _post_process(user_input)
            if not errors:
                # Name lives in entry.title; allow rename via the same form.
                new_name = cleaned.pop("name").strip()
                if new_name and new_name != self.entry.title:
                    self.hass.config_entries.async_update_entry(self.entry, title=new_name)
                return self.async_create_entry(title="", data=cleaned)
            return self.async_show_form(
                step_id="init", data_schema=_schema(user_input), errors=errors
            )
        merged = {**self.entry.data, **self.entry.options, "name": self.entry.title}
        return self.async_show_form(step_id="init", data_schema=_schema(merged))
