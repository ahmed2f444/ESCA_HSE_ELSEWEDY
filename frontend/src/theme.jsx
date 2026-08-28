import { createContext, useCallback, useContext, useEffect, useState } from 'react'

/* ------------------------------------------------------------------ *
 * Theme state — mode ('standard' | 'dark' | 'light' | 'colorblind' | 'custom') + accent.
 * Persisted in localStorage under `esca.hse.theme`.
 *
 * Mode behavior:
 * - 'standard': Default corporate navy console (clean deep navy surfaces from index.css).
 * - 'dark': True Pitch Black OLED mode (deep black #07090D base with high contrast).
 * - 'light': Clean high-contrast light mode with white cards from index.css.
 * - 'colorblind': Accessible high-contrast slate & cobalt/amber/orange indicators from index.css.
 * - 'custom': Dynamic palette derived from selected color via inline CSS variables.
 *
 * When switching away from 'custom' to 'standard', 'dark', 'light', or 'colorblind',
 * all inline CSS variables are cleanly removed from document.documentElement
 * and document.body so stylesheet rules take full control immediately.
 * ------------------------------------------------------------------ */

const STORAGE_KEY = 'esca.hse.theme'
export const MODES = ['standard', 'dark', 'light', 'colorblind', 'custom']
const DEFAULT_MODE = 'standard'
export const DEFAULT_CUSTOM_ACCENT = '#7C3AED'

export const PALETTE_PROPS = [
  '--c-steel',
  '--c-steel2',
  '--c-steel3',
  '--c-line',
  '--c-hi',
  '--c-hi2',
  '--c-hi-dim',
  '--c-hi-txt',
  '--c-safe',
  '--c-warn',
  '--c-crit',
  '--c-info',
  '--c-txt',
  '--c-txt2',
  '--c-txt3',
]

/** Color math: Convert Hex to RGB triplet array */
export function hexToRgb(hex) {
  if (!hex || typeof hex !== 'string') return [124, 58, 237]
  const clean = hex.replace('#', '')
  if (clean.length === 3) {
    return [
      parseInt(clean[0] + clean[0], 16) || 0,
      parseInt(clean[1] + clean[1], 16) || 0,
      parseInt(clean[2] + clean[2], 16) || 0,
    ]
  }
  return [
    parseInt(clean.slice(0, 2), 16) || 0,
    parseInt(clean.slice(2, 4), 16) || 0,
    parseInt(clean.slice(4, 6), 16) || 0,
  ]
}

/**
 * Dynamic Palette Derivation: Generates rich, deeply saturated surface and
 * background shades directly from the selected RGB color values for Custom mode.
 */
export function derivePaletteFromRgb(r, g, b) {
  const lum = (0.299 * r + 0.587 * g + 0.114 * b) / 255
  const txtColor = lum > 0.58 ? '15 23 42' : '255 255 255'

  return {
    '--c-steel':   `${Math.round(r * 0.12 + 6)} ${Math.round(g * 0.10 + 6)} ${Math.round(b * 0.18 + 8)}`,
    '--c-steel2':  `${Math.round(r * 0.22 + 10)} ${Math.round(g * 0.18 + 10)} ${Math.round(b * 0.30 + 14)}`,
    '--c-steel3':  `${Math.round(r * 0.32 + 14)} ${Math.round(g * 0.26 + 14)} ${Math.round(b * 0.40 + 20)}`,
    '--c-line':    `${Math.round(r * 0.45 + 20)} ${Math.round(g * 0.38 + 20)} ${Math.round(b * 0.55 + 28)}`,
    '--c-txt':     '248 250 255',
    '--c-txt2':    `${Math.min(255, Math.round(r * 0.35 + 160))} ${Math.min(255, Math.round(g * 0.35 + 165))} ${Math.min(255, Math.round(b * 0.35 + 195))}`,
    '--c-txt3':    `${Math.min(255, Math.round(r * 0.30 + 110))} ${Math.min(255, Math.round(g * 0.30 + 115))} ${Math.min(255, Math.round(b * 0.30 + 145))}`,
    '--c-hi':      `${r} ${g} ${b}`,
    '--c-hi2':     `${Math.min(255, Math.round(r + 35))} ${Math.min(255, Math.round(g + 35))} ${Math.min(255, Math.round(b + 35))}`,
    '--c-hi-dim':  `${Math.round(r * 0.4 + 15)} ${Math.round(g * 0.4 + 15)} ${Math.round(b * 0.4 + 20)}`,
    '--c-hi-txt':  txtColor,
    '--c-safe':    '56 184 124',
    '--c-warn':    '240 144 48',
    '--c-crit':    '224 72 60',
    '--c-info':    '74 157 216',
  }
}

/** Read persisted theme preferences (or fall back to defaults). */
function readStored() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return { mode: DEFAULT_MODE, accent: null, lastCustomAccent: DEFAULT_CUSTOM_ACCENT }
    const parsed = JSON.parse(raw)
    const validMode = MODES.includes(parsed.mode) ? parsed.mode : DEFAULT_MODE
    const lastColor = typeof parsed.lastCustomAccent === 'string'
      ? parsed.lastCustomAccent
      : (typeof parsed.accent === 'string' ? parsed.accent : DEFAULT_CUSTOM_ACCENT)
    return {
      mode: validMode,
      accent: validMode === 'custom' ? (typeof parsed.accent === 'string' ? parsed.accent : lastColor) : null,
      lastCustomAccent: lastColor,
    }
  } catch {
    return { mode: DEFAULT_MODE, accent: null, lastCustomAccent: DEFAULT_CUSTOM_ACCENT }
  }
}

/** Apply theme values to DOM elements. */
export function applyToDOM(mode, accent, lastCustomAccent) {
  const html = document.documentElement
  const body = document.body
  
  html.setAttribute('data-theme', mode)
  html.className = mode
  if (body) {
    body.setAttribute('data-theme', mode)
    body.className = `${mode} bg-steel text-txt font-sans text-base antialiased`
  }
  html.style.colorScheme = mode === 'light' ? 'light' : 'dark'

  if (mode === 'custom') {
    // ONLY in Custom Mode: calculate and inject dynamic surface and accent variables
    const activeColor = accent || lastCustomAccent || DEFAULT_CUSTOM_ACCENT
    const [r, g, b] = hexToRgb(activeColor)
    const vars = derivePaletteFromRgb(r, g, b)

    Object.entries(vars).forEach(([k, v]) => {
      html.style.setProperty(k, v)
      if (body) {
        body.style.setProperty(k, v)
      }
    })
  } else {
    // In Standard, Dark, Light, and Colorblind modes: EXPLICITLY CLEAR all inline custom variables
    // so index.css stylesheet rules take full, clean control
    PALETTE_PROPS.forEach((prop) => {
      html.style.removeProperty(prop)
      if (body) {
        body.style.removeProperty(prop)
      }
    })
  }
}

const ThemeCtx = createContext(null)

export function ThemeProvider({ children }) {
  const [{ mode, accent, lastCustomAccent }, setState] = useState(readStored)

  // Sync DOM whenever state changes
  useEffect(() => {
    applyToDOM(mode, accent, lastCustomAccent)
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ mode, accent, lastCustomAccent }))
  }, [mode, accent, lastCustomAccent])

  const setMode = useCallback((m) => {
    if (MODES.includes(m)) {
      setState((s) => {
        const nextAccent = m === 'custom' ? (s.lastCustomAccent || DEFAULT_CUSTOM_ACCENT) : null
        return {
          ...s,
          mode: m,
          accent: nextAccent,
        }
      })
    }
  }, [])

  const setAccentColor = useCallback((hex) => {
    if (hex && typeof hex === 'string') {
      setState({
        mode: 'custom',
        accent: hex,
        lastCustomAccent: hex,
      })
    }
  }, [])

  const resetAccent = useCallback(() => {
    setState((s) => ({
      mode: DEFAULT_MODE,
      accent: null,
      lastCustomAccent: s.lastCustomAccent || DEFAULT_CUSTOM_ACCENT,
    }))
  }, [])

  return (
    <ThemeCtx.Provider value={{
      mode,
      setMode,
      accent,
      lastCustomAccent: lastCustomAccent || DEFAULT_CUSTOM_ACCENT,
      setAccent: setAccentColor,
      setAccentColor,
      resetAccent,
      modes: MODES,
    }}>
      {children}
    </ThemeCtx.Provider>
  )
}

export function useTheme() {
  const ctx = useContext(ThemeCtx)
  if (!ctx) throw new Error('useTheme must be used inside ThemeProvider')
  return ctx
}
