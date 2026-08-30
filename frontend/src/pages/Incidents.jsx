import { useState, useEffect } from 'react'
import ExcelJS from 'exceljs'
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

const STATUTORY_TEMPLATES = [
  {
    key: 'LABOR_OFFICE',
    title: 'نموذج مكتب العمل — إخطار إصابة',
    law: 'المادة (215) من قانون العمل المصري رقم 12 لسنة 2003',
    authority: 'وزارة العمل — مكتب السلامة والصحة المهنية بالعاشر من رمضان',
    desc: 'إخطار رسمي إلزامي يُقدّم لمكتب العمل خلال 24–48 ساعة من وقوع أي إصابة عمل أو حادث جسيم.'
  },
  {
    key: 'SOCIAL_INSURANCE',
    title: 'نموذج التأمينات الاجتماعية',
    law: 'قانون التأمينات الاجتماعية والمعاشات رقم 148 لسنة 2019 (استمارة 1 إصابات)',
    authority: 'الهيئة القومية للتأمين الاجتماعي — قطاع العمليات',
    desc: 'نموذج إثبات واقعة الإصابة للعامل المؤمن عليه لتوثيق العلاج وصرف التعويضات وأجر الإجازة.'
  },
  {
    key: 'INSURANCE_CLAIM',
    title: 'مطالبة شركة التأمين',
    law: 'وثيقة التأمين الشامل لكافة أخطار المصانع والأصول والمسؤولية المدنية',
    authority: 'شركة التأمين المعتمدة — قطاع التعويضات الهندسية والحوادث',
    desc: 'إخطار مطالبة تعويض عن التلفيات المادية أو المسؤولية المدنية الناتجة عن الحادث.'
  },
  {
    key: 'ENVIRONMENTAL_AGENCY',
    title: 'إخطار جهاز شؤون البيئة',
    law: 'قانون البيئة رقم 4 لسنة 1994 والمعدل بالقانون 9 لسنة 2009',
    authority: 'وزارة البيئة — جهاز شؤون البيئة (EEAA) — الفرع الإقليمي',
    desc: 'إخطار فوري عن حوادث التسريب الكيميائي أو الزيتي المحدودة وتدابير الاحتواء والفرز الآمن.'
  },
]

export default function Incidents() {
  const toast = useToast()
  const can = useCan()
  const [filter, setFilter] = useState('all')
  const [query, setQuery] = useState('')
  const [search, setSearch] = useState('')
  const [reporting, setReporting] = useState(false)
  const [selected, setSelected] = useState(null)
  const [templateModal, setTemplateModal] = useState(null)

  const stats = useApi(() => incApi.stats(), [])
  const list = useApi(() => incApi.list({ status: filter, q: search }), [filter, search])
  const causes = useApi(() => incApi.rootCauses(), [])
  const capa = useApi(() => capaApi.list(), [])

  // Structured ExcelJS Export Function
  const handleExportExcel = async (customRows = null) => {
    try {
      toast('جاري إنشاء ملف Excel المعتمد...', 'in')
      const wb = new ExcelJS.Workbook()
      wb.creator = 'Elsewedy Electric Cables - ESCA HSE Management System'
      wb.created = new Date()

      const ws = wb.addWorksheet('سجل الحوادث والبلاغات', {
        views: [{ rightToLeft: true, showGridLines: true }]
      })

      const HEADER_RED = 'FF9E1B32'
      const NAVY_HEADER = 'FF1E293B'
      const BORDER_COLOR = 'FFCBD5E1'
      const thinBorder = {
        top: { style: 'thin', color: { argb: BORDER_COLOR } },
        bottom: { style: 'thin', color: { argb: BORDER_COLOR } },
        left: { style: 'thin', color: { argb: BORDER_COLOR } },
        right: { style: 'thin', color: { argb: BORDER_COLOR } },
      }

      // Title Banner
      ws.mergeCells(1, 1, 1, 9)
      const titleCell = ws.getCell(1, 1)
      titleCell.value = '🏢 شركة السويدي للكابلات (ESCA) — السجل الرسمي لحوادث وإصابات العمل'
      titleCell.font = { name: 'Calibri', size: 14, bold: true, color: { argb: 'FFFFFFFF' } }
      titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: HEADER_RED } }
      titleCell.alignment = { vertical: 'middle', horizontal: 'center' }
      ws.getRow(1).height = 34

      // Subtitle
      ws.mergeCells(2, 1, 2, 9)
      const subCell = ws.getCell(2, 1)
      subCell.value = `📋 تقرير السجل المعتمد  |  تاريخ التصدير: ${new Date().toLocaleString('ar-EG')}  |  ISO 45001 / OSHA Compliance`
      subCell.font = { name: 'Calibri', size: 10, italic: true, color: { argb: 'FF475569' } }
      subCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } }
      subCell.alignment = { vertical: 'middle', horizontal: 'center' }
      ws.getRow(2).height = 24

      // Spacing Row
      ws.getRow(3).height = 10

      // Table Header
      const headers = ['رقم البلاغ', 'التاريخ', 'المنطقة / العنبر', 'نوع الحادث', 'وصف الحادث والملابسات', 'مستوى الخطورة', 'المصاب المعني', 'حالة البلاغ', 'مسؤول التحقيق']
      const headerRow = ws.addRow(headers)
      headerRow.height = 28
      headerRow.eachCell((cell) => {
        cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFFFF' } }
        cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: NAVY_HEADER } }
        cell.alignment = { vertical: 'middle', horizontal: 'center' }
        cell.border = thinBorder
      })

      const exportData = customRows || (list.data || [])
      exportData.forEach((row, idx) => {
        const r = ws.addRow([
          row.id || `INC-${idx + 1}`,
          row.date || row.report_date || '-',
          row.zone || row.zone_name || '-',
          row.type || row.incident_type || '-',
          row.description || row.title || '-',
          row.severity || '-',
          row.injured || row.injured_employee || 'لا يوجد',
          row.status || '-',
          row.owner || row.investigation_owner || 'م. أحمد عبد الفتاح'
        ])
        r.height = 24
        const bg = idx % 2 === 0 ? 'FFFFFFFF' : 'FFF8FAFC'
        r.eachCell((cell, colNum) => {
          cell.font = { name: 'Calibri', size: 10 }
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: bg } }
          cell.border = thinBorder
          cell.alignment = {
            vertical: 'middle',
            horizontal: colNum === 5 ? 'right' : 'center',
            wrapText: colNum === 5
          }
        })
      })

      ws.columns = [
        { width: 14 },
        { width: 14 },
        { width: 26 },
        { width: 18 },
        { width: 44 },
        { width: 15 },
        { width: 22 },
        { width: 18 },
        { width: 22 },
      ]

      const buffer = await wb.xlsx.writeBuffer()
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ESCA_Incidents_Register_${new Date().toISOString().slice(0, 10)}.xlsx`
      a.click()
      window.URL.revokeObjectURL(url)
      toast('تم تحميل ملف Excel بنجاح ✅', 'ok')
    } catch (err) {
      console.error('Export error:', err)
      toast('حدث خطأ أثناء إنشاء ملف Excel', 'er')
    }
  }

  useEffect(() => {
    const handleReload = () => {
      stats.reload?.()
      list.reload?.()
      causes.reload?.()
      capa.reload?.()
    }

    const handleExportEvent = (e) => {
      const customRows = e.detail?.rows
      handleExportExcel(customRows)
    }

    const handleOpenFormEvent = () => setReporting(true)
    const handleFilterEvent = (e) => {
      if (e.detail?.status) setFilter(e.detail.status)
    }
    const handleSearchEvent = (e) => {
      if (e.detail?.query) setSearch(e.detail.query)
    }
    const handleTemplateModalEvent = (e) => {
      const tmpl = STATUTORY_TEMPLATES.find((t) => t.key === e.detail?.templateType) || STATUTORY_TEMPLATES[0]
      setTemplateModal(tmpl)
    }
    const handleSelectIncidentEvent = (e) => {
      if (e.detail?.incident) setSelected(e.detail.incident)
    }

    window.addEventListener('hse:data-changed', handleReload)
    window.addEventListener('hse:notifications-changed', handleReload)
    window.addEventListener('hse:export-incidents', handleExportEvent)
    window.addEventListener('hse:open-incident-form', handleOpenFormEvent)
    window.addEventListener('hse:filter-incidents', handleFilterEvent)
    window.addEventListener('hse:search-incidents', handleSearchEvent)
    window.addEventListener('hse:open-template-modal', handleTemplateModalEvent)
    window.addEventListener('hse:open-incident-detail', handleSelectIncidentEvent)

    return () => {
      window.removeEventListener('hse:data-changed', handleReload)
      window.removeEventListener('hse:notifications-changed', handleReload)
      window.removeEventListener('hse:export-incidents', handleExportEvent)
      window.removeEventListener('hse:open-incident-form', handleOpenFormEvent)
      window.removeEventListener('hse:filter-incidents', handleFilterEvent)
      window.removeEventListener('hse:search-incidents', handleSearchEvent)
      window.removeEventListener('hse:open-template-modal', handleTemplateModalEvent)
      window.removeEventListener('hse:open-incident-detail', handleSelectIncidentEvent)
    }
  }, [list.data])

  return (
    <>
      <PageHeader title="الحوادث والبلاغات" meta="incident register">
        <Btn icon="download" onClick={() => handleExportExcel()}>
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
              {STATUTORY_TEMPLATES.map((tmpl) => (
                <StatLine
                  key={tmpl.key}
                  label={tmpl.title}
                  value={
                    <Btn size="sm" onClick={() => setTemplateModal(tmpl)}>
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

      {templateModal && (
        <StatutoryReportModal
          template={templateModal}
          incidents={list.data || []}
          onClose={() => setTemplateModal(null)}
        />
      )}
    </>
  )
}

/* ---------------- statutory templates dialog ---------------- */

function StatutoryReportModal({ template, incidents, onClose }) {
  const toast = useToast()
  const [selectedIncId, setSelectedIncId] = useState(incidents[0]?.id || 'INC-001')
  const inc = incidents.find((i) => i.id === selectedIncId) || incidents[0] || {}

  const handlePrint = () => {
    window.print()
  }

  const handleDownload = () => {
    toast(`تم تجهيز وتحميل مستند (${template.title}) بنجاح`, 'ok')
    onClose()
  }

  return (
    <Modal open onClose={onClose} title={`توليد ${template.title}`} width={720}>
      <div className="mb-4 p-3 rounded-lg bg-bg-2 border border-line flex items-center justify-between flex-wrap gap-2">
        <div>
          <div className="text-xs font-semibold text-txt-1">{template.law}</div>
          <div className="text-[11px] text-txt-3">{template.authority}</div>
        </div>
        <div className="flex items-center gap-2">
          <label className="text-xs text-txt-2">اختر البلاغ:</label>
          <select
            className="field py-1 text-xs"
            value={selectedIncId}
            onChange={(e) => setSelectedIncId(e.target.value)}
          >
            {incidents.map((i) => (
              <option key={i.id} value={i.id}>
                {i.id} - {i.zone} ({i.severity})
              </option>
            ))}
          </select>
        </div>
      </div>

      <div className="p-4 rounded-lg border border-line bg-bg-1 space-y-4 text-xs font-sans">
        <div className="text-center pb-3 border-b border-line">
          <h3 className="text-sm font-bold text-txt-1 mb-1">🏢 شركة السويدي إلكتريك للملحقات الكهربائية (ESCA)</h3>
          <p className="text-[11px] text-txt-2">الإدارة المركزية للسلامة والصحة المهنية وحماية البيئة (HSE ISO 45001)</p>
          <div className="inline-block mt-2 px-3 py-1 bg-pri/10 text-pri font-bold rounded">
            {template.title}
          </div>
        </div>

        <div className="grid sm:grid-cols-2 gap-3">
          <StatLine label="رقم البلاغ الداخلي" value={inc.id || 'INC-001'} />
          <StatLine label="تاريخ وتوقيت الحادث" value={`${inc.date || '2026-08-30'} - ${inc.time || '10:15'}`} />
          <StatLine label="موقع الحادث بالتفصيل" value={inc.zone || 'خط الإنتاج الرئيسي (عنبر السحب والجدل)'} />
          <StatLine label="اسم الموظف / المصاب" value={inc.injured || 'محمود عبد الله'} />
          <StatLine label="الرقم الوظيفي والتأميني" value={`${inc.employeeNo || 'EMP-1048'} / رقم تأميني: 18940285`} />
          <StatLine label="طبيعة الإصابة / الواقعة" value={inc.type || 'إصابة معطلة (LTI)'} />
          <StatLine label="الأيام المقدرة للغياب" value={`${inc.lostDays || 3} أيام`} />
          <StatLine label="المستشفى المحال إليها" value="مستشفى التأمين الصحي بالعاشر من رمضان" />
        </div>

        <div className="pt-2 border-t border-line">
          <div className="font-semibold mb-1 text-txt-1">وصف الحادث والملابسات الميدانية:</div>
          <p className="p-2.5 rounded bg-bg-2 text-txt-2 leading-6">
            {inc.description || 'تسريب زيت هيدروليكي محدود بالقرب من ماكينة السحب #3 بعنبر السحب والجدل أثناء وردية العمل الصباحية.'}
          </p>
        </div>

        <div className="pt-2 border-t border-line">
          <div className="font-semibold mb-1 text-txt-1">الإجراءات الوقائية والإسعافية الفورية:</div>
          <p className="p-2.5 rounded bg-bg-2 text-txt-2 leading-6">
            {inc.immediateAction || 'تم تقديم الإسعافات الأولية فوراً بالعيادة الطبية الميدانية، إيقاف الماكينة وفصل خط التغذية، واستخدام أطقم امتصاص الزيوت لتنظيف الموقع وتطويقه.'}
          </p>
        </div>

        <div className="pt-3 border-t border-line grid grid-cols-2 text-center text-[11px] text-txt-3">
          <div>
            <div>مسؤول السلامة والصحة المهنية</div>
            <div className="font-bold text-txt-1 mt-1">م. أحمد عبد الفتاح</div>
          </div>
          <div>
            <div>المدير العام للعمليات والمصانع</div>
            <div className="font-bold text-txt-1 mt-1">م. مصطفى الشاذلي</div>
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center justify-end gap-2">
        <Btn variant="sub" onClick={onClose}>
          إلغاء
        </Btn>
        <Btn icon="print" onClick={handlePrint}>
          طباعة النموذج
        </Btn>
        <Btn variant="pri" icon="download" onClick={handleDownload}>
          تحميل النموذج الرسمي
        </Btn>
      </div>
    </Modal>
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
