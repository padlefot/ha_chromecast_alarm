"""Event platform: fires when the alarm triggers."""
from __future__ import annotations

from homeassistant.components.event import EventEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_RUNNERS, DOMAIN
from .coordinator import AlarmRunner


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    runner: AlarmRunner = hass.data[DOMAIN][DATA_RUNNERS][entry.entry_id]
    async_add_entities([ChromecastAlarmEvent(runner, entry)])


class ChromecastAlarmEvent(EventEntity):
    """Fires an event each time the alarm goes off."""

    _attr_has_entity_name = False
    _attr_icon = "mdi:alarm-bell"
    _attr_event_types = ["alarm_fired"]

    def __init__(self, runner: AlarmRunner, entry: ConfigEntry) -> None:
        self._runner = runner
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_event"
        self._attr_name = f"{entry.title} Event"

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()

        @callback
        def _on_event(event_type: str, event_attributes: dict) -> None:
            self._trigger_event(event_type, event_attributes)
            self.async_write_ha_state()

        self._runner.set_event_callback(_on_event)

    async def async_will_remove_from_hass(self) -> None:
        self._runner.clear_event_callback()
