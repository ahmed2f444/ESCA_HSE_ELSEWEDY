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
import ExcelJS from 'exceljs'
import { RiskMatrix, bandColor, bandLabel } from '../components/charts.jsx'
import RiskForm from './parts/RiskForm.jsx'
import { risk as riskApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

export default function Risk() {
  const toast = useToast()
  const [cell, setCell] = useState(null)

  const hazards = useApi(() => riskApi.register(), [])
  const dist = useApi(() => riskApi.distribution(), [])
  const [formOpen, setFormOpen] = useState(false)

  const all = Array.isArray(hazards.data) ? hazards.data : []
  const filtered = cell
    ? all.filter((h) => `${h?.probability}x${h?.severity}` === cell)
    : all

  const handleExportExcel = async () => {
    try {
      toast('جاري تصدير سجل المخاطر (HIRA) إلى ملف Excel...', 'in')
      const wb = new ExcelJS.Workbook()
      wb.creator = 'ESCA HSE Management System'
      wb.created = new Date()
      
      const ws = wb.addWorksheet('HIRA Register', { views: [{ rightToLeft: true }] })
      
      ws.columns = [
        { header: 'الكود', key: 'code', width: 12 },
        { header: 'المنطقة', key: 'zone', width: 25 },
        { header: 'الخطر', key: 'hazard', width: 35 },
        { header: 'النشاط', key: 'activity', width: 35 },
        { header: 'الاحتمالية', key: 'probability', width: 12 },
        { header: 'الشدة', key: 'severity', width: 10 },
        { header: 'الدرجة الكلية', key: 'score', width: 15 },
        { header: 'مستوى الخطر', key: 'level', width: 15 },
        { header: 'ضوابط التحكم', key: 'controls', width: 45 },
        { header: 'المخاطر المتبقية', key: 'residual', width: 15 },
        { header: 'المسؤول', key: 'owner', width: 25 },
      ]

      ws.getRow(1).font = { bold: true, color: { argb: 'FFFFFFFF' } }
      ws.getRow(1).fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FF1F2937' } }

      all.forEach((row) => {
        const score = (row.probability || 0) * (row.severity || 0)
        ws.addRow({
          code: row.code || '-',
          zone: row.zone || '-',
          hazard: row.hazard || '-',
          activity: row.activity || '-',
          probability: row.probability || 0,
          severity: row.severity || 0,
          score: score,
          level: row.level || bandLabel(score),
          controls: row.controls || '-',
          residual: row.residual || 0,
          owner: row.owner || '-',
        })
      })

      const buf = await wb.xlsx.writeBuffer()
      const blob = new Blob([buf], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `Risk_Register_HIRA_${new Date().toISOString().split('T')[0]}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
      toast('تم تصدير سجل المخاطر بنجاح.', 'ok')
    } catch (err) {
      console.error('Export error:', err)
      toast('حدث خطأ أثناء تصدير سجل المخاطر إلى Excel', 'cr')
    }
  }

  return (
    <>
      <PageHeader title="تقييم المخاطر" meta="risk assessment register · hira">
        <Btn icon="download" onClick={handleExportExcel}>
          تصدير السجل
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setFormOpen(true)}>
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
                      { label: 'مقبول (1–4)', color: tc.safe() },
                      { label: 'منخفض (5–9)', color: '#C6C43A' },
                      { label: 'متوسط (10–14)', color: tc.warn() },
                      { label: 'عالي (15–19)', color: tc.crit() },
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
                {filtered.map((h, idx) => {
                  const prob = Number(h?.probability) || 1
                  const sev = Number(h?.severity) || 1
                  const score = Number(h?.score) || (prob * sev)
                  const code = h?.code || `RSK-${idx + 1}`
                  const residual = Number(h?.residual) || 1
                  return (
                    <tr key={code}>
                      <td className="mono">{code}</td>
                      <td>{h?.zone || '-'}</td>
                      <td>{h?.hazard || '-'}</td>
                      <td>{h?.activity || '-'}</td>
                      <td className="mono">{prob}</td>
                      <td className="mono">{sev}</td>
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
                      <td className="text-xs text-txt-2">{h?.controls || '-'}</td>
                      <td>
                        <Pill tone={residual <= 4 ? 'ok' : residual <= 9 ? 'in' : 'wn'}>{residual}</Pill>
                      </td>
                      <td className="text-xs">{h?.owner || '-'}</td>
                    </tr>
                  )
                })}
              </Table>
            )
          }
        </Async>
      </Card>

      <RiskForm 
        open={formOpen} 
        onClose={() => setFormOpen(false)} 
        onSuccess={() => {
          hazards.reload?.()
          dist.reload?.()
        }} 
      />
    </>
  )
}
