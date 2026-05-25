"""Constants for the Chromecast Alarm integration."""
from __future__ import annotations

DOMAIN = "chromecast_alarm"

PLATFORMS = ["switch", "button", "sensor", "event"]

# Config / options keys
CONF_TARGET = "target_media_player"
CONF_TIME = "time"
CONF_DAYS = "days"
CONF_VOLUME = "volume"
CONF_SNOOZE_MINUTES = "snooze_minutes"
CONF_STOP_AFTER_MINUTES = "stop_after_minutes"
CONF_LIBRARY = "library"
CONF_SKIP_HOLIDAYS = "skip_holidays"
CONF_HOLIDAY_COUNTRY = "holiday_country"

# Defaults
DEFAULT_TIME = "07:00:00"
DEFAULT_DAYS = ["mon", "tue", "wed", "thu", "fri"]
DEFAULT_VOLUME = 0.4
DEFAULT_SNOOZE_MINUTES = 9
DEFAULT_STOP_AFTER_MINUTES = 30
DEFAULT_SKIP_HOLIDAYS = False
DEFAULT_HOLIDAY_COUNTRY = "NO"

# Day codes (matches Python's calendar / weekday names lowercased)
DAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Storage keys
STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = f"{DOMAIN}_state_{{entry_id}}"

# Service names
SERVICE_FIRE = "fire"
SERVICE_STOP = "stop"
SERVICE_SNOOZE = "snooze"
SERVICE_SET_TIME = "set_time"
SERVICE_SET_DAYS = "set_days"

# Hass data key for shared runner registry
DATA_RUNNERS = "runners"
