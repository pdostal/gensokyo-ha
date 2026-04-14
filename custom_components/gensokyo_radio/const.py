"""Constants for the Gensokyo Radio integration."""

DOMAIN = "gensokyo_radio"
PLATFORMS = ["media_player"]

API_URL = "https://gensokyoradio.net/api/station/playing/"
ALBUM_ART_BASE_URL = "https://gensokyoradio.net/images/albums/500/"

# Seconds added to SONGTIMES.REMAINING before next poll
UPDATE_DELAY_AFTER_SONG = 2

# Retry delay on API error (seconds)
ERROR_RETRY_DELAY = 30

# Request timeout (seconds)
REQUEST_TIMEOUT = 10

# Config entry keys
CONF_TARGET_PLAYER = "target_player"
CONF_STREAM_QUALITY = "stream_quality"
DEFAULT_STREAM_QUALITY = "1"

# Service names
SERVICE_PLAY = "play"
SERVICE_STOP = "stop"

# Stream URLs keyed by Gensokyo Radio stream number
STREAM_URLS: dict[str, str] = {
    "1": "https://stream.gensokyoradio.net/1/",   # 128 kbps
    "2": "https://stream.gensokyoradio.net/2/",   # 64 kbps
    "3": "https://stream.gensokyoradio.net/3/",   # 256 kbps
    "4": "https://stream.gensokyoradio.net/4/",   # 1000 kbps / lossless
}
