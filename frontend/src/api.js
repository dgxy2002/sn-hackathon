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

export const submitExtraction = (fixtureId, signal) => request('/v1/extractions', {
  method: 'POST',
  body: JSON.stringify({ fixture_id: fixtureId }),
  signal,
})

export const reviewExtraction = (extractionId, body, signal) => request(
  `/v1/extractions/${encodeURIComponent(extractionId)}/review`,
  {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  },
)

export const invokeCoverCheck = (body, signal) => request('/v1/invocations', {
  method: 'POST',
  body: JSON.stringify(body),
  signal,
})

export const compareEvidence = (body, signal) => request('/v1/evidence/compare', {
  method: 'POST',
  body: JSON.stringify(body),
  signal,
})

export const createConversation = (activeRevisionId, profile, recommendation, signal) => request('/v1/conversations', {
  method: 'POST',
  body: JSON.stringify({
    active_revision_id: activeRevisionId,
    profile,
    recommendation,
  }),
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

export const decideProposal = (conversationId, proposalId, decision, body, signal) => request(
  `/v1/conversations/${encodeURIComponent(conversationId)}/proposals/${encodeURIComponent(proposalId)}/${decision}`,
  {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  },
)

export const fetchReplay = (conversationId, signal) => request(
  `/v1/conversations/${encodeURIComponent(conversationId)}/replay`,
  { signal },
)

export const undoRevision = (conversationId, body, signal) => request(
  `/v1/conversations/${encodeURIComponent(conversationId)}/undo`,
  {
    method: 'POST',
    body: JSON.stringify(body),
    signal,
  },
)