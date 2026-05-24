"""Button platform: Snooze and Dismiss for each alarm."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_RUNNERS, DOMAIN
from .coordinator import AlarmRunner


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runner: AlarmRunner = hass.data[DOMAIN][DATA_RUNNERS][entry.entry_id]
    async_add_entities(
        [
            ChromecastAlarmSnoozeButton(runner, entry),
            ChromecastAlarmDismissButton(runner, entry),
        ]
    )


class _BaseAlarmButton(ButtonEntity):
    _attr_has_entity_name = False

    def __init__(self, runner: AlarmRunner, entry: ConfigEntry, suffix: str, icon: str) -> None:
        self._runner = runner
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{suffix}"
        self._attr_name = f"{entry.title} {suffix.capitalize()}"
        self._attr_icon = icon


class ChromecastAlarmSnoozeButton(_BaseAlarmButton):
    def __init__(self, runner: AlarmRunner, entry: ConfigEntry) -> None:
        super().__init__(runner, entry, "snooze", "mdi:alarm-snooze")

    async def async_press(self) -> None:
        await self._runner.async_snooze()


class ChromecastAlarmDismissButton(_BaseAlarmButton):
    def __init__(self, runner: AlarmRunner, entry: ConfigEntry) -> None:
        super().__init__(runner, entry, "dismiss", "mdi:alarm-off")

    async def async_press(self) -> None:
        await self._runner.async_dismiss()
