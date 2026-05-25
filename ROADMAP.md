# Chromecast Alarm — Roadmap

## Planned

### Norwegian red day support
Skip alarm on Norwegian public holidays ("rode dager"). When the alarm is scheduled to fire on a red day, treat it the same as an unchecked weekday — don't fire.

**Scope:**
- Map all fixed Norwegian public holidays (1. jan, 1. mai, 17. mai, 25. des, 26. des)
- Map movable holidays derived from Easter (Skjaertorsdag, Langfredag, 1. pinsedag, 2. pinsedag, Kr. himmelfartsdag, 2. paaskedag)
- Add a per-alarm toggle: "Skip red days" (default on)
- Compute Easter date via algorithm (no external API dependency)
- Check red day list in `_on_clock_tick` before firing
- Show next red day skip in `sensor.next_fire` (jump to next valid day)

### Dashboard alarm card
A Lovelace card per alarm showing status and controls at a glance.

**Scope:**
- Show alarm name, time, enabled state, and next fire
- Toggle enable/disable directly from the card
- Set/change alarm time inline (time picker)
- Snooze and dismiss buttons
- Show which days are active
- Visual indicator when alarm is currently firing
- Ideally a custom card via HACS frontend, or a well-structured markdown/entities card template

## Done (v0.2.x)

- Random media pick from per-alarm library
- YouTube URL playback via yt-dlp extraction
- Snooze / dismiss button entities
- Persisted state across HA restarts
- Auto-stop safety timer
- Event entity for automation triggers (alarm_fired)
- Stale Chromecast session fix (media_stop before play_media)
- Clear dismissed state on options change
