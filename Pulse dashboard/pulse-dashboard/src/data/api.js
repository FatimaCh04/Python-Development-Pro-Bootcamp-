/**
 * api.js — central fetch wrapper for the Pulse Flask backend.
 *
 * Features
 * --------
 * - Base URL from VITE_API_URL env var (falls back to localhost:5000)
 * - Attaches Authorization: Bearer <access_token> automatically
 * - On 401 "token_expired": silently refreshes with the stored refresh token,
 *   replaces stored access token, then retries the original request once.
 * - On any other 401 (bad token / unauthorised): fires a custom
 *   "pulse:logout" event so AuthContext can clear state.
 * - Exports typed helpers: api.get / api.post / api.patch / api.delete
 *   plus a raw `apiFetch` for multipart (FormData) calls.
 */

// In development, VITE_API_URL is left unset — Vite's proxy forwards /api/* to Flask.
// In production (Vercel), set VITE_API_URL=https://your-backend.onrender.com
const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '')

// ─── Token storage ────────────────────────────────────────────────────────────
export const tokenStore = {
  getAccess: () => localStorage.getItem('pulse_access_token'),
  getRefresh: () => localStorage.getItem('pulse_refresh_token'),
  setAccess: (t) => localStorage.setItem('pulse_access_token', t),
  setRefresh: (t) => localStorage.setItem('pulse_refresh_token', t),
  clear: () => {
    localStorage.removeItem('pulse_access_token')
    localStorage.removeItem('pulse_refresh_token')
    localStorage.removeItem('pulse_user')
  },
}

// ─── Core fetch ───────────────────────────────────────────────────────────────
let _refreshPromise = null  // deduplicate concurrent refresh attempts

async function _doRefresh() {
  const refreshToken = tokenStore.getRefresh()
  if (!refreshToken) throw new Error('No refresh token')

  const res = await fetch(`${BASE_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${refreshToken}`,
    },
  })

  if (!res.ok) throw new Error('Refresh failed')
  const data = await res.json()
  tokenStore.setAccess(data.access_token)
  return data.access_token
}

/**
 * Low-level fetch wrapper used by all helpers below.
 * Pass `body` as FormData for multipart uploads — Content-Type is omitted
 * so the browser sets the correct multipart boundary automatically.
 *
 * @param {string} path   e.g. '/api/posts'
 * @param {RequestInit & { skipAuth?: boolean }} options
 * @param {boolean} _isRetry  internal flag to prevent infinite retry loops
 */
export async function apiFetch(path, options = {}, _isRetry = false) {
  const { skipAuth = false, ...fetchOptions } = options

  const headers = new Headers(fetchOptions.headers || {})

  // Attach access token unless caller explicitly skips auth (e.g. login/signup)
  if (!skipAuth) {
    const token = tokenStore.getAccess()
    if (token) headers.set('Authorization', `Bearer ${token}`)
  }

  // Only set Content-Type for JSON bodies; FormData sets its own
  if (fetchOptions.body && !(fetchOptions.body instanceof FormData)) {
    if (!headers.has('Content-Type')) {
      headers.set('Content-Type', 'application/json')
    }
  }

  const response = await fetch(`${BASE_URL}${path}`, {
    ...fetchOptions,
    headers,
  })

  // ── Handle token expiry ───────────────────────────────────────────────────
  if (response.status === 401 && !_isRetry && !skipAuth) {
    let body
    try { body = await response.clone().json() } catch { body = {} }

    if (body.error === 'token_expired') {
      // Deduplicate: if a refresh is already in flight, wait for it
      if (!_refreshPromise) {
        _refreshPromise = _doRefresh().finally(() => { _refreshPromise = null })
      }
      try {
        await _refreshPromise
        // Retry the original request with the new token
        return apiFetch(path, options, true)
      } catch {
        tokenStore.clear()
        window.dispatchEvent(new CustomEvent('pulse:logout'))
        throw new Error('Session expired — please log in again')
      }
    }

    // Any other 401 (invalid token, missing auth, etc.)
    tokenStore.clear()
    window.dispatchEvent(new CustomEvent('pulse:logout'))
    throw new Error('Unauthorised')
  }

  // ── Parse response ────────────────────────────────────────────────────────
  // Return the raw response for callers that need status + body together
  return response
}

// ─── Convenience helpers ─────────────────────────────────────────────────────

/** Parse JSON and throw a human-readable error on non-2xx. */
async function _json(response) {
  let data
  try { data = await response.json() } catch { data = {} }
  if (!response.ok) {
    throw new Error(data.error || data.message || `HTTP ${response.status}`)
  }
  return data
}

export const api = {
  get: (path, opts = {}) =>
    apiFetch(path, { method: 'GET', ...opts }).then(_json),

  post: (path, body, opts = {}) =>
    apiFetch(path, {
      method: 'POST',
      body: body instanceof FormData ? body : JSON.stringify(body),
      ...opts,
    }).then(_json),

  patch: (path, body, opts = {}) =>
    apiFetch(path, {
      method: 'PATCH',
      body: JSON.stringify(body),
      ...opts,
    }).then(_json),

  delete: (path, opts = {}) =>
    apiFetch(path, { method: 'DELETE', ...opts }).then(_json),
}

export default api
