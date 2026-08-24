import { forwardRef } from 'react'
import Icon from './Icon.jsx'

/* ------------------------------------------------------------------ *
 * Shared console primitives. Kept in one module on purpose — they are
 * all two-to-ten liners and splitting them across 12 files made imports
 * noisier than the components themselves.
 * ------------------------------------------------------------------ */

export function PageHeader({ title, meta, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 pb-3.5 mb-5 border-b border-line">
      <div>
        <h2 className="text-[21px] font-semibold tracking-tight">{title}</h2>
        {meta && <p className="text-sm text-txt-3 font-mono num mt-0.5 uppercase">{meta}</p>}
      </div>
      {children && <div className="flex flex-wrap gap-2">{children}</div>}
    </div>
  )
}

export const Btn = forwardRef(function Btn(
  { variant, size, icon, className = '', children, ...rest },
  ref
) {
  const v = variant === 'pri' ? 'btn-pri' : variant === 'dgr' ? 'btn-dgr' : variant === 'ghost' ? 'btn-ghost' : ''
  return (
    <button ref={ref} className={`btn ${v} ${size === 'sm' ? 'btn-sm' : ''} ${className}`} {...rest}>
      {icon && <Icon name={icon} size={size === 'sm' ? 13 : 15} />}
      {children}
    </button>
  )
})

export function Card({ className = '', children }) {
  return <div className={`card ${className}`}>{children}</div>
}

/** `hint` is the plain-text right slot; pass children instead when the slot
 *  needs controls. Children win, so a card can fall back to a hint. */
export function CardHead({ title, hint, children }) {
  return (
    <div className="card-h">
      <h3>{title}</h3>
      {children ?? (hint ? <span className="hint">{hint}</span> : null)}
    </div>
  )
}

export function CardBody({ className = '', children }) {
  return <div className={`card-b ${className}`}>{children}</div>
}

/** KPI tile. `tone` drives the accent rail on the leading edge. */
export function Kpi({ label, value, sub, tone = 'info', trend }) {
  const rail = {
    safe: 'bg-safe',
    warn: 'bg-warn',
    crit: 'bg-crit',
    info: 'bg-info',
    hi: 'bg-hi',
  }[tone]
  return (
    <div className="relative overflow-hidden bg-steel-2 border border-line rounded-md px-4 py-[15px]">
      <span className={`absolute top-0 end-0 w-[3px] h-full ${rail}`} />
      <div className="text-xs text-txt-3 uppercase tracking-wide font-mono mb-1.5">{label}</div>
      <div className="text-[30px] font-bold font-mono num leading-none tracking-[-1.5px]">{value}</div>
      {sub && (
        <div className="text-xs text-txt-2 mt-1.5 flex items-center gap-1.5">
          {trend === 'up' && <span className="text-safe">▲</span>}
          {trend === 'down' && <span className="text-crit">▼</span>}
          <span>{sub}</span>
        </div>
      )}
    </div>
  )
}

export function KpiRow({ children }) {
  return (
    <div className="grid gap-3 mb-5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(190px,1fr))' }}>
      {children}
    </div>
  )
}

/** Status chip. Accepts an explicit tone, or maps a known Arabic status. */
export function Pill({ tone, children, icon }) {
  const cls = { ok: 'p-ok', wn: 'p-wn', cr: 'p-cr', in: 'p-in', nu: 'p-nu' }[tone] || 'p-nu'
  return (
    <span className={`pill ${cls}`}>
      {icon && <Icon name={icon} size={11} />}
      {children}
    </span>
  )
}

export function Tag({ tone, children }) {
  return <span className={`tag ${tone === 'g' ? 'tag-g' : tone === 'r' ? 'tag-r' : ''}`}>{children}</span>
}

export function StatLine({ label, value, valueClass = '' }) {
  return (
    <div className="stat-line">
      <span>{label}</span>
      {typeof value === 'string' || typeof value === 'number' ? (
        <b className={valueClass}>{value}</b>
      ) : (
        value
      )}
    </div>
  )
}

/** Labelled progress bar — used for coverage, compliance and safety scores. */
export function BarRow({ label, value, display, color = '#4A9DD8', note, width }) {
  return (
    <div className="mb-3.5 last:mb-0">
      <div className="flex justify-between text-sm mb-0.5">
        <span>{label}</span>
        <b className="font-mono num font-semibold" style={{ color }}>
          {display ?? `${value}%`}
        </b>
      </div>
      <div className="bar-track" style={width ? { width } : undefined}>
        <i className="bar-fill" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
      </div>
      {note && <div className="text-2xs text-txt-3 mt-1">{note}</div>}
    </div>
  )
}

export function MiniBar({ value, color, width = 78 }) {
  return (
    <div className="bar-track mt-0" style={{ width }}>
      <i className="bar-fill" style={{ width: `${Math.min(value, 100)}%`, background: color }} />
    </div>
  )
}

/** Vertical event rail used by alerts, findings and inspection notes. */
export function Timeline({ children }) {
  return (
    <div className="relative pe-[22px]">
      <span className="absolute end-1.5 top-1.5 bottom-1.5 w-0.5 bg-line" />
      {children}
    </div>
  )
}

export function TimelineItem({ time, color = '#4A9DD8', children }) {
  return (
    <div className="relative pb-4 last:pb-0">
      <span
        className="absolute -end-[20px] top-1.5 w-[11px] h-[11px] rounded-full border-2 border-steel-2"
        style={{ background: color }}
      />
      <div className="text-xs text-txt-3 font-mono num">{time}</div>
      <div className="text-[12.5px] mt-0.5">{children}</div>
    </div>
  )
}

/** Numbered / lettered step used by RCA, approval chains and workflows. */
export function Step({ n, title, tone, children }) {
  const bg = tone === 'ok' ? '#38B87C' : tone === 'wn' ? '#F09030' : tone === 'nu' ? '#1B2E4A' : '#9E1B32'
  return (
    <div className="flex gap-3 py-3 border-b last:border-b-0" style={{ borderColor: 'rgba(39,64,95,.5)' }}>
      <div
        className="w-[26px] h-[26px] rounded-full flex items-center justify-center font-mono num text-[12px] font-bold text-white shrink-0"
        style={{ background: bg }}
      >
        {n}
      </div>
      <div className="flex-1">
        <h4 className="text-[13px] font-semibold mb-1">{title}</h4>
        <div className="text-xs text-txt-2 leading-[1.75]">{children}</div>
      </div>
    </div>
  )
}

export function Legend({ items }) {
  return (
    <div className="flex flex-wrap gap-4 text-xs text-txt-2 mt-3">
      {items.map((it) => (
        <span key={it.label} className="flex items-center gap-1.5">
          <i className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: it.color }} />
          {it.label}
        </span>
      ))}
    </div>
  )
}

export function Grid({ cols = 2, className = '', children }) {
  const min = { 2: 330, 3: 270, 4: 215 }[cols] || 330
  return (
    <div className={`grid gap-3.5 ${className}`} style={{ gridTemplateColumns: `repeat(auto-fit,minmax(${min}px,1fr))` }}>
      {children}
    </div>
  )
}

export function Empty({ children = 'لا توجد بيانات مطابقة' }) {
  return (
    <div className="text-center py-10 px-5 text-txt-3">
      <Icon name="document" size={34} className="mx-auto mb-2.5 opacity-40" />
      <div className="text-sm">{children}</div>
    </div>
  )
}

/** Skeleton rows — the console is data-first, so loading shows table shape. */
export function Loading({ rows = 5, className = '' }) {
  return (
    <div className={`p-4 ${className}`}>
      {Array.from({ length: rows }).map((_, i) => (
        <div
          key={i}
          className="h-[13px] rounded-sm bg-steel-3 mb-2.5 last:mb-0 animate-pulse"
          style={{ width: `${92 - i * 7}%`, animationDelay: `${i * 70}ms` }}
        />
      ))}
    </div>
  )
}

export function ErrorNote({ error, onRetry }) {
  return (
    <div className="p-4">
      <div className="border rounded p-3.5 text-xs leading-7" style={{ borderColor: 'rgba(224,72,60,.4)', background: 'rgba(224,72,60,.09)' }}>
        <div className="font-semibold text-crit mb-1 flex items-center gap-1.5">
          <Icon name="incident" size={14} /> تعذّر جلب البيانات من الخادم
        </div>
        <div className="text-txt-2 font-mono num text-2xs">{String(error?.message || error)}</div>
        {onRetry && (
          <Btn size="sm" icon="refresh" className="mt-2.5" onClick={onRetry}>
            إعادة المحاولة
          </Btn>
        )}
      </div>
    </div>
  )
}

/**
 * Renders the three states of a `useApi` call so pages don't repeat the
 * `loading ? … : error ? … :` ladder seventeen times.
 */
export function Async({ state, rows = 5, children }) {
  if (state.loading) return <Loading rows={rows} />
  if (state.error) return <ErrorNote error={state.error} onRetry={state.reload} />
  if (state.data == null) return <Empty />
  return children(state.data)
}

/** Table shell: keeps the horizontal-scroll wrapper and header markup in one place. */
export function Table({ head, children, clickable = true, className = '' }) {
  return (
    <div className="tw">
      <table className={`tbl ${clickable ? 'tbl-rows' : ''} ${className}`}>
        <thead>
          <tr>
            {head.map((h, i) => (
              <th key={i}>{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>{children}</tbody>
      </table>
    </div>
  )
}

/** Donut gauge for the ratio KPIs on the reports page. */
export function Donut({ value, pct, color = '#38B87C' }) {
  return (
    <div className="flex items-center justify-center">
      <div
        className="w-24 h-24 rounded-full flex items-center justify-center relative print:border print:border-slate-300"
        style={{ background: `conic-gradient(${color} 0 ${pct}%, var(--donut-bg, #1B2E4A) ${pct}% 100%)` }}
      >
        <span className="absolute w-[70px] h-[70px] rounded-full bg-steel-2 print:!bg-white print:border print:border-slate-200" />
        <span className="relative z-10 font-mono num font-bold text-[19px] text-txt print:!text-slate-900">{value}</span>
      </div>
    </div>
  )
}

export function LiveDot({ label = 'LIVE', tone = 'crit' }) {
  const c = tone === 'crit' ? '#E0483C' : '#38B87C'
  return (
    <span className="flex items-center gap-1.5 text-2xs font-mono num" style={{ color: c }}>
      <i className="w-[7px] h-[7px] rounded-full animate-blip" style={{ background: c }} />
      {label}
    </span>
  )
}

export function Field({ label, children, className = '' }) {
  return (
    <div className={`mb-3.5 ${className}`}>
      {label && <label className="label">{label}</label>}
      {children}
    </div>
  )
}
