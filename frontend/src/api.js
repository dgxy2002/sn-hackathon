const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000').replace(/\/$/, '')

export class ApiError extends Error {
  code

  constructor(message, code = 'API_ERROR') {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

/**
 * @param {string} path
 * @param {RequestInit} [options]
 */
const request = async (path, options = /** @type {RequestInit} */ ({})) => {
  const headers = new Headers(Reflect.get(options, 'headers'))
  headers.set('Content-Type', 'application/json')
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })
  const payload = await response.json().catch(() => null)

  if (!response.ok) {
    throw new ApiError(
      payload?.error?.message || 'CoverCheck could not complete that request.',
      payload?.error?.code,
    )
  }

  return payload
}

export const createClientId = () => {
  if (globalThis.crypto?.randomUUID) return globalThis.crypto.randomUUID()
  if (globalThis.crypto?.getRandomValues) {
    const bytes = globalThis.crypto.getRandomValues(new Uint8Array(16))
    return `client-${Array.from(bytes, (byte) => byte.toString(16).padStart(2, '0')).join('')}`
  }
  return `client-${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export const createConversation = (activeRevisionId, signal) => request('/v1/conversations', {
  method: 'POST',
  body: JSON.stringify({ active_revision_id: activeRevisionId }),
  signal,
})

export const sendConversationMessage = (conversationId, body, signal) => request(
  `/v1/conversations/${encodeURIComponent(conversationId)}/messages`,
  {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  },
)