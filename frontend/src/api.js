const API_BASE_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace(/\/$/, '')

export class ApiError extends Error {
  code

  constructor(message, code = 'API_ERROR') {
    super(message)
    this.name = 'ApiError'
    this.code = code
  }
}

const request = async (path, options = {}) => {
  const headers = new Headers(options.headers)
  if (options.body && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json')
  }
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
  })
  if (response.status === 204) return null

  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(
      payload?.error?.message || 'We couldn’t finish that step. Please try again.',
      payload?.error?.code,
    )
  }
  return payload
}

export const createIdempotencyKey = (prefix) => {
  const id = globalThis.crypto?.randomUUID?.() || `${Date.now()}-${Math.random().toString(16).slice(2)}`
  return `${prefix}-${id}`
}

export const createAnalysis = (purpose, decisionDate, signal) => request('/v2/analyses', {
  method: 'POST',
  body: JSON.stringify({
    purpose,
    decision_date: decisionDate || null,
  }),
  signal,
})

export const uploadDocument = (analysisId, file, idempotencyKey, signal) => {
  const body = new FormData()
  body.append('document', file)
  return request(`/v2/analyses/${encodeURIComponent(analysisId)}/documents`, {
    method: 'POST',
    body,
    headers: { 'Idempotency-Key': idempotencyKey },
    signal,
  })
}

export const scanPrivacy = (analysisId, idempotencyKey, signal) => request(
  `/v2/analyses/${encodeURIComponent(analysisId)}/privacy-scan`,
  {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    signal,
  },
)

export const reviewPrivacy = (analysisId, decisions, idempotencyKey, signal) => request(
  `/v2/analyses/${encodeURIComponent(analysisId)}/privacy-findings`,
  {
    method: 'PATCH',
    body: JSON.stringify({ decisions }),
    headers: { 'Idempotency-Key': idempotencyKey },
    signal,
  },
)

export const extractTerms = (analysisId, idempotencyKey, signal) => request(
  `/v2/analyses/${encodeURIComponent(analysisId)}/extract`,
  {
    method: 'POST',
    headers: { 'Idempotency-Key': idempotencyKey },
    signal,
  },
)

export const reviewTerms = (analysisId, decisions, idempotencyKey, signal) => request(
  `/v2/analyses/${encodeURIComponent(analysisId)}/terms`,
  {
    method: 'PATCH',
    body: JSON.stringify({ decisions }),
    headers: { 'Idempotency-Key': idempotencyKey },
    signal,
  },
)

export const deleteAnalysis = (analysisId, signal) => request(
  `/v2/analyses/${encodeURIComponent(analysisId)}`,
  {
    method: 'DELETE',
    signal,
  },
)