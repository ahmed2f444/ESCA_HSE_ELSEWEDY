import axios from 'axios'
import mockAdapter from './mock/adapter.js'

/**
 * Two transports, because the platform is two services:
 *
 *   api    → Spring Boot (Member 1 + Member 2)  — /api
 *   agent  → Python FastAPI agent (AI 1 + AI 2) — /agent
 *
 * Both trust the same JWT issued by Spring Boot, so the token interceptor
 * is shared.
 *
 * While the backend is still being built, VITE_USE_MOCK=true swaps axios'
 * adapter for a local one that serves the fixtures in ./mock/data.js.
 * Nothing above this file knows which transport is live — flipping the env
 * var is the whole integration switch.
 */

const viteEnv = import.meta.env ?? {}
export const USE_MOCK = viteEnv.VITE_USE_MOCK !== 'false'

const TOKEN_KEY = 'esca.hse.token'

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
}

function build(baseURL, timeout = 20000, useMockByDefault = true) {
  const instance = axios.create({
    baseURL,
    timeout,
    headers: { 'Content-Type': 'application/json' },
  })

  if (USE_MOCK && useMockByDefault) instance.defaults.adapter = mockAdapter

  instance.interceptors.request.use((config) => {
    const t = tokenStore.get()
    if (t) config.headers.Authorization = `Bearer ${t}`
    return config
  })

  instance.interceptors.response.use(
    (res) => res,
    (err) => {
      const status = err.response?.status
      if (status === 401) {
        tokenStore.clear()
        // Full reload rather than a router push: clears every cached page state.
        if (!location.pathname.startsWith('/login')) location.assign('/login?expired=1')
      }
      // Surface the backend's message when there is one, the transport error otherwise.
      const data = err.response?.data
      if (typeof data === 'string') {
        err.message = data
      } else if (data && typeof data === 'object') {
        if (data.validation_errors && typeof data.validation_errors === 'object') {
          err.message = Object.values(data.validation_errors).filter(Boolean).join(', ') || data.message || err.message
        } else if (data.fields && typeof data.fields === 'object') {
          err.message = Object.values(data.fields).filter(Boolean).join(', ') || data.message || err.message
        } else {
          err.message = data.message || data.error || data.detail || err.message
        }
      }
      return Promise.reject(err)
    }
  )

  return instance
}

export const api = build(viteEnv.VITE_API_BASE_URL || '/api', 25000, true)
export const agent = build(viteEnv.VITE_AGENT_BASE_URL || '/agent', 120000, false)
