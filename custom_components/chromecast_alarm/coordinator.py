"""AlarmRunner: scheduling, firing, snoozing, dismissing per config entry."""
from __future__ import annotations

import asyncio
import logging
import random
from datetime import date, datetime, time, timedelta
from typing import Any, Callable

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import CALLBACK_TYPE, HomeAssistant, callback
from homeassistant.helpers.event import (
    async_call_later,
    async_track_time_change,
)
from homeassistant.util import dt as dt_util

from .const import (
    CONF_DAYS,
    CONF_LIBRARY,
    CONF_SNOOZE_MINUTES,
    CONF_STOP_AFTER_MINUTES,
    CONF_TARGET,
    CONF_TIME,
    CONF_VOLUME,
    DAY_CODES,
    DEFAULT_DAYS,
    DEFAULT_SNOOZE_MINUTES,
    DEFAULT_STOP_AFTER_MINUTES,
    DEFAULT_TIME,
    DEFAULT_VOLUME,
)
from .media import extract_audio_url, is_youtube_url
from .store import AlarmState, AlarmStore

_LOGGER = logging.getLogger(__name__)


def _parse_time(value: Any) -> time:
    """Parse a stored time value (HH:MM or HH:MM:SS) into a time object."""
    if isinstance(value, time):
        return value
    if isinstance(value, str):
        parts = value.split(":")
        try:
            h = int(parts[0])
            m = int(parts[1]) if len(parts) > 1 else 0
            s = int(parts[2]) if len(parts) > 2 else 0
            return time(hour=h, minute=m, second=s)
        except (ValueError, IndexError):
            pass
    return _parse_time(DEFAULT_TIME)


class AlarmRunner:
    """Runtime controller for a single alarm config entry."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self._store = AlarmStore(hass, entry.entry_id)
        self._state: AlarmState = AlarmState()
        self._enabled: bool = True
        self._is_firing: bool = False
        self._unsub_time_listener: CALLBACK_TYPE | None = None
        self._unsub_snooze: CALLBACK_TYPE | None = None
        self._unsub_autostop: CALLBACK_TYPE | None = None
        self._next_fire: datetime | None = None
        self._listeners: list[Callable[[], None]] = []
        self._event_callback: Callable[[str, dict], None] | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def async_start(self) -> None:
        """Load persisted state and arm the scheduler."""
        self._state = await self._store.async_load()
        # If a snooze was pending and is still in the future, re-arm it.
        if self._state.snooze_until and self._state.snooze_until > dt_util.utcnow():
            remaining = (self._state.snooze_until - dt_util.utcnow()).total_seconds()
            _LOGGER.debug(
                "[%s] Re-arming pending snooze fire in %.0fs", self.entry.title, remaining
            )
            self._unsub_snooze = async_call_later(self.hass, remaining, self._snooze_fire)
        self._arm_time_listener()
        self._refresh_next_fire()

    async def async_stop(self) -> None:
        """Tear down all listeners."""
        if self._unsub_time_listener:
            self._unsub_time_listener()
            self._unsub_time_listener = None
        if self._unsub_snooze:
            self._unsub_snooze()
            self._unsub_snooze = None
        if self._unsub_autostop:
            self._unsub_autostop()
            self._unsub_autostop = None

    def add_listener(self, cb: Callable[[], None]) -> Callable[[], None]:
        """Register a callback invoked when next_fire or state changes."""
        self._listeners.append(cb)

        def _unsub() -> None:
            if cb in self._listeners:
                self._listeners.remove(cb)

        return _unsub

    def set_event_callback(self, cb: Callable[[str, dict], None]) -> None:
        self._event_callback = cb

    def clear_event_callback(self) -> None:
        self._event_callback = None

    def _notify(self) -> None:
        for cb in list(self._listeners):
            try:
                cb()
            except Exception:  # pragma: no cover
                _LOGGER.exception("[%s] Listener raised", self.entry.title)

    # ------------------------------------------------------------------
    # Config helpers
    # ------------------------------------------------------------------

    @property
    def _options(self) -> dict[str, Any]:
        # Options override data; both supported because config_flow may write either.
        merged = dict(self.entry.data)
        merged.update(self.entry.options)
        return merged

    @property
    def target(self) -> str:
        return self._options.get(CONF_TARGET, "")

    @property
    def alarm_time(self) -> time:
        return _parse_time(self._options.get(CONF_TIME, DEFAULT_TIME))

    @property
    def days(self) -> list[str]:
        return list(self._options.get(CONF_DAYS) or DEFAULT_DAYS)

    @property
    def volume(self) -> float:
        try:
            return float(self._options.get(CONF_VOLUME, DEFAULT_VOLUME))
        except (TypeError, ValueError):
            return DEFAULT_VOLUME

    @property
    def snooze_minutes(self) -> int:
        try:
            return int(self._options.get(CONF_SNOOZE_MINUTES, DEFAULT_SNOOZE_MINUTES))
        except (TypeError, ValueError):
            return DEFAULT_SNOOZE_MINUTES

    @property
    def stop_after_minutes(self) -> int:
        try:
            return int(self._options.get(CONF_STOP_AFTER_MINUTES, DEFAULT_STOP_AFTER_MINUTES))
        except (TypeError, ValueError):
            return DEFAULT_STOP_AFTER_MINUTES

    @property
    def library(self) -> list[dict[str, str]]:
        lib = self._options.get(CONF_LIBRARY) or []
        if not isinstance(lib, list):
            return []
        return [i for i in lib if isinstance(i, dict) and i.get("url")]

    @property
    def enabled(self) -> bool:
        return self._enabled

    @property
    def next_fire(self) -> datetime | None:
        return self._next_fire

    @property
    def is_dismissed_today(self) -> bool:
        return self._state.dismissed_date == dt_util.now().date()

    # ------------------------------------------------------------------
    # Public actions
    # ------------------------------------------------------------------

    async def async_set_enabled(self, enabled: bool) -> None:
        self._enabled = bool(enabled)
        self._refresh_next_fire()

    async def async_handle_options_updated(self) -> None:
        """Called on options/data change — re-arm scheduler from scratch."""
        self._arm_time_listener()
        self._refresh_next_fire()

    async def async_fire_now(self) -> None:
        """Manually fire the alarm immediately (used by service and snooze re-fire)."""
        await self._do_fire()

    async def async_stop_playback(self) -> None:
        """Stop ongoing playback on the target media player and cancel auto-stop."""
        if self._unsub_autostop:
            self._unsub_autostop()
            self._unsub_autostop = None
        if not self.target:
            return
        try:
            await self.hass.services.async_call(
                "media_player",
                "media_stop",
                {"entity_id": self.target},
                blocking=False,
            )
        except Exception:
            _LOGGER.exception("[%s] media_stop failed", self.entry.title)
        self._is_firing = False
        self._notify()

    async def async_snooze(self, minutes: int | None = None) -> None:
        """Stop current playback and re-fire after `minutes` (default snooze_minutes)."""
        delay_minutes = minutes if minutes and minutes > 0 else self.snooze_minutes
        if self._unsub_snooze:
            self._unsub_snooze()
            self._unsub_snooze = None
        await self.async_stop_playback()
        snooze_until = dt_util.utcnow() + timedelta(minutes=delay_minutes)
        self._state.snooze_until = snooze_until
        await self._store.async_save(self._state)
        _LOGGER.info("[%s] Snoozed for %d min (until %s)", self.entry.title, delay_minutes, snooze_until)
        self._unsub_snooze = async_call_later(self.hass, delay_minutes * 60, self._snooze_fire)
        self._refresh_next_fire()

    async def async_dismiss(self) -> None:
        """Stop and suppress further fires until next day."""
        if self._unsub_snooze:
            self._unsub_snooze()
            self._unsub_snooze = None
        await self.async_stop_playback()
        self._state.snooze_until = None
        self._state.dismissed_date = dt_util.now().date()
        await self._store.async_save(self._state)
        _LOGGER.info("[%s] Dismissed for the rest of %s", self.entry.title, self._state.dismissed_date)
        self._refresh_next_fire()

    # ------------------------------------------------------------------
    # Scheduling internals
    # ------------------------------------------------------------------

    def _arm_time_listener(self) -> None:
        if self._unsub_time_listener:
            self._unsub_time_listener()
            self._unsub_time_listener = None
        t = self.alarm_time
        self._unsub_time_listener = async_track_time_change(
            self.hass, self._on_clock_tick, hour=t.hour, minute=t.minute, second=t.second
        )

    @callback
    def _on_clock_tick(self, now: datetime) -> None:
        if not self._enabled:
            return
        weekday = DAY_CODES[dt_util.as_local(now).weekday()]
        if weekday not in self.days:
            return
        if self.is_dismissed_today:
            _LOGGER.debug("[%s] Skipping fire — dismissed for today", self.entry.title)
            return
        # If snooze is pending, the snooze callback will handle the fire.
        if self._state.snooze_until and self._state.snooze_until > dt_util.utcnow():
            _LOGGER.debug("[%s] Skipping scheduled fire — snooze pending", self.entry.title)
            return
        self.hass.async_create_task(self._do_fire())

    async def _snooze_fire(self, _now: Any = None) -> None:
        self._unsub_snooze = None
        # Clear persisted snooze before firing so a crash doesn't loop us.
        self._state.snooze_until = None
        await self._store.async_save(self._state)
        await self._do_fire()

    async def _do_fire(self) -> None:
        if not self.target:
            _LOGGER.warning("[%s] No target media_player configured; cannot fire", self.entry.title)
            return
        if not self.library:
            _LOGGER.warning("[%s] Library is empty; nothing to play", self.entry.title)
            return
        item = random.choice(self.library)
        url = item.get("url", "")
        label = item.get("label") or url
        _LOGGER.info("[%s] Firing → %s : %s", self.entry.title, label, url)
        try:
            media_content_id = url
            if is_youtube_url(url):
                media_content_id = await extract_audio_url(self.hass, url)
        except Exception:
            _LOGGER.exception("[%s] Failed to extract media URL for %s", self.entry.title, url)
            return
        try:
            # Clear any existing media session before casting; without this,
            # Chromecasts with a stale app (e.g. Music Assistant) silently
            # reject the new stream.
            await self.hass.services.async_call(
                "media_player",
                "media_stop",
                {"entity_id": self.target},
                blocking=True,
            )
            await asyncio.sleep(1)
            # Mute before casting to suppress the Chromecast connection chime,
            # then restore the desired volume after playback starts.
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {"entity_id": self.target, "volume_level": 0.0},
                blocking=True,
            )
            await self.hass.services.async_call(
                "media_player",
                "play_media",
                {
                    "entity_id": self.target,
                    "media_content_id": media_content_id,
                    "media_content_type": "music",
                },
                blocking=False,
            )
            await asyncio.sleep(3)
            await self.hass.services.async_call(
                "media_player",
                "volume_set",
                {"entity_id": self.target, "volume_level": self.volume},
                blocking=True,
            )
        except Exception:
            _LOGGER.exception("[%s] play_media failed", self.entry.title)
            return
        self._is_firing = True
        if self._event_callback:
            self._event_callback("alarm_fired", {"label": label, "url": url, "target": self.target})
        # Arm auto-stop
        if self._unsub_autostop:
            self._unsub_autostop()
        self._unsub_autostop = async_call_later(
            self.hass, self.stop_after_minutes * 60, self._auto_stop
        )
        self._refresh_next_fire()

    async def _auto_stop(self, _now: Any = None) -> None:
        self._unsub_autostop = None
        _LOGGER.debug("[%s] Auto-stop after %d min", self.entry.title, self.stop_after_minutes)
        await self.async_stop_playback()

    def _refresh_next_fire(self) -> None:
        self._next_fire = self._compute_next_fire()
        self._notify()

    def _compute_next_fire(self) -> datetime | None:
        if not self._enabled:
            return None
        if self._state.snooze_until and self._state.snooze_until > dt_util.utcnow():
            return self._state.snooze_until
        days_set = set(self.days)
        if not days_set:
            return None
        now_local = dt_util.now()
        alarm_t = self.alarm_time
        today = now_local.date()
        for delta in range(0, 14):
            candidate_date: date = today + timedelta(days=delta)
            weekday_code = DAY_CODES[candidate_date.weekday()]
            if weekday_code not in days_set:
                continue
            candidate_local = dt_util.start_of_local_day(candidate_date).replace(
                hour=alarm_t.hour, minute=alarm_t.minute, second=alarm_t.second, microsecond=0
            )
            if delta == 0:
                # Skip today if time has passed or dismissed.
                if candidate_local <= now_local:
                    continue
                if self.is_dismissed_today:
                    continue
            return dt_util.as_utc(candidate_local)
        return None
