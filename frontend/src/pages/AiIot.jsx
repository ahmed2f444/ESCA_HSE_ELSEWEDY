import {
  Async,
  Card,
  CardBody,
  CardHead,
  Grid,
  Kpi,
  KpiRow,
  LiveDot,
  PageHeader,
  Pill,
  StatLine,
  Tag,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { Spark } from '../components/charts.jsx'
import { iot as iotApi } from '../api/endpoints.js'
import { useApi, usePolling } from '../hooks.jsx'

const TONE_COLOR = { ok: '#38B87C', wn: '#F09030', cr: '#E0483C', in: '#4A9DD8' }

/**
 * Live monitoring view.
 *
 * Everything on this page is fed by the simulation service — no real cameras
 * or sensors exist in the training environment. The banner says so explicitly
 * so nobody in a demo mistakes it for a live plant feed.
 */
export default function AiIot() {
  const sensors = usePolling(() => iotApi.sensors(), 3500)
  const events = usePolling(() => iotApi.events(), 5000)
  const detections = useApi(() => iotApi.detections(), [])
  const models = useApi(() => iotApi.models(), [])
  const wearables = useApi(() => iotApi.wearables(), [])

  return (
    <>
      <PageHeader title="المراقبة الآلية والحساسات" meta="computer vision · iot sensors · wearables" />

      <div
        className="flex items-center gap-2.5 text-xs px-3.5 py-2.5 rounded-md mb-5"
        style={{ background: 'rgba(240,144,48,.09)', border: '1px solid rgba(240,144,48,.35)', color: '#F09030' }}
      >
        <Icon name="incident" size={15} />
        <span>
          كل القراءات والاكتشافات في هذه الشاشة مولّدة من خدمة المحاكاة الخاصة بالمشروع — لا توجد كاميرات أو
          حساسات حقيقية موصولة. البنية جاهزة لاستقبال مصدر حقيقي بنفس الشكل.
        </span>
      </div>

      <Async state={models} rows={3}>
        {({ stats }) => (
          <KpiRow>
            <Kpi label="كاميرات متصلة" value={stats.cameras} tone="info" sub={`${stats.camerasWithAi} بتحليل نشط`} />
            <Kpi label="مخالفات PPE اليوم" value={stats.ppeViolationsToday} tone="crit" trend="down" sub={`${stats.unhandled} لم يتم التعامل معها`} />
            <Kpi label="دخول مناطق محظورة" value={stats.restrictedEntries} tone="warn" sub="تم إخطار المشرفين" />
            <Kpi label="دقة النموذج" value={`${stats.modelAccuracy}%`} tone="safe" sub={`False positives: ${stats.falsePositives}%`} />
            <Kpi label="حساسات متصلة" value={stats.sensors} tone="info" sub="غاز · ضوضاء · حرارة" />
            <Kpi label="أجهزة ملبوسة نشطة" value={stats.wearables} tone="hi" sub="الإنتاج والصيانة" />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="الرؤية الحاسوبية — كشف حي">
            <LiveDot label="SIM · CAM-A-07" />
          </CardHead>
          <CardBody>
            <Async state={detections} rows={4}>
              {(d) => (
                <>
                  <div
                    className="relative overflow-hidden rounded-md border border-line"
                    style={{ background: '#0a0f16', aspectRatio: '16/10' }}
                  >
                    <div
                      className="absolute inset-0"
                      style={{
                        backgroundImage:
                          'linear-gradient(rgba(158,27,50,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(158,27,50,.07) 1px,transparent 1px)',
                        backgroundSize: '22px 22px',
                      }}
                    />
                    <div className="absolute top-2 end-2.5 font-mono num text-2xs text-txt-2 z-10">
                      {d.camera} · {d.zone}
                    </div>
                    {d.boxes.map((b) => (
                      <div
                        key={b.id}
                        className="absolute rounded-sm"
                        style={{ ...b.box, border: `2px solid ${b.ok ? '#38B87C' : '#E0483C'}` }}
                      >
                        <span
                          className="absolute -top-[19px] end-0 text-[9.5px] px-1.5 font-mono num whitespace-nowrap rounded-sm"
                          style={{ background: b.ok ? '#38B87C' : '#E0483C', color: b.ok ? '#06180f' : '#fff' }}
                        >
                          {b.label} — {b.confidence}%
                        </span>
                      </div>
                    ))}
                    <div className="absolute bottom-2 end-2 font-mono num text-2xs text-txt-3">
                      {d.boxes.length} أشخاص · {d.boxes.filter((b) => !b.ok).length} مخالفة · معالجة {d.fps} fps
                    </div>
                  </div>

                  <div className="mt-3.5">
                    <Async state={models} rows={7}>
                      {({ models: list }) =>
                        list.map((m) => (
                          <StatLine
                            key={m.model}
                            label={m.model}
                            value={
                              <span className="flex items-center gap-2">
                                <Tag tone={m.state === 'نشط' ? 'g' : undefined}>{m.state}</Tag>
                                <b className="font-mono num">{m.accuracy}%</b>
                              </span>
                            }
                          />
                        ))
                      }
                    </Async>
                  </div>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <div className="flex flex-col gap-3.5">
          <Card>
            <CardHead title="حساسات — قراءات حية">
              <LiveDot />
            </CardHead>
            <CardBody>
              {!sensors ? (
                <div className="text-sm text-txt-3 py-6 text-center">جارٍ الاتصال بمولّد القراءات…</div>
              ) : (
                sensors.map((s) => (
                  <div
                    key={s.id}
                    className="flex items-center gap-3 py-2.5 border-b last:border-b-0"
                    style={{ borderColor: 'rgba(39,64,95,.45)' }}
                  >
                    <span
                      className="w-[34px] h-[34px] rounded-md bg-steel-3 flex items-center justify-center shrink-0"
                      style={{ color: TONE_COLOR[s.tone] }}
                    >
                      <Icon name="sensor" size={17} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-xs truncate">{s.name}</div>
                      <div className="text-2xs text-txt-3 font-mono num">{s.limitLabel}</div>
                    </div>
                    <div className="w-16 hidden sm:block">
                      <Spark values={s.history} color={TONE_COLOR[s.tone]} />
                    </div>
                    <div className="font-mono num font-bold text-[15px] text-end w-20" style={{ color: TONE_COLOR[s.tone] }}>
                      {s.value} <span className="text-2xs font-normal">{s.unit}</span>
                    </div>
                  </div>
                ))
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHead title="سجل التنبيهات">
              <Pill tone="cr">{events?.length ?? 0} تنبيه</Pill>
            </CardHead>
            <CardBody>
              <div className="font-mono num text-xs leading-8 max-h-[280px] overflow-y-auto text-txt-2">
                {(events || []).map((e, i) => (
                  <div key={i} className="whitespace-nowrap">
                    <span className="text-txt-3">{e.at}</span> ·{' '}
                    <b style={{ color: TONE_COLOR[e.tone] }}>{e.code}</b> ·{' '}
                    <span className="text-txt">{e.source}</span> · {e.detail} ·{' '}
                    <span className="text-txt-3">{e.action}</span>
                  </div>
                ))}
              </div>
            </CardBody>
          </Card>
        </div>
      </Grid>

      <Card>
        <CardHead title="الأجهزة الملبوسة" hint="WEARABLE DEVICES" />
        <CardBody>
          <Async state={wearables} rows={4}>
            {(rows) => (
              <div className="grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(215px,1fr))' }}>
                {rows.map((w) => (
                  <div
                    key={w.title}
                    className="bg-steel-3 border border-line rounded-md p-3.5"
                    style={{ borderInlineEndWidth: 4, borderInlineEndColor: w.color }}
                  >
                    <div className="text-[13.5px] font-semibold mb-0.5">{w.title}</div>
                    <div className="text-xs text-txt-3 font-mono num mb-2.5">{w.en}</div>
                    {w.rows.map(([label, value, cls]) => (
                      <div key={label} className="flex justify-between text-xs py-0.5 text-txt-2">
                        <span>{label}</span>
                        <b className={`font-mono num text-txt ${cls}`}>{value}</b>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Async>
        </CardBody>
      </Card>
    </>
  )
}
