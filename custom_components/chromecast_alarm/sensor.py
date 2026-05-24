"""Sensor platform: `next_fire` timestamp per alarm."""
from __future__ import annotations

from datetime import datetime

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_RUNNERS, DOMAIN
from .coordinator import AlarmRunner


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runner: AlarmRunner = hass.data[DOMAIN][DATA_RUNNERS][entry.entry_id]
    async_add_entities([ChromecastAlarmNextFireSensor(runner, entry)])


class ChromecastAlarmNextFireSensor(SensorEntity):
    """Reports the datetime of the next scheduled fire."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:clock-outline"
    _attr_device_class = SensorDeviceClass.TIMESTAMP

    def __init__(self, runner: AlarmRunner, entry: ConfigEntry) -> None:
        self._runner = runner
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_next_fire"
        self._attr_name = f"{entry.title} Next fire"
        self._unsub_listener = None

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _refresh() -> None:
            self.async_write_ha_state()

        self._unsub_listener = self._runner.add_listener(_refresh)

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_listener:
            self._unsub_listener()
            self._unsub_listener = None

    @property
    def native_value(self) -> datetime | None:
        return self._runner.next_fire
