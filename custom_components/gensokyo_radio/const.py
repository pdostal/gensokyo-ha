"""Constants for the Gensokyo Radio integration."""

DOMAIN = "gensokyo_radio"
PLATFORMS = ["media_player"]

API_URL = "https://gensokyoradio.net/api/station/playing/"
ALBUM_ART_BASE_URL = "https://gensokyoradio.net/images/albums/500/"
SONG_DETAIL_BASE_URL = "https://gensokyoradio.net/music/show/"
DEFAULT_STREAM_URL = "https://stream.gensokyoradio.net/1/"

# Seconds added to SONGTIMES.REMAINING before next poll
UPDATE_DELAY_AFTER_SONG = 2

# Retry delay on API error (seconds)
ERROR_RETRY_DELAY = 30

# Request timeout (seconds)
REQUEST_TIMEOUT = 10
