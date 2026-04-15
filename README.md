# Gensokyo Radio — Home Assistant Integration

A HACS-compatible Home Assistant integration for [Gensokyo Radio](https://gensokyoradio.net/), the Touhou music internet radio station.

Tracks the currently playing song and exposes it as a `media_player` entity. Includes a Lovelace card with album art, animated progress bar, rating, listener count, and optional play/stop controls for a linked speaker.

**Smart polling**: the integration only hits the API once per song — it reads `SONGTIMES.REMAINING` from each response and schedules the next fetch for exactly that many seconds later (+ 2 seconds buffer). No wasted requests.

---

## Features

- `media_player` entity with title, artist, album, circle, duration, and position
- Album art served directly from Gensokyo Radio's CDN
- Extra attributes: rating, times rated, year, song ID, album ID, listener count, stream URL, song URL
- Custom Lovelace card — hero album art layout, animated progress bar, elapsed/duration time, star rating
- Optional play/stop controls on the card for a linked speaker
- Song changes logged in the HA activity log
- Smart per-song polling — zero unnecessary API calls
- HACS-compatible (integration + dashboard card from the same repo)

---

## Installation

### Step 1 — Integration (Python backend)

1. Open HACS → **Integrations** → ⋮ → **Custom repositories**
2. Add `https://github.com/pdostal/gensokyo-ha` with category **Integration**
3. Install **Gensokyo Radio** and restart Home Assistant

### Step 2 — Dashboard card (Lovelace frontend)

The card is a separate HACS package at **[pdostal/gensokyo-ha-card](https://github.com/pdostal/gensokyo-ha-card)**.

1. Open HACS → **Frontend** → ⋮ → **Custom repositories**
2. Add `https://github.com/pdostal/gensokyo-ha-card` with category **Dashboard**
3. Install **Gensokyo Radio Card** — no restart needed

### Manual installation (no HACS)

1. Copy `custom_components/gensokyo_radio/` into your HA `config/custom_components/` directory
2. Download `gensokyo-radio-card.js` from [gensokyo-ha-card releases](https://github.com/pdostal/gensokyo-ha-card/releases) into your HA `config/www/` directory
3. Add the resource in **Settings → Dashboards → Resources**:
   - URL: `/local/gensokyo-radio-card.js`
   - Type: **JavaScript module**
4. Restart Home Assistant

---

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Gensokyo Radio**
3. Click through — no configuration required

A `media_player.gensokyo_radio` entity will appear immediately.

---

## Lovelace Card

After installing the dashboard card via HACS, add it to any dashboard from **Edit → Add card** — search for *Gensokyo Radio* — or add it manually in YAML:

```yaml
type: custom:gensokyo-radio-card
entity: media_player.gensokyo_radio
```

The card shows album art, track info, star rating, listener count, and an animated progress bar with elapsed/duration times.

### Optional: linked speaker controls

Set a `target_player` attribute on the entity (requires custom options flow — coming soon) to display Play/Stop buttons that control a real speaker in your home.

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
| `rating` | Community rating (e.g. `4.36`) |
| `times_rated` | Number of ratings |
| `year` | Release year |
| `song_id` | Gensokyo Radio song ID |
| `album_id` | Gensokyo Radio album ID |
| `listeners` | Current listener count |
| `stream_url` | Audio stream URL |
| `song_url` | Link to song detail page on gensokyoradio.net |
| `circle_link` | Link to circle/label page on gensokyoradio.net |

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
