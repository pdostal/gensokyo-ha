# Gensokyo Radio — Home Assistant Integration

A HACS-compatible Home Assistant integration for [Gensokyo Radio](https://gensokyoradio.net/), the Touhou music internet radio station.

Tracks the currently playing song and exposes it as a `media_player` entity. Includes a compact Lovelace card with album art, animated progress bar, rating, and listener count. **The card is bundled with the integration and loads automatically — no manual setup needed.**

**Smart polling**: the integration only hits the API once per song — it reads `SONGTIMES.REMAINING` from each response and schedules the next fetch for exactly that many seconds later (+ 2 seconds buffer). No wasted requests.

---

## Features

- `media_player` entity with title, artist, album, circle, duration, and position
- Album art served directly from Gensokyo Radio's CDN
- Extra attributes: rating, times rated, year, song ID, album ID, listener count, song URL
- Custom Lovelace card — compact layout, animated progress bar, star rating
- Click the card to open the song detail page on gensokyoradio.net
- Bundled card auto-loads on every HA page — no manual resource configuration
- Song changes logged in the HA activity log
- Smart per-song polling — zero unnecessary API calls
- HACS-importable

---

## Installation

### Via HACS (recommended)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/pdostal/gensokyo-ha` with category **Integration**
3. Install **Gensokyo Radio**
4. Restart Home Assistant

### Manual

1. Copy `custom_components/gensokyo_radio/` into your HA `config/custom_components/` directory
2. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Gensokyo Radio**
3. Click through — no configuration required

A `media_player.gensokyo_radio` entity will appear immediately.

---

## Lovelace Card

The card is bundled with the integration and loads automatically — no manual resource setup needed.

After restarting Home Assistant, add the card to any dashboard:

```yaml
type: custom:gensokyo-radio-card
entity: media_player.gensokyo_radio
```

Click anywhere on the card to open the song detail page on gensokyoradio.net.

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
| `rating` | Community rating (e.g. `4.36/5`) |
| `times_rated` | Number of ratings |
| `year` | Release year |
| `song_id` | Gensokyo Radio song ID |
| `album_id` | Gensokyo Radio album ID |
| `listeners` | Current listener count |
| `song_url` | Link to song detail page on gensokyoradio.net |

---

## Development

```bash
# Install test dependencies
pip install -r requirements_test.txt

# Run tests
pytest tests/ -v
```

## License

MIT
