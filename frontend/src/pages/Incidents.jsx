import { useState, useEffect } from 'react'
import {
  Async,
  BarRow,
  Btn,
  Card,
  CardBody,
  CardHead,
  Grid,
  Kpi,
  KpiRow,
  PageHeader,
  Pill,
  StatLine,
  Step,
  Table,
  Tag,
} from '../components/ui.jsx'
import Modal from '../components/Modal.jsx'
import Icon from '../components/Icon.jsx'
import IncidentForm from './parts/IncidentForm.jsx'
import { capa as capaApi, incidents as incApi } from '../api/endpoints.js'
import { useApi, useCan, useToast } from '../hooks.jsx'

const FILTERS = [
  { key: 'all', label: 'الكل' },
  { key: 'open', label: 'مفتوح' },
  { key: 'investigating', label: 'تحت التحقيق' },
  { key: 'closed', label: 'مغلق' },
]

const LIFECYCLE = [
  ['Reported', 'in'],
  ['Classified', 'in'],
  ['Investigation', 'wn'],
  ['CAPA Assigned', 'wn'],
  ['Pending Verification', 'in'],
  ['Closed', 'ok'],
]

export default function Incidents() {
  const toast = useToast()
  const can = useCan()
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [reporting, setReporting] = useState(false)
  const [selected, setSelected] = useState(null)

  const stats = useApi(() => incApi.stats(), [])
  const list = useApi(() => incApi.list({ status: filter, q: search }), [filter, search])
  const causes = useApi(() => incApi.rootCauses(), [])
  const capa = useApi(() => capaApi.list(), [])

  useEffect(() => {
    const handleReload = () => {
      stats.reload?.()
      list.reload?.()
      causes.reload?.()
      capa.reload?.()
    }
    window.addEventListener('hse:data-changed', handleReload)
    window.addEventListener('hse:notifications-changed', handleReload)
    return () => {
      window.removeEventListener('hse:data-changed', handleReload)
      window.removeEventListener('hse:notifications-changed', handleReload)
    }
  }, [])

  return (
    <>
      <PageHeader title="الحوادث والبلاغات" meta="incident register">
        <Btn icon="download" onClick={() => toast('جاري تجهيز ملف Excel للتصدير', 'in')}>
          تصدير Excel
        </Btn>
        {can.report && (
          <Btn variant="dgr" icon="incident" onClick={() => setReporting(true)}>
            تسجيل حادث جديد
          </Btn>
        )}
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="إجمالي الحوادث YTD" value={s.ytdTotal} tone="crit" sub={`${s.lti} مُعطِّلة · ${s.firstAid} إسعاف أولي`} />
            <Kpi label="أشباه حوادث" value={s.nearMiss} tone="warn" trend="up" sub="إبلاغ نشط" />
            <Kpi label="أيام ضائعة" value={s.lostDays} tone="info" sub="من حادثين" />
            <Kpi label="متوسط زمن الإغلاق" value={s.avgClosureDays} tone="safe" sub={`يوم / الهدف ≤ ${s.closureTarget}`} />
          </KpiRow>
        )}
      </Async>

      <Card>
        <CardHead title="سجل الحوادث">
          <div className="flex items-center gap-2 flex-wrap">
            <form
              className="relative"
              onSubmit={(e) => {
                e.preventDefault()
                setSearch(query)
              }}
            >
              <Icon name="search" size={13} className="absolute top-1/2 -translate-y-1/2 start-2.5 text-txt-3" />
              <input
                className="field py-1.5 ps-8 w-44 text-xs"
                placeholder="بحث بالرقم أو الوصف…"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
              />
            </form>
            {FILTERS.map((f) => (
              <Btn key={f.key} size="sm" variant={filter === f.key ? 'pri' : undefined} onClick={() => setFilter(f.key)}>
                {f.label}
              </Btn>
            ))}
          </div>
        </CardHead>

        <Async state={list} rows={8}>
          {(rows) =>
            rows.length === 0 ? (
              <div className="py-10 text-center text-txt-3 text-sm">لا توجد بلاغات مطابقة للفلتر</div>
            ) : (
              <Table head={['الرقم', 'التاريخ', 'المنطقة', 'النوع', 'الوصف', 'الخطورة', 'المصاب', 'الحالة', 'المسؤول']}>
                {rows.map((r) => (
                  <tr key={r.id} onClick={() => setSelected(r)}>
                    <td className="mono">{r.id}</td>
                    <td className="mono">{r.date}</td>
                    <td>{r.zone}</td>
                    <td>{r.type}</td>
                    <td className="max-w-[280px]">{r.description}</td>
                    <td>
                      <Pill tone={r.severityTone}>{r.severity}</Pill>
                    </td>
                    <td>{r.injured}</td>
                    <td>
                      <Pill tone={r.statusTone}>{r.status}</Pill>
                    </td>
                    <td>{r.owner}</td>
                  </tr>
                ))}
              </Table>
            )
          }
        </Async>
      </Card>

      <Grid cols={2} className="mt-3.5">
        <Card>
          <CardHead title="تحليل الأسباب الجذرية — YTD" hint="ROOT CAUSE" />
          <CardBody>
            <Async state={causes} rows={6}>
              {(d) => d.map((c) => <BarRow key={c.cause} label={c.cause} value={c.pct} color={c.color} />)}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="الإجراءات التصحيحية (CAPA)" hint="CAPA REGISTER" />
          <Async state={capa} rows={6}>
            {(rows) => (
              <Table head={['الإجراء', 'المسؤول', 'الموعد', 'المصدر', 'الحالة']} clickable={false}>
                {rows.map((c) => (
                  <tr key={c.id}>
                    <td>{c.action}</td>
                    <td>{c.owner}</td>
                    <td className="mono">{c.due}</td>
                    <td className="mono">{c.source}</td>
                    <td>
                      <Pill tone={c.tone}>{c.status}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>
      </Grid>

      <Grid cols={2} className="mt-3.5">
        <Card>
          <CardHead title="دورة حياة البلاغ" hint="INCIDENT LIFECYCLE" />
          <CardBody>
            <div className="flex items-center flex-wrap gap-y-2 text-xs font-mono mb-4">
              {LIFECYCLE.map(([label, tone], i) => (
                <span key={label} className="flex items-center">
                  <Pill tone={tone}>{label}</Pill>
                  {i < LIFECYCLE.length - 1 && <Icon name="chevron" size={13} className="text-txt-3 mx-1" />}
                </span>
              ))}
            </div>
            <p className="text-sm text-txt-2 leading-8 mb-3.5">
              التسجيل الميداني مصمَّم ليتم في <b>أقل من 60 ثانية</b> — 4 حقول إلزامية فقط، والباقي يُستكمل أثناء
              التحقيق. التصنيف النهائي يتحدد حسب الشدة:
            </p>
            <div>
              <Tag tone="g">First Aid</Tag>
              <Tag>Near Miss</Tag>
              <Tag>Property Damage</Tag>
              <Tag tone="r">Lost Time Injury (LTI)</Tag>
              <Tag tone="r">Fatality</Tag>
            </div>
            <div className="mt-4 pt-3.5 border-t border-line">
              <div className="text-[12.5px] font-semibold mb-2">قوالب الإبلاغ الخارجي</div>
              {[
                'نموذج مكتب العمل — إخطار إصابة',
                'نموذج التأمينات الاجتماعية',
                'مطالبة شركة التأمين',
                'إخطار جهاز شؤون البيئة',
              ].map((t) => (
                <StatLine
                  key={t}
                  label={t}
                  value={
                    <Btn size="sm" onClick={() => toast('تم توليد النموذج — جاهز للطباعة')}>
                      توليد
                    </Btn>
                  }
                />
              ))}
            </div>
          </CardBody>
        </Card>

        {/* Follow whichever incident is actually under investigation. */}
        <RcaCard
          incidentId={(list.data || []).find((i) => i.rawStatus === 'INVESTIGATING')?.id || (list.data || [])[0]?.id}
          incidentTitle={(list.data || []).find((i) => i.rawStatus === 'INVESTIGATING')?.description}
        />
      </Grid>

      <IncidentForm
        open={reporting}
        onClose={() => setReporting(false)}
        onCreated={(rec) => {
          toast(`تم تسجيل البلاغ ${rec.id} وإخطار المسؤولين`)
          list.reload()
          stats.reload()
        }}
      />

      <IncidentDetail incident={selected} onClose={() => setSelected(null)} />
    </>
  )
}

/* ---------------- root-cause toolkit ---------------- */

/**
 * Root-cause record for the incident under investigation.
 *
 * The sheets store one RCA row per incident — the method used, the problem
 * statement, the cause category and the root cause — not a step-by-step ladder.
 * So this shows what is actually recorded rather than padding it into five
 * whys that nobody wrote.
 */
function RcaCard({ incidentId, incidentTitle }) {
  const rca = useApi(() => (incidentId ? incApi.rca(incidentId) : Promise.resolve(null)), [incidentId])

  return (
    <Card>
      <CardHead title={`تحليل السبب الجذري — ${incidentId || '—'}`} hint="RCA RECORD" />
      <CardBody>
        <Async state={rca} rows={5}>
          {(d) =>
            !d ? (
              <div className="text-sm text-txt-3 py-8 text-center">
                لم يُسجّل تحليل سبب جذري لهذا البلاغ بعد
              </div>
            ) : (
              <>
                <div className="flex flex-wrap gap-2 mb-3.5">
                  <Pill tone="in">{d.method}</Pill>
                  <Pill tone="nu">{d.category}</Pill>
                  <Pill tone={d.status === 'مكتمل' ? 'ok' : 'wn'}>{d.status}</Pill>
                </div>

                <Step n="P" title="المشكلة">
                  {d.problem || incidentTitle}
                </Step>
                <Step n="R" tone="wn" title="السبب الجذري">
                  <b className="text-crit">{d.rootCause}</b>
                </Step>
                <Step n="C" tone="nu" title="عوامل مساهمة">
                  {d.contributing || '—'}
                </Step>

                <div className="mt-3.5 pt-3 border-t border-line">
                  <StatLine label="أجرى التحليل" value={d.completedBy} />
                  <StatLine label="تاريخ الإنهاء" value={d.completedAt} />
                </div>
              </>
            )
          }
        </Async>
      </CardBody>
    </Card>
  )
}

/* ---------------- detail dialog ---------------- */

function IncidentDetail({ incident, onClose }) {
  if (!incident) return null
  return (
    <Modal open onClose={onClose} title={`تفاصيل البلاغ ${incident.id}`} width={660}>
      <div className="flex flex-wrap gap-2 mb-4">
        <Pill tone={incident.severityTone}>خطورة {incident.severity}</Pill>
        <Pill tone={incident.statusTone}>{incident.status}</Pill>
        <Pill tone="nu">{incident.classification}</Pill>
      </div>

      <p className="text-sm leading-8 mb-4 pb-4 border-b border-line">{incident.description}</p>

      <div className="grid sm:grid-cols-2 gap-x-6">
        <StatLine label="التاريخ والوقت" value={`${incident.date} · ${incident.time}`} />
        <StatLine label="المنطقة" value={incident.zone} />
        <StatLine label="النوع" value={incident.type} />
        <StatLine label="المصاب" value={incident.injured} />
        <StatLine label="الرقم الوظيفي" value={incident.employeeNo} />
        <StatLine label="أيام ضائعة" value={incident.lostDays} valueClass={incident.lostDays ? 'text-crit' : ''} />
        <StatLine label="مسؤول التحقيق" value={incident.owner} />
        <StatLine label="موعد الإنهاء" value={incident.dueDate} />
        <StatLine label="تصريح مرتبط" value={incident.linkedPermit || '—'} />
        <StatLine label="خطر مرتبط بالسجل" value={incident.linkedHazard || '—'} />
      </div>

      <div className="mt-4 pt-4 border-t border-line">
        <div className="text-[12.5px] font-semibold mb-1.5">الإجراء الفوري المتخذ</div>
        <p className="text-xs text-txt-2 leading-8">{incident.immediateAction}</p>
      </div>
    </Modal>
  )
}
