"""Constants for the Chromecast Alarm integration."""
from __future__ import annotations

DOMAIN = "chromecast_alarm"

PLATFORMS = ["switch", "button", "sensor"]

# Config / options keys
CONF_TARGET = "target_media_player"
CONF_TIME = "time"
CONF_DAYS = "days"
CONF_VOLUME = "volume"
CONF_SNOOZE_MINUTES = "snooze_minutes"
CONF_STOP_AFTER_MINUTES = "stop_after_minutes"
CONF_LIBRARY = "library"

# Defaults
DEFAULT_TIME = "07:00:00"
DEFAULT_DAYS = ["mon", "tue", "wed", "thu", "fri"]
DEFAULT_VOLUME = 0.4
DEFAULT_SNOOZE_MINUTES = 9
DEFAULT_STOP_AFTER_MINUTES = 30

# Day codes (matches Python's calendar / weekday names lowercased)
DAY_CODES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]

# Storage keys
STORAGE_VERSION = 1
STORAGE_KEY_TEMPLATE = f"{DOMAIN}_state_{{entry_id}}"

# Service names
SERVICE_FIRE = "fire"
SERVICE_STOP = "stop"
SERVICE_SNOOZE = "snooze"

# Hass data key for shared runner registry
DATA_RUNNERS = "runners"
