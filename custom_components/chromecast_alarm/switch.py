"""Switch platform: master enable/disable per alarm."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from .const import DATA_RUNNERS, DOMAIN
from .coordinator import AlarmRunner


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runner: AlarmRunner = hass.data[DOMAIN][DATA_RUNNERS][entry.entry_id]
    async_add_entities([ChromecastAlarmSwitch(runner, entry)])


class ChromecastAlarmSwitch(SwitchEntity, RestoreEntity):
    """Master enable for an alarm. Persists across HA restarts."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:alarm"

    def __init__(self, runner: AlarmRunner, entry: ConfigEntry) -> None:
        self._runner = runner
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_switch"
        self._attr_name = entry.title
        self._unsub_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        # Restore previous state (default on).
        last = await self.async_get_last_state()
        enabled = True
        if last is not None and last.state in ("on", "off"):
            enabled = last.state == "on"
        await self._runner.async_set_enabled(enabled)

        @callback
        def _refresh() -> None:
            self.async_write_ha_state()

        self._unsub_listener = self._runner.add_listener(_refresh)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None

    @property
    def is_on(self) -> bool:
        return self._runner.enabled

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self._runner.async_set_enabled(True)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self._runner.async_set_enabled(False)
        self.async_write_ha_state()
