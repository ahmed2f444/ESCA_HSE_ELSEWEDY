import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

/* Recharts defaults are built for LTR light themes; these wrappers pin the
   axis direction, the grid colour and the tooltip chrome so every chart in
   the console looks like it came off the same plotter. */

const AXIS = { stroke: '#5E7794', fontSize: 11, fontFamily: '"IBM Plex Mono", monospace' }
const GRID = '#2E3D4E'

function TipBox({ active, payload, label, unit = '' }) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-steel-3 border border-line rounded px-3 py-2 text-xs shadow-lg">
      <div className="font-mono num text-txt-3 mb-1">{label}</div>
      {payload.map((p) => (
        <div key={p.dataKey} className="flex items-center gap-2 justify-between">
          <span className="flex items-center gap-1.5">
            <i className="w-2 h-2 rounded-sm inline-block" style={{ background: p.color || p.fill }} />
            {p.name}
          </span>
          <b className="font-mono num">
            {p.value}
            {unit}
          </b>
        </div>
      ))}
    </div>
  )
}

/** Monthly incidents / near misses / observations. */
export function MonthlyBars({ data }) {
  return (
    <ResponsiveContainer width="100%" height={215}>
      <BarChart data={data} margin={{ top: 8, right: 4, left: -18, bottom: 0 }} barGap={2}>
        <CartesianGrid stroke={GRID} strokeDasharray="0" vertical={false} />
        <XAxis dataKey="month" reversed tickLine={false} axisLine={{ stroke: GRID }} tick={AXIS} />
        <YAxis orientation="right" tickLine={false} axisLine={false} tick={AXIS} width={44} />
        <Tooltip content={<TipBox />} cursor={{ fill: 'rgba(158,27,50,.10)' }} />
        <Bar dataKey="incidents" name="حوادث مسجّلة" fill="#E0483C" radius={[2, 2, 0, 0]} />
        <Bar dataKey="nearMiss" name="أشباه حوادث" fill="#F09030" radius={[2, 2, 0, 0]} />
        <Bar dataKey="observations" name="ملاحظات سلامة" fill="#38B87C" radius={[2, 2, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
}

/** Five-year TRIR trend with the value printed on each point. */
export function TrirTrend({ data }) {
  return (
    <ResponsiveContainer width="100%" height={205}>
      <AreaChart data={data} margin={{ top: 22, right: 6, left: -14, bottom: 0 }}>
        <defs>
          <linearGradient id="trirFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#38B87C" stopOpacity={0.34} />
            <stop offset="100%" stopColor="#38B87C" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="year" reversed tickLine={false} axisLine={{ stroke: GRID }} tick={AXIS} />
        <YAxis orientation="right" tickLine={false} axisLine={false} tick={AXIS} width={46} />
        <Tooltip content={<TipBox />} cursor={{ stroke: '#5E7794', strokeDasharray: '3 3' }} />
        <Area
          type="monotone"
          dataKey="trir"
          name="TRIR"
          stroke="#38B87C"
          strokeWidth={2.4}
          fill="url(#trirFill)"
          dot={{ r: 4, fill: '#0B1526', stroke: '#38B87C', strokeWidth: 2.4 }}
          activeDot={{ r: 6 }}
        >
          <LabelList
            dataKey="trir"
            position="top"
            offset={11}
            style={{ fill: '#E9EFF7', fontSize: 11, fontFamily: '"IBM Plex Mono", monospace', fontWeight: 600 }}
          />
        </Area>
      </AreaChart>
    </ResponsiveContainer>
  )
}

/** Horizontal comparison used for fire-equipment coverage per zone. */
export function ZoneBars({ data, dataKey, nameKey, color = '#4A9DD8', height = 250 }) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} layout="vertical" margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
        <CartesianGrid stroke={GRID} horizontal={false} />
        <XAxis type="number" orientation="top" tickLine={false} axisLine={false} tick={AXIS} />
        <YAxis
          type="category"
          dataKey={nameKey}
          orientation="right"
          tickLine={false}
          axisLine={false}
          width={118}
          tick={{ ...AXIS, fontFamily: '"IBM Plex Sans Arabic", sans-serif', fontSize: 11 }}
        />
        <Tooltip content={<TipBox />} cursor={{ fill: 'rgba(158,27,50,.10)' }} />
        <Bar dataKey={dataKey} name="العدد" radius={[0, 2, 2, 0]}>
          {data.map((d, i) => (
            <Cell key={i} fill={d.color || color} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}

/** 24-point sparkline for a single sensor channel. */
export function Spark({ values = [], color = '#4A9DD8' }) {
  if (!values || !values.length) return null
  const min = Math.min(...values)
  const max = Math.max(...values)
  const span = max - min || 1
  const pts = values
    .map((v, i) => `${(i / Math.max(1, values.length - 1)) * 100},${28 - ((v - min) / span) * 24 - 2}`)
    .join(' ')
  return (
    <svg viewBox="0 0 100 28" preserveAspectRatio="none" className="w-full h-7">
      <polyline points={pts} fill="none" stroke={color} strokeWidth="1.6" vectorEffect="non-scaling-stroke" />
    </svg>
  )
}

/* ------------------------------------------------------------------ */
/* Domain-specific visuals — hand-built, not chart-library shapes       */
/* ------------------------------------------------------------------ */

export const bandColor = (score) =>
  score <= 4 ? '#38B87C' : score <= 9 ? '#C6C43A' : score <= 14 ? '#F09030' : score <= 19 ? '#E0483C' : '#8E1F17'

export const bandLabel = (score) =>
  score <= 4 ? 'مقبول' : score <= 9 ? 'منخفض' : score <= 14 ? 'متوسط' : score <= 19 ? 'عالي' : 'حرج'

const SEVERITY = ['ضئيل 1', 'بسيط 2', 'متوسط 3', 'كبير 4', 'كارثي 5']
const PROBABILITY = ['نادر 1', 'ضعيف 2', 'ممكن 3', 'مرجح 4', 'شبه مؤكد 5']

/**
 * 5×5 HIRA matrix. Cells carry the count of hazards that land on them, so the
 * register and the matrix are two views of one dataset — clicking a cell
 * filters the register below it.
 */
export function RiskMatrix({ hazards = [], selected, onSelect }) {
  const count = (p, s) => hazards.filter((h) => h.probability === p && h.severity === s).length

  return (
    <div className="overflow-x-auto">
      <div className="grid gap-[3px] font-mono num text-xs min-w-[420px]" style={{ gridTemplateColumns: 'auto repeat(5,1fr)' }}>
        <div className="bg-steel-3 text-txt-2 text-2xs py-2.5 px-1 text-center rounded-sm">احتمالية ↓ / شدة →</div>
        {SEVERITY.map((s) => (
          <div key={s} className="bg-steel-3 text-txt-2 text-2xs py-2.5 px-1 text-center rounded-sm">
            {s}
          </div>
        ))}

        {[5, 4, 3, 2, 1].map((p) => (
          <FragmentRow key={p} p={p} count={count} selected={selected} onSelect={onSelect} />
        ))}
      </div>
    </div>
  )
}

function FragmentRow({ p, count, selected, onSelect }) {
  return (
    <>
      <div className="bg-steel-3 text-txt-2 text-2xs py-2.5 px-1 text-center rounded-sm">{PROBABILITY[p - 1]}</div>
      {[1, 2, 3, 4, 5].map((s) => {
        const v = p * s
        const n = count(p, s)
        const key = `${p}x${s}`
        const isSel = selected === key
        return (
          <button
            key={s}
            onClick={() => onSelect?.(isSel ? null : key)}
            title={`درجة الخطر ${v} — احتمالية ${p} × شدة ${s}${n ? ` · ${n} خطر مسجّل` : ''}`}
            className="relative py-2.5 px-1 rounded-sm font-semibold transition-transform duration-150 hover:scale-105 hover:z-10"
            style={{
              background: bandColor(v),
              color: v >= 15 ? '#fff' : '#0d1218',
              outline: isSel ? '2px solid #E9EFF7' : 'none',
              outlineOffset: isSel ? '1px' : 0,
            }}
          >
            {v}
            {n > 0 && (
              <span className="absolute top-0.5 start-1 text-[9px] font-bold opacity-80" style={{ color: v >= 15 ? '#fff' : '#0d1218' }}>
                ●{n}
              </span>
            )}
          </button>
        )
      })}
    </>
  )
}

/** Plant incident-density grid — 4 rows × 8 cells, mirrors the floor layout. */
export function PlantHeatmap({ rows = [], onCell }) {
  const shade = (n) => (n === 0 ? '#1a3a2e' : n <= 2 ? '#8a9a34' : n <= 4 ? '#F09030' : n <= 6 ? '#c0402e' : '#8E1F17')
  const ink = (n) => (n >= 5 ? '#fff' : n === 0 ? '#5E7794' : '#101a10')

  return (
    <div className="space-y-2">
      {rows.map((r) => (
        <div key={r.row}>
          <div className="text-2xs text-txt-3 font-mono mb-1">{r.row}</div>
          <div className="grid grid-cols-8 gap-1">
            {r.cells.map(([name, n]) => (
              <button
                key={name}
                onClick={() => onCell?.(name, n)}
                className="rounded-sm flex flex-col items-center justify-center font-mono num text-[9px] p-1
                           leading-tight transition-transform duration-150 hover:scale-110 hover:z-10"
                style={{ aspectRatio: '1.35', background: shade(n), color: ink(n) }}
              >
                <b className="text-[13px]">{n}</b>
                <span className="text-[8.5px] truncate w-full text-center">{name}</span>
              </button>
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

/** Heinrich pyramid — the reporting-culture check. */
export function SafetyPyramid({ tiers = [] }) {
  return (
    <div>
      <div className="flex flex-col gap-1.5 items-center mb-3.5">
        {tiers.map((t, i) => (
          <div
            key={t.label}
            className="py-1.5 text-center font-mono num font-bold text-[13px]"
            style={{
              width: `${t.width}%`,
              background: t.color,
              color: t.textColor,
              borderRadius: i === 0 ? '3px 3px 0 0' : i === tiers.length - 1 ? '0 0 3px 3px' : 0,
            }}
          >
            {t.count}
          </div>
        ))}
      </div>
      <div className="text-xs text-txt-2 leading-8">
        {tiers.map((t) => (
          <div key={t.label} className="flex items-center gap-2">
            <i className="w-2.5 h-2.5 rounded-sm inline-block" style={{ background: t.color }} />
            <b className="font-mono num">{t.count}</b>
            <span>— {t.label}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
