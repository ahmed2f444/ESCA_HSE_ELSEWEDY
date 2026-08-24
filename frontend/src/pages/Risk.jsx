import { useState } from 'react'
import {
  Async,
  BarRow,
  Btn,
  Card,
  CardBody,
  CardHead,
  Grid,
  Legend,
  PageHeader,
  Pill,
  StatLine,
  Table,
} from '../components/ui.jsx'
import { RiskMatrix, bandColor, bandLabel } from '../components/charts.jsx'
import { risk as riskApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

export default function Risk() {
  const toast = useToast()
  const [cell, setCell] = useState(null)

  const hazards = useApi(() => riskApi.register(), [])
  const dist = useApi(() => riskApi.distribution(), [])

  const all = hazards.data || []
  const filtered = cell
    ? all.filter((h) => `${h.probability}x${h.severity}` === cell)
    : all

  return (
    <>
      <PageHeader title="تقييم المخاطر" meta="risk assessment register · hira">
        <Btn icon="download" onClick={() => toast('جاري تصدير سجل المخاطر', 'in')}>
          تصدير السجل
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => toast('نموذج التقييم الجديد يفتح بعد ربط خدمة HIRA', 'in')}>
          تقييم جديد
        </Btn>
      </PageHeader>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="مصفوفة المخاطر 5×5" hint="الاحتمالية × الشدة" />
          <CardBody>
            <Async state={hazards} rows={5}>
              {(d) => (
                <>
                  <RiskMatrix hazards={d} selected={cell} onSelect={setCell} />
                  <Legend
                    items={[
                      { label: 'مقبول (1–4)', color: '#38B87C' },
                      { label: 'منخفض (5–9)', color: '#C6C43A' },
                      { label: 'متوسط (10–14)', color: '#F09030' },
                      { label: 'عالي (15–19)', color: '#E0483C' },
                      { label: 'حرج (20–25)', color: '#8E1F17' },
                    ]}
                  />
                  <p className="text-xs text-txt-3 mt-3 leading-7">
                    النقطة الصغيرة في الخانة = عدد المخاطر المسجّلة عندها. اضغط أي خانة لتصفية السجل بالأسفل عليها.
                  </p>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="توزيع المخاطر" hint="RISK REGISTER" />
          <CardBody>
            <Async state={dist} rows={5}>
              {(d) => (
                <>
                  {d.bands.map((b) => (
                    <BarRow key={b.band} label={b.band} value={b.pct} display={b.count} color={b.color} />
                  ))}
                  <div className="mt-5 pt-3.5 border-t border-line">
                    <StatLine label="مخاطر تم تخفيضها هذا العام" value={d.summary.reducedThisYear} valueClass="text-safe" />
                    <StatLine label="مخاطر جديدة تم تحديدها" value={d.summary.newlyIdentified} valueClass="text-warn" />
                    <StatLine label="آخر مراجعة شاملة" value={d.summary.lastFullReview} />
                    <StatLine label="المراجعة القادمة" value={d.summary.nextReview} />
                  </div>
                </>
              )}
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <Card>
        <CardHead title="سجل المخاطر">
          {cell ? (
            <div className="flex items-center gap-2">
              <Pill tone="in">
                مُصفّى على احتمالية {cell.split('x')[0]} × شدة {cell.split('x')[1]}
              </Pill>
              <Btn size="sm" icon="close" onClick={() => setCell(null)}>
                إلغاء التصفية
              </Btn>
            </div>
          ) : (
            <span className="hint">HIRA REGISTER</span>
          )}
        </CardHead>

        <Async state={hazards} rows={8}>
          {() =>
            filtered.length === 0 ? (
              <div className="py-10 text-center text-txt-3 text-sm">
                لا توجد مخاطر مسجّلة عند هذه الدرجة — الخانة فاضية في السجل الحالي
              </div>
            ) : (
              <Table
                head={['الكود', 'المنطقة', 'الخطر', 'النشاط', 'احتمالية', 'شدة', 'الدرجة', 'الضوابط', 'المتبقية', 'المسؤول']}
                clickable={false}
              >
                {filtered.map((h) => {
                  const score = h.probability * h.severity
                  return (
                    <tr key={h.code}>
                      <td className="mono">{h.code}</td>
                      <td>{h.zone}</td>
                      <td>{h.hazard}</td>
                      <td>{h.activity}</td>
                      <td className="mono">{h.probability}</td>
                      <td className="mono">{h.severity}</td>
                      <td>
                        <span
                          className="pill"
                          style={{
                            background: `${bandColor(score)}22`,
                            border: `1px solid ${bandColor(score)}55`,
                            color: bandColor(score),
                          }}
                        >
                          {score} {bandLabel(score)}
                        </span>
                      </td>
                      <td className="text-xs text-txt-2">{h.controls}</td>
                      <td>
                        <Pill tone={h.residual <= 4 ? 'ok' : h.residual <= 9 ? 'in' : 'wn'}>{h.residual}</Pill>
                      </td>
                      <td className="text-xs">{h.owner}</td>
                    </tr>
                  )
                })}
              </Table>
            )
          }
        </Async>
      </Card>
    </>
  )
}
