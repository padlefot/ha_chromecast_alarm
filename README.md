# Chromecast Alarm

A Home Assistant custom integration that acts as a wake-up alarm clock — casting a randomly chosen item from a per-alarm media library to a target Chromecast (or any `media_player`) at a configured time, with snooze, dismiss, and public holiday support.

YouTube URLs are played via on-the-fly audio extraction with `yt-dlp` (bundled as a Python requirement). Local media-source paths work too.

## Features

- One config entry per alarm — create as many as you need
- Built-in scheduler with weekday selection — no automations to wire
- Random pick from a per-alarm library on each fire
- YouTube URL playback via `yt-dlp` extraction
- Snooze (re-fire after N minutes) and dismiss (skip until tomorrow)
- Skip public holidays — configurable country (100+ supported via `holidays` library)
- Event entity for automation triggers (e.g. actionable notifications)
- State survives Home Assistant restarts (snooze and dismiss are persisted)
- Auto-stop after a configurable safety duration
- Switch entity exposes alarm attributes for dashboard cards

## Dashboard card

A companion Mushroom-style Lovelace card is available: [Chromecast Alarm Card](https://github.com/padlefot/ha_chromecast_alarm_card)

Install via HACS (Frontend → Custom repositories), then add to your dashboard:

```yaml
type: custom:chromecast-alarm-card
entity: switch.morning_alarm
```

## Entities per alarm

| Entity | Purpose |
|---|---|
| `switch.<slug>` | Master enable/disable (also exposes alarm config as attributes) |
| `button.<slug>_snooze` | Pause current alarm, re-fire after `snooze_minutes` |
| `button.<slug>_dismiss` | Stop and suppress further fires until tomorrow |
| `sensor.<slug>_next_fire` | Timestamp of the next scheduled fire |
| `event.<slug>_event` | Fires `alarm_fired` event for automation triggers |

### Switch attributes

The switch entity exposes these attributes for use in templates and dashboard cards:

`alarm_time`, `days`, `volume`, `next_fire`, `is_dismissed_today`, `snooze_minutes`, `stop_after_minutes`, `skip_holidays`, `holiday_country`, `target`, `library_count`

## Services

| Service | Fields | Purpose |
|---|---|---|
| `chromecast_alarm.fire` | `entity_id` | Manually fire an alarm (good for testing) |
| `chromecast_alarm.stop` | `entity_id` | Stop ongoing playback |
| `chromecast_alarm.snooze` | `entity_id`, `minutes?` | Snooze the alarm (override duration optional) |
| `chromecast_alarm.set_time` | `entity_id`, `time` | Change alarm time (HH:MM format) |
| `chromecast_alarm.set_days` | `entity_id`, `days` | Change active weekdays |
| `chromecast_alarm.set_volume` | `entity_id`, `volume` | Change alarm volume (0.0–1.0) |
| `chromecast_alarm.set_target` | `entity_id`, `target` | Change target media player |

## Installation

1. In HACS → Custom repositories, add `https://github.com/padlefot/ha_chromecast_alarm` with category **Integration**.
2. Search for **Chromecast Alarm** and install.
3. Restart Home Assistant.
4. Settings → Devices & Services → **+ Add Integration** → search **Chromecast Alarm**.

## Configuration

When adding an alarm, you'll be asked for:

- **Name** — display name (slugified into entity IDs).
- **Target media player** — a Chromecast or any `media_player`.
- **Time** — wall-clock time (HH:MM).
- **Days** — list of weekdays.
- **Skip public holidays** — toggle (default off). When enabled, the alarm won't fire on public holidays.
- **Holiday country** — which country's holidays to use (default Norway). Supports 100+ countries.
- **Volume** — 0.0–1.0; set before each fire.
- **Snooze minutes** — default re-fire delay (default 9).
- **Stop after minutes** — auto-stop safety (default 30).
- **Library** — one item per line, format `label|url`. URL can be:
  - A YouTube URL (`https://www.youtube.com/...`) — extracted via `yt-dlp`.
  - A media-source path (`media-source://...`).
  - Any URL the target `media_player` understands.

## Library example

```
BirdsAndPiano|https://www.youtube.com/watch?v=LcOn6z-cf8Y
Gentle bells|media-source://media_source/local/bells.mp3
Morning radio|http://stream.example.com/radio.mp3
```

## Changelog

- **v0.3.5** — Retry next track when a video fails (e.g. taken down); persistent notification if all tracks fail
- **v0.3.4** — Add `set_volume` and `set_target` services for dashboard card control
- **v0.3.2** — Add `set_time` and `set_days` services for dashboard card control
- **v0.3.1** — Expose alarm config as switch entity attributes for dashboard card support
- **v0.3.0** — Skip public holidays with configurable country (100+ supported)
- **v0.2.5** — Clear dismissed state on options change; fix re-schedule after time edit
- **v0.2.4** — Revert chime suppression; simplify fire sequence
- **v0.2.0** — Event entity for automation triggers; fix stale Chromecast stream bug

## License

MIT
