/* ------------------------------------------------------------------
   themeColors.js — read CSS theme variables for use in inline JS styles.
   Import `tc` and call e.g. tc.safe() to get the current "safe" color
   as an rgb() string that responds to theme switching.
   
   These are functions (not constants) because the CSS variable values
   change when the user switches theme, so we need to re-read them at
   render time.
------------------------------------------------------------------- */

/** Read a single CSS variable as `rgb(R, G, B)` for use in inline styles. */
function v(name) {
  const rgb = getComputedStyle(document.documentElement).getPropertyValue(name).trim()
  return rgb ? `rgb(${rgb.replace(/ /g, ', ')})` : '#888'
}

/** Theme color accessors — call as functions, e.g. tc.safe() */
const tc = {
  steel:  () => v('--c-steel'),
  steel2: () => v('--c-steel2'),
  steel3: () => v('--c-steel3'),
  line:   () => v('--c-line'),
  hi:     () => v('--c-hi'),
  hi2:    () => v('--c-hi2'),
  hiDim:  () => v('--c-hi-dim'),
  safe:   () => v('--c-safe'),
  warn:   () => v('--c-warn'),
  crit:   () => v('--c-crit'),
  info:   () => v('--c-info'),
  txt:    () => v('--c-txt'),
  txt2:   () => v('--c-txt2'),
  txt3:   () => v('--c-txt3'),
}

/** Common tone maps used across pages — returns an object of color strings. */
export function toneColors() {
  return { ok: tc.safe(), wn: tc.warn(), cr: tc.crit(), in: tc.info() }
}

/** Score→color mapping (for compliance %, safety scores, etc.) */
export function scoreColor(s) {
  return s >= 85 ? tc.safe() : s >= 70 ? tc.warn() : tc.crit()
}

export default tc
