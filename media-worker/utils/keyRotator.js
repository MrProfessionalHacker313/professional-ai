/**
 * Multi-Key Rotator
 * Rotates through comma-separated API keys.
 * Marks keys rate-limited/exhausted and auto-skips them.
 * Owner adds keys in .env — no code change needed.
 */

class KeyRotator {
  constructor(keys = [], rateLimitCooldownMs = 60_000) {
    this._keys = keys.filter(Boolean);
    this._cooldown = rateLimitCooldownMs;
    this._index = 0;
    this._status = new Map();
    for (const key of this._keys) {
      this._status.set(key, { rateLimitedUntil: 0, errorCount: 0, successCount: 0 });
    }
  }

  get size() {
    return this._keys.length;
  }

  get activeCount() {
    const now = Date.now();
    return this._keys.filter(k => {
      const s = this._status.get(k);
      return s.rateLimitedUntil <= now && s.errorCount < 5;
    }).length;
  }

  /** Get next usable key. Rotates automatically. */
  next() {
    if (this._keys.length === 0) return null;

    const now = Date.now();
    const attempts = this._keys.length;

    for (let i = 0; i < attempts; i++) {
      const idx = (this._index + i) % attempts;
      const key = this._keys[idx];
      const status = this._status.get(key);

      if (status.rateLimitedUntil > now) continue;
      if (status.errorCount >= 5) continue;

      this._index = (idx + 1) % attempts;
      status.lastUsed = now;
      return key;
    }

    // All exhausted — soft reset
    for (const k of this._keys) {
      this._status.get(k).errorCount = 0;
      this._status.get(k).rateLimitedUntil = 0;
    }
    this._index = 0;
    return this._keys[0] || null;
  }

  /** Mark a key as rate-limited (e.g. HTTP 429). */
  markRateLimited(key, retryAfterMs = 60_000) {
    if (!key || !this._status.has(key)) return;
    this._status.get(key).rateLimitedUntil = Date.now() + retryAfterMs;
  }

  /** Mark a key as errored. After 5 errors it's skipped until reset. */
  markError(key) {
    if (!key || !this._status.has(key)) return;
    this._status.get(key).errorCount++;
  }

  /** Mark a key as successful — resets error count. */
  markSuccess(key) {
    if (!key || !this._status.has(key)) return;
    const s = this._status.get(key);
    s.errorCount = 0;
    s.successCount++;
  }

  getStatus() {
    const now = Date.now();
    return {
      total: this._keys.length,
      active: this.activeCount,
      keys: this._keys.map(k => {
        const s = this._status.get(k);
        return {
          prefix: k.slice(0, 8) + "...",
          rateLimited: s.rateLimitedUntil > now,
          errors: s.errorCount,
          successes: s.successCount,
        };
      }),
    };
  }

  /** Refresh keys from env (owner can add keys without restart). */
  reload(newKeys = []) {
    this._keys = newKeys.filter(Boolean);
    for (const key of this._keys) {
      if (!this._status.has(key)) {
        this._status.set(key, { rateLimitedUntil: 0, errorCount: 0, successCount: 0 });
      }
    }
  }
}

module.exports = { KeyRotator };
