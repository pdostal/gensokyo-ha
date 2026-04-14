/**
 * Gensokyo Radio Lovelace Card
 *
 * Compact card showing the currently playing track with album art,
 * animated progress bar, rating, and listener count.
 * Click anywhere on the card to open the song detail page.
 *
 * Usage:
 *   type: custom:gensokyo-radio-card
 *   entity: media_player.gensokyo_radio
 */

class GensokyoRadioCard extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._progressTimer = null;
    this._positionBase = null;
    this._positionBaseTime = null;
    this._duration = null;
    this._lastSongId = null;
  }

  // ------------------------------------------------------------------ //
  // Lovelace card API
  // ------------------------------------------------------------------ //

  setConfig(config) {
    if (!config.entity) {
      throw new Error("Please define an entity (e.g. media_player.gensokyo_radio)");
    }
    this._config = config;
  }

  set hass(hass) {
    this._hass = hass;
    const state = hass.states[this._config.entity];

    if (!state) {
      this._renderUnavailable();
      return;
    }

    const songId = state.attributes.song_id;
    if (songId !== this._lastSongId) {
      this._lastSongId = songId;
      this._render(state);
    }

    this._syncPosition(state.attributes);
  }

  getCardSize() {
    return 2;
  }

  disconnectedCallback() {
    this._stopProgressTimer();
  }

  // ------------------------------------------------------------------ //
  // Rendering
  // ------------------------------------------------------------------ //

  _render(state) {
    const attrs = state.attributes;
    const title    = attrs.media_title    || "Unknown Track";
    const artist   = attrs.media_artist   || "";
    const album    = attrs.media_album_name  || "";
    const circle   = attrs.media_album_artist || "";
    const year     = attrs.year           || "";
    const rating   = attrs.rating         || "";
    const timesRated = attrs.times_rated  || 0;
    const listeners  = attrs.listeners    || 0;
    const albumArt   = attrs.entity_picture || "";
    const songUrl    = attrs.song_url     || "https://gensokyoradio.net/";

    this.shadowRoot.innerHTML = `
      <style>
        :host {
          display: block;
          --card-bg:        var(--ha-card-background, #1c1c2e);
          --accent:         var(--primary-color, #b39ddb);
          --text-primary:   var(--primary-text-color, #e8e8f0);
          --text-secondary: var(--secondary-text-color, #9a9ab0);
          --progress-bg:    rgba(255,255,255,0.1);
          --progress-fill:  var(--accent);
          font-family: var(--paper-font-body1_-_font-family, sans-serif);
        }

        .card {
          background: var(--card-bg);
          border-radius: var(--ha-card-border-radius, 12px);
          overflow: hidden;
          box-shadow: var(--ha-card-box-shadow, 0 2px 12px rgba(0,0,0,0.4));
          color: var(--text-primary);
          cursor: pointer;
          user-select: none;
          transition: filter 0.15s;
        }
        .card:hover { filter: brightness(1.08); }
        .card:active { filter: brightness(0.92); }

        .body {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 10px 12px;
        }

        .art {
          flex-shrink: 0;
          width: 72px;
          height: 72px;
          border-radius: 6px;
          overflow: hidden;
          background: #0d0d1a;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 28px;
        }

        .art img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .info {
          flex: 1;
          min-width: 0;
        }

        .title {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-primary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 2px;
        }

        .artist {
          font-size: 12px;
          color: var(--accent);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
          margin-bottom: 2px;
        }

        .sub {
          font-size: 11px;
          color: var(--text-secondary);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }

        .right {
          flex-shrink: 0;
          text-align: right;
          font-size: 11px;
          color: var(--text-secondary);
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          gap: 4px;
        }

        .stars { color: #f0c040; letter-spacing: 0.5px; font-size: 12px; }

        .listeners {
          display: flex;
          align-items: center;
          gap: 3px;
        }
        .listeners::before { content: "👥"; font-size: 10px; }

        .progress-bar {
          height: 3px;
          background: var(--progress-bg);
          border-radius: 0 0 12px 12px;
          overflow: hidden;
        }

        .progress-fill {
          height: 100%;
          background: var(--progress-fill);
          transition: width 1s linear;
          width: 0%;
        }
      </style>

      <ha-card class="card" role="link" title="Open song detail on Gensokyo Radio">
        <div class="body">
          <div class="art">
            ${albumArt
              ? `<img src="${this._escapeHtml(albumArt)}" alt="Album art" onerror="this.style.display='none'">`
              : "🎵"
            }
          </div>

          <div class="info">
            <div class="title" title="${this._escapeHtml(title)}">${this._escapeHtml(title)}</div>
            <div class="artist">${this._escapeHtml(artist)}</div>
            <div class="sub">${this._escapeHtml(album)}${circle && circle !== artist ? ` · ${this._escapeHtml(circle)}` : ""}${year ? ` (${this._escapeHtml(year)})` : ""}</div>
          </div>

          <div class="right">
            <div class="stars">${this._ratingToStars(rating)}</div>
            <div class="sub">${rating}</div>
            <div class="listeners">${listeners}</div>
          </div>
        </div>

        <div class="progress-bar">
          <div class="progress-fill" id="gr-progress"></div>
        </div>
      </ha-card>
    `;

    this.shadowRoot.querySelector(".card").addEventListener("click", () => {
      window.open(songUrl, "_blank", "noopener,noreferrer");
    });

    this._syncPosition(state.attributes);
    this._startProgressTimer();
  }

  _renderUnavailable() {
    this.shadowRoot.innerHTML = `
      <ha-card>
        <div style="padding:12px;text-align:center;font-size:13px;color:var(--secondary-text-color,#9a9ab0);">
          Gensokyo Radio unavailable
        </div>
      </ha-card>
    `;
  }

  // ------------------------------------------------------------------ //
  // Progress bar
  // ------------------------------------------------------------------ //

  _syncPosition(attrs) {
    const position  = attrs.media_position;
    const updatedAt = attrs.media_position_updated_at;
    const duration  = attrs.media_duration;
    if (position == null || duration == null) return;
    this._positionBase     = parseFloat(position);
    this._positionBaseTime = updatedAt ? new Date(updatedAt).getTime() : Date.now();
    this._duration         = parseFloat(duration);
    this._updateProgressDOM();
  }

  _startProgressTimer() {
    this._stopProgressTimer();
    this._progressTimer = setInterval(() => this._updateProgressDOM(), 1000);
  }

  _stopProgressTimer() {
    if (this._progressTimer !== null) {
      clearInterval(this._progressTimer);
      this._progressTimer = null;
    }
  }

  _updateProgressDOM() {
    if (this._positionBase == null || this._duration == null) return;
    const elapsed = this._positionBase + (Date.now() - this._positionBaseTime) / 1000;
    const clamped = Math.min(Math.max(elapsed, 0), this._duration);
    const pct     = (clamped / this._duration) * 100;
    const fill    = this.shadowRoot.getElementById("gr-progress");
    if (fill) fill.style.width = `${pct.toFixed(1)}%`;
  }

  // ------------------------------------------------------------------ //
  // Utilities
  // ------------------------------------------------------------------ //

  _ratingToStars(ratingStr) {
    if (!ratingStr) return "";
    const num = parseFloat(ratingStr);
    if (isNaN(num)) return "";
    const full = Math.round(num);
    return "★".repeat(full) + "☆".repeat(Math.max(0, 5 - full));
  }

  _escapeHtml(str) {
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }
}

customElements.define("gensokyo-radio-card", GensokyoRadioCard);

window.customCards = window.customCards || [];
window.customCards.push({
  type: "gensokyo-radio-card",
  name: "Gensokyo Radio Card",
  description: "Compact card showing the currently playing track on Gensokyo Radio. Click to open song details.",
  preview: true,
  documentationURL: "https://github.com/pdostal/gensokyo-ha",
});
