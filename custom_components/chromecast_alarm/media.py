"""Media helpers: YouTube detection and audio-URL extraction via yt-dlp."""
from __future__ import annotations

import logging
from urllib.parse import urlparse

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

_YOUTUBE_HOSTS = {
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
    "music.youtube.com",
    "youtu.be",
}


def is_youtube_url(url: str) -> bool:
    """Return True if the URL looks like a YouTube link."""
    if not url:
        return False
    try:
        host = (urlparse(url).hostname or "").lower()
    except ValueError:
        return False
    return host in _YOUTUBE_HOSTS


def _extract_blocking(url: str) -> str:
    """Blocking yt-dlp extraction; called via executor."""
    # Lazy import: yt-dlp is heavy and only needed for YouTube URLs.
    from yt_dlp import YoutubeDL  # type: ignore

    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "format": "bestaudio/best",
        "noplaylist": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if not info:
            raise RuntimeError("yt-dlp returned no info")
        # Prefer the top-level URL if present (already format-selected).
        if "url" in info and info["url"]:
            return info["url"]
        # Fallback: scan formats for the best audio.
        formats = info.get("formats") or []
        audio_only = [
            f
            for f in formats
            if f.get("acodec") and f["acodec"] != "none" and (f.get("vcodec") == "none" or not f.get("vcodec"))
        ]
        chosen = audio_only or formats
        if not chosen:
            raise RuntimeError("No suitable audio stream found")
        chosen.sort(key=lambda f: f.get("abr") or 0, reverse=True)
        if not chosen[0].get("url"):
            raise RuntimeError("Selected format has no URL")
        return chosen[0]["url"]


async def extract_audio_url(hass: HomeAssistant, url: str) -> str:
    """Resolve a YouTube URL to a direct audio stream URL."""
    _LOGGER.debug("Extracting audio stream URL for %s", url)
    stream_url: str = await hass.async_add_executor_job(_extract_blocking, url)
    _LOGGER.debug("Extracted stream URL for %s (length=%d)", url, len(stream_url))
    return stream_url


def parse_library_text(text: str) -> list[dict[str, str]]:
    """Parse the textarea-format library into a list of {label, url} dicts.

    Each non-empty line: ``label|url`` (label may contain spaces; whitespace stripped).
    Lines starting with ``#`` are treated as comments.
    """
    items: list[dict[str, str]] = []
    for raw_line in (text or "").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "|" not in line:
            # Tolerate URL-only lines; label defaults to URL.
            items.append({"label": line, "url": line})
            continue
        label, _, url = line.partition("|")
        label = label.strip()
        url = url.strip()
        if not url:
            continue
        items.append({"label": label or url, "url": url})
    return items


def library_to_text(library: list[dict[str, str]] | None) -> str:
    """Render a library list back into the textarea format for editing."""
    if not library:
        return ""
    lines = []
    for item in library:
        label = (item.get("label") or "").strip()
        url = (item.get("url") or "").strip()
        if not url:
            continue
        if label and label != url:
            lines.append(f"{label}|{url}")
        else:
            lines.append(url)
    return "\n".join(lines)
