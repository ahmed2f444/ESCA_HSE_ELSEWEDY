import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { auth as authApi } from './api/endpoints.js'
import { tokenStore } from './api/client.js'
import { permissionsFor } from './permissions.js'
import Icon from './components/Icon.jsx'

/* ------------------------------------------------------------------ *
 * Data fetching
 * ------------------------------------------------------------------ */

/**
 * Minimal fetch-on-mount hook. No cache layer on purpose — this console
 * is a live plant view, and every page wants fresh numbers when it opens.
 */
export function useApi(fetcher, deps = []) {
  const [state, setState] = useState({ data: null, loading: true, error: null })
  const [nonce, setNonce] = useState(0)
  const fn = useRef(fetcher)
  fn.current = fetcher

  useEffect(() => {
    let alive = true
    setState((s) => ({ ...s, loading: true, error: null }))
    Promise.resolve()
      .then(() => fn.current())
      .then(
        (data) => alive && setState({ data, loading: false, error: null }),
        (error) => alive && setState({ data: null, loading: false, error })
      )
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, nonce])

  return { ...state, reload: useCallback(() => setNonce((n) => n + 1), []) }
}

/** Same, but re-polls on an interval. Used by the IoT panels. */
export function usePolling(fetcher, intervalMs = 4000, deps = []) {
  const [data, setData] = useState(null)
  const fn = useRef(fetcher)
  fn.current = fetcher

  useEffect(() => {
    let alive = true
    const run = () =>
      Promise.resolve()
        .then(() => fn.current())
        .then((d) => alive && setData(d))
        .catch(() => {})
    run()
    const id = setInterval(run, intervalMs)
    return () => {
      alive = false
      clearInterval(id)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [intervalMs, ...deps])

  return data
}

/** Wall clock in the header — plant staff cross-check it against permit times. */
export function useClock() {
  const [t, setT] = useState(() => new Date())
  useEffect(() => {
    const id = setInterval(() => setT(new Date()), 1000)
    return () => clearInterval(id)
  }, [])
  return t
}

/* ------------------------------------------------------------------ *
 * Auth
 * ------------------------------------------------------------------ */

const USER_KEY = 'esca.hse.user'
const AuthCtx = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw || !tokenStore.get()) return null
    try {
      const parsed = JSON.parse(raw)
      if (parsed.username === 'mostafa' && (!parsed.displayName || parsed.displayName === 'محمود عبد الله' || parsed.name === 'محمود عبد الله')) {
        parsed.displayName = 'مصطفى'
        parsed.name = 'مصطفى'
        parsed.initials = 'م'
        localStorage.setItem(USER_KEY, JSON.stringify(parsed))
      } else if (parsed.username === 'admin' && (parsed.displayName === 'محمود عبد الله' || parsed.name === 'محمود عبد الله')) {
        parsed.displayName = 'مدير النظام'
        parsed.name = 'مدير النظام'
        parsed.initials = 'م'
        localStorage.setItem(USER_KEY, JSON.stringify(parsed))
      }
      return parsed
    } catch {
      return null
    }
  })

  const login = useCallback(async (username, password) => {
    const res = await authApi.login(username, password)
    const token = res.token || res.access_token
    tokenStore.set(token)
    localStorage.setItem(USER_KEY, JSON.stringify(res.user))
    setUser(res.user)
    return res.user
  }, [])

  const logout = useCallback(() => {
    tokenStore.clear()
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }, [])

  return <AuthCtx.Provider value={{ user, login, logout }}>{children}</AuthCtx.Provider>
}

export const useAuth = () => useContext(AuthCtx)

/**
 * Role gate. The backend enforces RBAC for real; this only hides controls the
 * current role can't use, so the UI doesn't offer buttons that will 403.
 * The rules themselves live in ../permissions.js.
 */
export function useCan() {
  const { user } = useAuth()
  const role = user?.role
  return { ...permissionsFor(role, user?.permissions), role }
}

/* ------------------------------------------------------------------ *
 * Toasts
 * ------------------------------------------------------------------ */

const ToastCtx = createContext(() => {})

export function ToastProvider({ children }) {
  const [items, setItems] = useState([])

  const push = useCallback((message, tone = 'ok') => {
    const id = Math.random().toString(36).slice(2)
    setItems((s) => [...s, { id, message, tone }])
    setTimeout(() => setItems((s) => s.filter((i) => i.id !== id)), 3600)
  }, [])

  const colors = { ok: '#38B87C', wn: '#F09030', cr: '#E0483C', in: '#4A9DD8' }

  return (
    <ToastCtx.Provider value={push}>
      {children}
      <div className="fixed bottom-5 start-5 z-[999] flex flex-col gap-2 pointer-events-none no-print print:hidden">
        {items.map((t) => (
          <div
            key={t.id}
            className="bg-steel-3 border rounded-md px-4 py-3 text-sm flex items-center gap-2.5 animate-fade"
            style={{
              borderColor: colors[t.tone],
              borderInlineEndWidth: 4,
              boxShadow: '0 8px 26px rgba(0,0,0,.45)',
            }}
          >
            <Icon name={t.tone === 'ok' ? 'check' : 'incident'} size={15} style={{ color: colors[t.tone] }} />
            {t.message}
          </div>
        ))}
      </div>
    </ToastCtx.Provider>
  )
}

export const useToast = () => useContext(ToastCtx)
