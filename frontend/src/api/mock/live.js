import { sensorBaseline, iotEventSeed } from './data.js'

/**
 * Stand-in for AI Student 2's synthetic sensor feed.
 *
 * Readings drift around their baseline with a bounded random walk instead of
 * being re-randomised each poll — a jumpy value looks fake, and the dashboard
 * needs to show a believable trend line. When a channel crosses its limit an
 * event is appended to the same log the real feed will write to.
 */

const state = sensorBaseline.map((s) => ({
  ...s,
  current: s.value,
  history: Array.from({ length: 24 }, (_, i) => s.value + Math.sin(i / 3) * s.jitter * 0.6),
}))

const events = [...iotEventSeed]

function clockLabel(d = new Date()) {
  return d.toTimeString().slice(0, 8)
}

export function pushEvent(e) {
  events.unshift({ at: clockLabel(), ...e })
  if (events.length > 40) events.pop()
}

export function recentEvents() {
  return events.slice(0, 18)
}

/** One drift step per poll; the UI polls every few seconds. */
export function readSensors() {
  return state.map((s) => {
    const step = (Math.random() - 0.5) * s.jitter
    // Pull gently back toward baseline so the walk cannot wander off scale.
    const pull = (s.value - s.current) * 0.12
    let next = s.current + step + pull
    if (s.id === 'SNS-GS-01') next = Math.max(0, next)
    s.current = next
    s.history = [...s.history.slice(1), next]

    const d = s.decimals ?? 0
    const shown = Number(next.toFixed(d))
    const tone = s.inverted
      ? shown < s.crit ? 'cr' : shown < s.warn ? 'wn' : 'ok'
      : shown >= s.crit ? 'cr' : shown >= s.warn ? 'wn' : 'ok'

    // Escalations get logged the same way the real generator will log them.
    if (tone === 'cr' && Math.random() < 0.08) {
      pushEvent({
        code: s.inverted ? 'O2_LOW' : 'LIMIT_EXCEEDED',
        tone: 'cr',
        source: s.id,
        detail: `${shown} ${s.unit}`,
        action: 'إخطار مشرف المنطقة',
      })
    }

    return {
      id: s.id,
      name: s.name,
      limitLabel: s.limitLabel,
      unit: s.unit,
      value: shown,
      tone,
      history: s.history.map((v) => Number(v.toFixed(2))),
    }
  })
}
