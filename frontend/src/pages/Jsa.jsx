import { useState } from 'react'
import {
  Async,
  Btn,
  Card,
  CardBody,
  CardHead,
  Grid,
  Kpi,
  KpiRow,
  PageHeader,
  Pill,
  Table,
} from '../components/ui.jsx'
import { jsa as jsaApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

export default function Jsa() {
  const toast = useToast()
  const [openId, setOpenId] = useState('JSA-018')

  const stats = useApi(() => jsaApi.stats(), [])
  const list = useApi(() => jsaApi.list(), [])
  const detail = useApi(() => jsaApi.byId(openId), [openId])

  return (
    <>
      <PageHeader title="تحليل سلامة المهام (JSA)" meta="job safety analysis · linked to eptw">
        <Btn icon="permit" onClick={() => toast('ربط التحليل بتصريح عمل', 'in')}>
          ربط بتصريح عمل
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => toast('تحليل مهمة جديدة', 'in')}>
          تحليل مهمة جديدة
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="تحليلات معتمدة" value={s.approved} tone="safe" sub={`تغطي ${s.criticalTaskCoverage}% من المهام الحرجة`} />
            <Kpi label="تحتاج مراجعة دورية" value={s.needsReview} tone="warn" sub="مر عليها أكثر من 12 شهر" />
            <Kpi label="مرتبطة بتصاريح" value={s.linkedToPermits} tone="info" sub="إلزامية قبل إصدار PTW" />
            <Kpi label="تغطية المهام الحرجة" value={`${s.criticalTaskCoverage}%`} tone="hi" sub="الهدف 100% بنهاية Q4" />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2}>
        <Card>
          <CardHead title="سجل التحليلات" hint="JSA REGISTER" />
          <Async state={list} rows={8}>
            {(rows) => (
              <Table head={['الكود', 'المهمة', 'المنطقة', 'خطوات', 'حرجة', 'التصريح', 'آخر مراجعة', 'الحالة']}>
                {rows.map((j) => (
                  <tr key={j.id} onClick={() => setOpenId(j.id)} className={openId === j.id ? 'bg-hi/10' : ''}>
                    <td className="mono">{j.id}</td>
                    <td>{j.task}</td>
                    <td className="text-xs text-txt-2">{j.zone}</td>
                    <td className="mono">{j.steps}</td>
                    <td className="mono text-warn">{j.criticalSteps}</td>
                    <td className="text-xs">{j.linkedPermit}</td>
                    <td className="mono">{j.reviewed}</td>
                    <td>
                      <Pill tone={j.tone}>{j.status}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>

        <Card>
          <CardHead title={`تفصيل الخطوات — ${openId}`} hint="STEP / HAZARD / CONTROL" />
          <CardBody>
            <Async state={detail} rows={6}>
              {(d) =>
                !d ? (
                  <div className="text-sm text-txt-3 py-8 text-center">
                    التفاصيل الكاملة لهذا التحليل لم تُدخل بعد — اختر JSA-018 كنموذج مكتمل
                  </div>
                ) : (
                  <>
                    <p className="text-sm mb-3.5 pb-3 border-b border-line">{d.task}</p>
                    <div className="space-y-2.5">
                      {d.steps.map((s, i) => (
                        <div key={i} className="bg-steel-3 border border-line rounded p-3">
                          <div className="flex items-start gap-2.5">
                            <span className="font-mono num text-2xs text-txt-3 mt-0.5 shrink-0">{i + 1}</span>
                            <div className="flex-1">
                              <div className="text-[12.5px] font-medium mb-1.5">{s.step}</div>
                              <div className="grid sm:grid-cols-2 gap-x-4 gap-y-1 text-xs">
                                <div>
                                  <span className="text-crit">الخطر: </span>
                                  <span className="text-txt-2">{s.hazard}</span>
                                </div>
                                <div>
                                  <span className="text-safe">الضابط: </span>
                                  <span className="text-txt-2">{s.control}</span>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                )
              }
            </Async>
          </CardBody>
        </Card>
      </Grid>
    </>
  )
}
