"""Persistent runtime state for each alarm (snooze, dismiss).

Persisted via Home Assistant's Store so snooze and dismiss survive restarts.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from .const import STORAGE_KEY_TEMPLATE, STORAGE_VERSION


@dataclass
class AlarmState:
    """Per-alarm runtime state persisted across HA restarts."""

    snooze_until: datetime | None = None
    dismissed_date: date | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "snooze_until": self.snooze_until.isoformat() if self.snooze_until else None,
            "dismissed_date": self.dismissed_date.isoformat() if self.dismissed_date else None,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "AlarmState":
        if not data:
            return cls()
        snooze_until_raw = data.get("snooze_until")
        dismissed_date_raw = data.get("dismissed_date")
        return cls(
            snooze_until=datetime.fromisoformat(snooze_until_raw) if snooze_until_raw else None,
            dismissed_date=date.fromisoformat(dismissed_date_raw) if dismissed_date_raw else None,
        )


class AlarmStore:
    """Thin async wrapper around HA's Store for one alarm config entry."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        key = STORAGE_KEY_TEMPLATE.format(entry_id=entry_id)
        self._store: Store = Store(hass, STORAGE_VERSION, key)
        self._state: AlarmState | None = None

    async def async_load(self) -> AlarmState:
        data = await self._store.async_load()
        self._state = AlarmState.from_dict(data)
        return self._state

    async def async_save(self, state: AlarmState) -> None:
        self._state = state
        await self._store.async_save(state.to_dict())

    @property
    def state(self) -> AlarmState:
        return self._state or AlarmState()
