# Chromecast Alarm

A personal Home Assistant custom integration that acts as a wake-up alarm clock — casting a randomly chosen item from a per-alarm media library to a target Chromecast (or any `media_player`) at a configured time, with snooze and dismiss support.

YouTube URLs are played via on-the-fly audio extraction with `yt-dlp` (bundled as a Python requirement). Local media-source paths work too.

## Features

- One config entry per alarm (mirrors how Adaptive Lighting models rooms)
- Built-in scheduler with weekday selection — no automations to wire
- Random pick from a per-alarm library on each fire
- YouTube URL playback via `yt-dlp` extraction
- Snooze (re-fire after N minutes) and dismiss (skip until tomorrow), as proper button entities
- State survives Home Assistant restarts (snooze and dismiss are persisted)
- Auto-stop after a configurable safety duration

## Entities per alarm

| Entity | Purpose |
|---|---|
| `switch.<slug>` | Master enable/disable |
| `button.<slug>_snooze` | Pause current alarm, re-fire after `snooze_minutes` |
| `button.<slug>_dismiss` | Stop and suppress further fires until tomorrow |
| `sensor.<slug>_next_fire` | Timestamp of the next scheduled fire |

## Services

| Service | Fields | Purpose |
|---|---|---|
| `chromecast_alarm.fire` | `entity_id` | Manually fire an alarm (good for testing) |
| `chromecast_alarm.stop` | `entity_id` | Stop ongoing playback |
| `chromecast_alarm.snooze` | `entity_id`, `minutes?` | Snooze the alarm (override duration optional) |

## Installation

1. In HACS → Custom repositories, add `http://skyy:3001/padlefot/ha_chromecast_alarm` with category **Integration**.
2. Search for **Chromecast Alarm** and install.
3. Restart Home Assistant.
4. Settings → Devices & Services → **+ Add Integration** → search **Chromecast Alarm**.

## Configuration

When adding an alarm, you'll be asked for:

- **Name** — display name (slugified into entity IDs).
- **Target media player** — a Chromecast or any `media_player`.
- **Time** — wall-clock time (HH:MM).
- **Days** — list of weekdays.
- **Volume** — 0.0–1.0; set before each fire.
- **Snooze minutes** — default re-fire delay (default 9).
- **Stop after minutes** — auto-stop safety (default 30).
- **Library** — one item per line, format `label|url`. URL can be:
  - A YouTube URL (`https://www.youtube.com/...`) — extracted via `yt-dlp`.
  - A media-source path (`media-source://...`).
  - Any URL the target `media_player` understands.

## Library example

```
Rick Astley|https://www.youtube.com/watch?v=dQw4w9WgXcQ
Gentle bells|media-source://media_source/local/bells.mp3
Morning radio|http://stream.example.com/radio.mp3
```

## Status

v0.1 — initial release. See [the plan](https://example.invalid/plan) for the design.

## License

MIT
