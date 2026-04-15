# Gensokyo Radio — Home Assistant Integration

A HACS-compatible Home Assistant integration for [Gensokyo Radio](https://gensokyoradio.net/), the Touhou music internet radio station.

Exposes the currently playing track as a `media_player` entity. For a dashboard card, see **[pdostal/gensokyo-ha-card](https://github.com/pdostal/gensokyo-ha-card)**.

**Smart polling**: reads `SONGTIMES.REMAINING` from each API response and schedules the next fetch for exactly that many seconds later — one API call per song, no wasted requests.

---

## Features

- `media_player` entity with title, artist, album, circle, duration, and live position
- Album art from Gensokyo Radio's CDN
- Extra state attributes: rating, times rated, year, song ID, album ID, listener count, stream URL, song URL, circle link
- Song changes logged in the HA activity log
- Smart per-song polling — zero unnecessary API calls

---

## Installation

### Via HACS (recommended)

1. Open **HACS → Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/pdostal/gensokyo-ha` with category **Integration**
3. Install **Gensokyo Radio** and restart Home Assistant

### Manual

1. Copy `custom_components/gensokyo_radio/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Gensokyo Radio** and click through — no configuration required

A `media_player.gensokyo_radio` entity appears immediately.

---

## Dashboard Card

Install the companion card from **[pdostal/gensokyo-ha-card](https://github.com/pdostal/gensokyo-ha-card)** to display the currently playing track on your dashboard.

---

## Entity Attributes

| Attribute | Description |
|---|---|
| `media_title` | Track title |
| `media_artist` | Artist name |
| `media_album_name` | Album name |
| `media_album_artist` | Doujin circle / label |
| `media_duration` | Track duration in seconds |
| `media_position` | Elapsed time in seconds |
| `entity_picture` | Album art URL |
| `rating` | Community rating (0–5) |
| `times_rated` | Number of community ratings |
| `year` | Release year |
| `song_id` | Gensokyo Radio song ID |
| `album_id` | Gensokyo Radio album ID |
| `listeners` | Current stream listener count |
| `stream_url` | Audio stream URL |
| `song_url` | Song detail page on gensokyoradio.net |
| `circle_link` | Circle / label page on gensokyoradio.net |

---

## Development

```bash
pip install -r requirements_test.txt
pytest tests/ -v
```

## License

MIT
