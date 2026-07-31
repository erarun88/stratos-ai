// Defaults to '/api', which the Vite dev server proxies to the backend
// (see vite.config.ts). This keeps all browser requests same-origin, so
// the app works in Codespaces / remote dev hosts without exposing the
// backend port. Override with VITE_API_BASE_URL for other setups.
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api'

/**
 * Extracts a human-readable message from a FastAPI error response body.
 * FastAPI returns `{ detail: "..." }` for HTTPExceptions and
 * `{ detail: [{ msg, loc, ... }] }` for validation (422) errors.
 */
function parseErrorDetail(body: unknown, fallback: string): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail) && detail.length > 0) {
      return detail
        .map((d) => (d && typeof d === 'object' && 'msg' in d ? String((d as { msg: unknown }).msg) : ''))
        .filter(Boolean)
        .join('; ')
    }
  }
  return fallback
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  // File uploads must be sent as FormData, and the browser has to set that
  // Content-Type itself (it appends the multipart boundary), so only JSON
  // requests declare one.
  const isFormData = options.body instanceof FormData

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
      ...options.headers,
    },
  })

  if (!response.ok) {
    let body: unknown = null
    try {
      body = await response.json()
    } catch {
      // response had no JSON body
    }
    throw new Error(parseErrorDetail(body, `Request to ${path} failed (${response.status})`))
  }

  if (response.status === 204) {
    return undefined as T
  }
  return response.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'POST', body: JSON.stringify(body) })
}

export function apiPut<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'PUT', body: JSON.stringify(body) })
}

export function apiPatch<T>(path: string, body: unknown): Promise<T> {
  return request<T>(path, { method: 'PATCH', body: JSON.stringify(body) })
}

export function apiDelete(path: string): Promise<void> {
  return request<void>(path, { method: 'DELETE' })
}

/** POST a multipart/form-data body (file uploads). */
export function apiPostForm<T>(path: string, form: FormData): Promise<T> {
  return request<T>(path, { method: 'POST', body: form })
}

/**
 * Absolute URL for an API path. Used for links the browser follows itself —
 * e.g. file downloads, where letting the browser stream the response is
 * simpler and more memory-efficient than buffering it into a blob.
 */
export function apiUrl(path: string): string {
  return `${API_BASE_URL}${path}`
}
