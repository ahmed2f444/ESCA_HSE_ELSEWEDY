import { useNavigate } from 'react-router-dom'
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
  Legend,
  PageHeader,
  Pill,
  StatLine,
  Timeline,
  TimelineItem,
} from '../components/ui.jsx'
import { MonthlyBars, SafetyPyramid } from '../components/charts.jsx'
import { dashboard } from '../api/endpoints.js'
import { useApi, useCan, useToast } from '../hooks.jsx'
import IncidentForm from './parts/IncidentForm.jsx'
import { useState } from 'react'

const scoreColor = (s) => (s >= 85 ? '#38B87C' : s >= 70 ? '#F09030' : '#E0483C')

export default function Dashboard() {
  const nav = useNavigate()
  const toast = useToast()
  const can = useCan()
  const [reporting, setReporting] = useState(false)

  const summary = useApi(() => dashboard.summary(), [])
  const zones = useApi(() => dashboard.safetyByZone(), [])
  const alerts = useApi(() => dashboard.alerts(), [])
  const trend = useApi(() => dashboard.monthlyTrend(), [])
  const pyramid = useApi(() => dashboard.pyramid(), [])

  const refreshAll = () => {
    ;[summary, zones, alerts, trend, pyramid].forEach((s) => s.reload())
    toast('تم تحديث كل البيانات من الخادم')
  }

  return (
    <>
      <PageHeader title="لوحة قيادة السلامة" meta="real-time overview · all zones">
        <Btn icon="refresh" onClick={refreshAll}>
          تحديث
        </Btn>
        {can.report && (
          <Btn variant="pri" icon="plus" onClick={() => setReporting(true)}>
            تسجيل حادث
          </Btn>
        )}
      </PageHeader>

      <Async state={summary} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="Days Without LTI" value={s.daysWithoutLti} tone="safe" trend="up" sub={`أفضل رقم: ${s.bestStreak} يوم`} />
            <Kpi label="حوادث مفتوحة" value={s.openIncidents} tone="crit" trend="down" sub={`${s.highSeverityOpen} عالية الخطورة`} />
            <Kpi label="إجراءات متأخرة" value={s.overdueActions} tone="warn" sub={`من إجمالي ${s.totalActions} إجراء`} />
            <Kpi label="TRIR" value={s.trir.toFixed(2)} tone="info" trend="up" sub={`${Math.abs(s.trirDelta)} أقل عن 2025`} />
            <Kpi label="جاهزية الطفايات" value={`${s.fireReadiness}%`} tone="safe" sub={`${s.fireOk} من ${s.fireTotal} صالحة`} />
            <Kpi label="الالتزام بالـ PPE" value={`${s.ppeCompliance}%`} tone="hi" sub={`آخر جولة: ${s.lastWalk}`} />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="الأداء الشهري — الحوادث والبلاغات 2026" hint="JAN – AUG" />
          <CardBody>
            <Async state={trend} rows={4}>
              {(d) => (
                <>
                  <MonthlyBars data={d} />
                  <Legend
                    items={[
                      { label: 'حوادث مسجّلة', color: '#E0483C' },
                      { label: 'أشباه حوادث (Near Miss)', color: '#F09030' },
                      { label: 'ملاحظات سلامة', color: '#38B87C' },
                    ]}
                  />
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="مؤشر السلامة حسب المنطقة" hint="SAFETY SCORE" />
          <CardBody>
            <Async state={zones} rows={7}>
              {(d) =>
                d.map((z) => <BarRow key={z.zone} label={z.zone} value={z.score} color={scoreColor(z.score)} />)
              }
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <Grid cols={3}>
        <Card>
          <CardHead title="عداد الأمان" />
          <CardBody className="text-center px-4 py-6">
            <Async state={summary} rows={3}>
              {(s) => (
                <>
                  <div className="font-mono num text-[44px] font-bold text-safe tracking-[-2px] leading-none">
                    {s.daysWithoutLti}
                  </div>
                  <div className="text-sm text-txt-2 mt-2">يوم بدون إصابة مُعطِّلة عن العمل</div>
                  <div className="mt-4 pt-3.5 border-t border-line text-start">
                    <StatLine label="آخر حادث مُعطِّل" value={s.lastLtiDate} />
                    <StatLine label="الرقم القياسي" value={`${s.bestStreak} يوم`} valueClass="text-hi-2" />
                    <StatLine label="ساعات عمل آمنة" value={s.safeManHours.toLocaleString('en-US')} />
                  </div>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="تنبيهات عاجلة">
            <Pill tone="cr">4 عاجل</Pill>
          </CardHead>
          <CardBody>
            <Async state={alerts} rows={5}>
              {(d) => (
                <Timeline>
                  {d.map((a) => (
                    <TimelineItem key={a.title + a.time} time={a.time} color={a.color}>
                      <button className="text-start hover:text-white transition-colors" onClick={() => nav(a.to)}>
                        <b className="font-semibold">{a.title}</b> — {a.body}
                      </button>
                    </TimelineItem>
                  ))}
                </Timeline>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="هرم السلامة (Heinrich)" hint="YTD 2026" />
          <CardBody>
            <Async state={pyramid} rows={5}>
              {(d) => <SafetyPyramid tiers={d} />}
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <IncidentForm
        open={reporting}
        onClose={() => setReporting(false)}
        onCreated={(rec) => {
          toast(`تم تسجيل البلاغ ${rec.id} وإخطار المسؤولين`)
          summary.reload()
        }}
      />
    </>
  )
}
