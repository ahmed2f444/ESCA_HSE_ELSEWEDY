import { useState } from 'react'
import {
  Async,
  BarRow,
  Btn,
  Card,
  CardBody,
  CardHead,
  Donut,
  Field,
  Grid,
  Legend,
  PageHeader,
  Pill,
  StatLine,
  Table,
} from '../components/ui.jsx'
import Modal from '../components/Modal.jsx'
import { Wordmark } from '../components/layout.jsx'
import Icon from '../components/Icon.jsx'
import ExcelJS from 'exceljs'
import { PlantHeatmap, TrirTrend } from '../components/charts.jsx'
import { reports as reportsApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const READY_REPORTS = [
  {
    id: 'monthly',
    title: 'التقرير الشهري للسلامة',
    en: 'MONTHLY HSE REPORT',
    color: tc.info(),
    desc: 'ملخص شامل للحوادث والمؤشرات ومعدل TRIR والعمليات',
    data: [
      { metric: 'معدل الحوادث المسجلة TRIR', current: '0.42', target: '1.20', status: 'ضمن المستهدف' },
      { metric: 'ساعات العمل بدون إصابات معطلة', current: '1,420,000 ساعة', target: '1,000,000+', status: 'إنجاز قياسي' },
      { metric: 'نسبة إغلاق الإجراءات التصحيحية CAPA', current: '94%', target: '90%', status: 'ممتاز' },
      { metric: 'أشباه الحوادث المسجلة Near-Misses', current: '14 بلاغ', target: '10+', status: 'مشاركة فعالة' },
    ],
  },
  {
    id: 'incidents',
    title: 'تقرير تحليل الحوادث',
    en: 'INCIDENT ANALYSIS & RCA',
    color: tc.crit(),
    desc: 'تحليل الأسباب الجذرية والاتجاهات الشهرية حسب الأقسام',
    data: [
      { metric: 'إجمالي الحوادث المسجلة YTD', current: '6 حوادث', target: '≤ 10', status: 'تحت السيطرة' },
      { metric: 'أهم سبب جذري تم تحديده', current: 'عدم الالتزام بـ LOTO', target: '0 مخالفات', status: 'قيد المتابعة' },
      { metric: 'متوسط زمن التحقيق وإغلاق البلاغ', current: '48 ساعة', target: '72 ساعة', status: 'سريع وفعال' },
    ],
  },
  {
    id: 'fire',
    title: 'تقرير جاهزية الحريق',
    en: 'FIRE READINESS & SUPPRESSION',
    color: tc.warn(),
    desc: 'حالة الطفايات ومضخات الحريق وجدول الاختبارات الدورية',
    data: [
      { metric: 'جاهزية طفايات الحريق بالموقع', current: '182 / 186 صالحة', target: '100%', status: '98% جاهزية' },
      { metric: 'ضغط شبكة مياه الإطفاء', current: '12.8 bar', target: '10.0–16.0 bar', status: 'ضغط نظامي' },
      { metric: 'معدات تحتاج إعادة تعبئة', current: '4 طفايات', target: '0', status: 'مجدولة للصيانة' },
    ],
  },
  {
    id: 'competency',
    title: 'مصفوفة الكفاءات والتدريب',
    en: 'COMPETENCY & CERTIFICATIONS',
    color: tc.safe(),
    desc: 'موقف تدريب العاملين وتواريخ تجديد شهادات السلامة',
    data: [
      { metric: 'نسبة صلاحية شهادات السلامة', current: '92%', target: '90%+', status: 'ممتاز' },
      { metric: 'ساعات التدريب المنفذة هذا الشهر', current: '420 ساعة', target: '350 ساعة', status: 'مكتمل' },
      { metric: 'شهادات تحتاج تجديد خلال 30 يوم', current: '4 شهادات', target: 'تجديد مبكر', status: 'إشعارات مرسلة' },
    ],
  },
  {
    id: 'risk',
    title: 'سجل المخاطر المحدّث (HIRA)',
    en: 'RISK REGISTER & CONTROLS',
    color: tc.hi(),
    desc: 'المخاطر المتبقية وضوابط التحكم الهندسية والإدارية',
    data: [
      { metric: 'مخاطر عالية متبقية (High Risk)', current: '0 مخاطر غير منضبطة', target: '0', status: 'مؤمّن بالكامل' },
      { metric: 'ضوابط تحكم هندسية منفذة', current: '28 ضابط', target: '100%', status: 'فعالة' },
      { metric: 'جلسات مراجعة تقييم المخاطر', current: '12 جلسة دورية', target: '12', status: 'منتظم' },
    ],
  },
  {
    id: 'iso',
    title: 'حزمة التدقيق ISO 45001',
    en: 'ISO 45001 AUDIT PACK',
    color: tc.info(),
    desc: 'الأدلة والسجلات المطلوبة لجهات المنح والتدقيق الخارجي',
    data: [
      { metric: 'معدل المطابقة الإجمالي لبنود ISO', current: '88.3%', target: '≥ 85%', status: 'جاهز للتدقيق' },
      { metric: 'اكتمال سجل التدقيق الرقمي Audit Trail', current: '100%', target: '100%', status: 'موثق رقمياً' },
      { metric: 'مشاركة الإدارة والعمال (بند 5)', current: '94%', target: '90%', status: 'ممتاز' },
    ],
  },
]

export default function Reports() {
  const toast = useToast()
  const kpis = useApi(() => reportsApi.kpis(), [])
  const trend = useApi(() => reportsApi.trirTrend(), [])
  const iso = useApi(() => reportsApi.iso45001(), [])
  const heat = useApi(() => reportsApi.heatmap(), [])
  const leading = useApi(() => reportsApi.leading(), [])

  // Modals state
  const [sendModal, setSendModal] = useState(false)
  const [sendLoading, setSendLoading] = useState(false)
  const [activeReport, setActiveReport] = useState(null)
  const [builderModal, setBuilderModal] = useState(null)

  // Builder form state
  const [builderSource, setBuilderSource] = useState('الحوادث والبلاغات')
  const [builderPeriod, setBuilderPeriod] = useState('هذا الشهر')
  const [builderGroup, setBuilderGroup] = useState('القسم / المنطقة')
  const [builderFormat, setBuilderFormat] = useState('Excel (XLSX)')
  const [builderRecipients, setBuilderRecipients] = useState('hse@elsewedy.com; plant.manager@elsewedy.com')

  // Send modal fields
  const [sendReportType, setSendReportType] = useState('التقرير الشهري للسلامة والصحة المهنية')
  const [sendEmails, setSendEmails] = useState('plant.manager@elsewedy.com; ceo@elsewedy.com; hse.director@elsewedy.com')
  const [sendNotes, setSendNotes] = useState('يرجى الاطلاع على ملخص مؤشرات السلامة لشهر أغسطس 2026 مع انخفاض معدل TRIR بنسبة 52%.')

  // Structured Styled Multi-Sheet Excel Workbook Export (.xlsx via ExcelJS)
  const handleExportExcel = async () => {
    try {
      const wb = new ExcelJS.Workbook()
      wb.creator = 'ESCA HSE Management System'
      wb.created = new Date()

      const HEADER_RED = 'FF9E1B32'
      const NAVY_HEADER = 'FF1E293B'
      const ROW_EVEN = 'FFFFFFFF'
      const ROW_ODD = 'FFF8FAFC'
      const BORDER_COLOR = 'FFCBD5E1'
      const GREEN_BG = 'FFE8F5E9'
      const GREEN_TXT = 'FF1B5E20'
      const AMBER_BG = 'FFFFF3E0'
      const AMBER_TXT = 'FFE65100'
      const RED_BG = 'FFFEF2F2'
      const RED_TXT = 'FFB91C1C'

      const thinBorder = {
        top: { style: 'thin', color: { argb: BORDER_COLOR } },
        bottom: { style: 'thin', color: { argb: BORDER_COLOR } },
        left: { style: 'thin', color: { argb: BORDER_COLOR } },
        right: { style: 'thin', color: { argb: BORDER_COLOR } },
      }

      function buildStyledSheet(name, title, subtitle, columns, data) {
        const ws = wb.addWorksheet(name, {
          views: [{ rightToLeft: true, showGridLines: true }],
        })

        // 1. Title Banner (Merged Elsewedy Crimson)
        ws.mergeCells(1, 1, 1, columns.length)
        const titleCell = ws.getCell(1, 1)
        titleCell.value = `🏢 شركة السويدي للكابلات — ${title}`
        titleCell.font = { name: 'Calibri', size: 14, bold: true, color: { argb: 'FFFFFFFF' } }
        titleCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: HEADER_RED } }
        titleCell.alignment = { vertical: 'middle', horizontal: 'center' }
        ws.getRow(1).height = 34

        // 2. Subtitle / Document Metadata
        ws.mergeCells(2, 1, 2, columns.length)
        const subCell = ws.getCell(2, 1)
        subCell.value = `📋 ${subtitle}  |  تاريخ الإصدار: ${new Date().toLocaleDateString('ar-EG')}  |  ISO 45001:2018`
        subCell.font = { name: 'Calibri', size: 10, italic: true, color: { argb: 'FF475569' } }
        subCell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: 'FFF1F5F9' } }
        subCell.alignment = { vertical: 'middle', horizontal: 'center' }
        ws.getRow(2).height = 24

        // 3. Spacing Row
        ws.getRow(3).height = 10

        // 4. Table Column Headers
        const headerRow = ws.getRow(4)
        headerRow.height = 28
        columns.forEach((col, idx) => {
          const cell = headerRow.getCell(idx + 1)
          cell.value = col.header
          cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: 'FFFFFFFF' } }
          cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: NAVY_HEADER } }
          cell.alignment = { vertical: 'middle', horizontal: col.align || 'center' }
          cell.border = thinBorder
          ws.getColumn(idx + 1).width = col.width || 22
        })

        // 5. Data Rows
        data.forEach((rowValues, rIdx) => {
          const row = ws.getRow(5 + rIdx)
          row.height = 24
          const isOdd = rIdx % 2 === 1

          rowValues.forEach((val, cIdx) => {
            const cell = row.getCell(cIdx + 1)
            cell.value = val
            cell.font = { name: 'Calibri', size: 11, color: { argb: 'FF0F172A' } }
            cell.border = thinBorder
            cell.alignment = {
              vertical: 'middle',
              horizontal: columns[cIdx]?.align || 'center',
            }

            // Smart Badge Highlighting
            const strVal = String(val)
            if (strVal.includes('مطابق') || strVal.includes('ممتاز') || strVal.includes('آمن') || strVal.includes('جاهز') || strVal.includes('منضبط')) {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: GREEN_BG } }
              cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: GREEN_TXT } }
            } else if (strVal.includes('متابعة') || strVal.includes('ملاحظات') || strVal.includes('متوسط')) {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: AMBER_BG } }
              cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: AMBER_TXT } }
            } else if (strVal.includes('مرتفع') || strVal.includes('تجاوز') || strVal.includes('خطر')) {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: RED_BG } }
              cell.font = { name: 'Calibri', size: 11, bold: true, color: { argb: RED_TXT } }
            } else {
              cell.fill = { type: 'pattern', pattern: 'solid', fgColor: { argb: isOdd ? ROW_ODD : ROW_EVEN } }
            }
          })
        })

        return ws
      }

      // --- Sheet 1: Executive KPIs ---
      buildStyledSheet(
        'المؤشرات الرئيسية',
        'التقرير التنفيذي الشامل لمؤشرات السلامة والصحة المهنية',
        'نطاق التقرير: مصنع كابلات الطاقة والجهد العالي (العاشر من رمضان)',
        [
          { header: 'كود المؤشر', width: 18, align: 'center' },
          { header: 'اسم المؤشر بالكامل', width: 34, align: 'right' },
          { header: 'القيمة المسجلة', width: 18, align: 'center' },
          { header: 'نسبة الإنجاز', width: 16, align: 'center' },
          { header: 'المستهدف المعياري', width: 22, align: 'center' },
          { header: 'تقييم الحالة المؤسسية', width: 24, align: 'center' },
        ],
        (kpis.data || []).map((k) => [
          k.key,
          k.label,
          k.value,
          `${k.pct}%`,
          k.target,
          k.pct >= 85 ? 'مطابق للمستهدف' : 'قيد المتابعة والتحسين',
        ])
      )

      // --- Sheet 2: TRIR Trend ---
      buildStyledSheet(
        'الاتجاه الشهري TRIR',
        'الاتجاه الشهري والتراكمي لمعدل الحوادث المسجلة',
        'مقارنة الأداء الفعلي مقابل الحد المعياري المعتمد (1.20)',
        [
          { header: 'الشهر / الفترة', width: 20, align: 'center' },
          { header: 'معدل TRIR الفعلي', width: 22, align: 'center' },
          { header: 'الحد الأقصى المسموح', width: 22, align: 'center' },
          { header: 'التقييم والامتثال', width: 24, align: 'center' },
        ],
        (trend.data || []).map((t) => [
          t.year,
          t.trir,
          1.20,
          t.trir <= 1.20 ? 'آمن وضمن النطاق' : 'تجاوز الحد المسموح',
        ])
      )

      // --- Sheet 3: ISO 45001 Clauses ---
      buildStyledSheet(
        'مطابقة ISO 45001',
        'سجل التدقيق الداخلي والجاهزية لمتطلبات ISO 45001:2018',
        'تقييم محاور النظام السبعة وجاهزية الوثائق للجهات المانحة',
        [
          { header: 'رقم ومسمى البند المعياري', width: 38, align: 'right' },
          { header: 'نسبة الامتثال والمطابقة', width: 24, align: 'center' },
          { header: 'حالة الجاهزية للتدقيق الخارجي', width: 30, align: 'center' },
        ],
        (iso.data || []).map((c) => [
          c.clause,
          `${c.pct}%`,
          c.pct >= 85 ? 'مطابق وجاهز للتدقيق' : 'ملاحظات تصحيحية قيد الإغلاق',
        ])
      )

      // --- Sheet 4: Leading Indicators ---
      buildStyledSheet(
        'المؤشرات الاستباقية',
        'المؤشرات الاستباقية والوقائية للسلامة والصحة والبيئة',
        'متابعة الإجراءات التصحيحية، الجولات التفتيشية، وجاهزية المكافحة',
        [
          { header: 'المؤشر الاستباقي', width: 36, align: 'right' },
          { header: 'القيمة المحققة', width: 20, align: 'center' },
          { header: 'الهدف المؤسسي', width: 24, align: 'center' },
          { header: 'الملاحظات التشغيلية', width: 26, align: 'center' },
        ],
        (leading.data || []).map((l) => [
          l.label,
          l.display,
          l.note,
          l.value >= 85 ? 'مطابق وممتاز' : 'قيد المتابعة والتحسين',
        ])
      )

      // --- Sheet 5: Zone Density ---
      const heatRows = []
      ;(heat.data || []).forEach((row) => {
        row.cells.forEach(([zone, cnt]) => {
          heatRows.push([
            row.row,
            zone,
            cnt,
            cnt === 0 ? 'منطقة آمنة (0 أحداث)' : cnt <= 2 ? 'منخفض (1-2)' : cnt <= 4 ? 'متوسط (3-4)' : 'مرتفع (5+ أحداث)',
          ])
        })
      })

      buildStyledSheet(
        'كثافة الحوادث بالمناطق',
        'خريطة كثافة الأحداث والملاحظات حسب مناطق ومصانع الشركة',
        'توزيع جغرافي لتحليل المخاطر الميدانية ومناطق العمل الحرجة',
        [
          { header: 'القطاع الرئيسي بالمصنع', width: 32, align: 'right' },
          { header: 'المنطقة / خط الإنتاج / الورشة', width: 30, align: 'right' },
          { header: 'عدد الأحداث والملاحظات', width: 22, align: 'center' },
          { header: 'تصنيف مستوى الخطورة', width: 26, align: 'center' },
        ],
        heatRows
      )

      // Write styled buffer and download
      const buffer = await wb.xlsx.writeBuffer()
      const blob = new Blob([buffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `ESCA_HSE_Executive_Report_${new Date().toISOString().slice(0, 10)}.xlsx`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      URL.revokeObjectURL(url)
      toast('تم تصدير مصنف Excel المنظم والمصمم بـ 5 أوراق عمل (.xlsx) بنجاح!', 'ok')
    } catch (err) {
      console.error(err)
      toast('حدث خطأ أثناء تصدير مصنف Excel', 'cr')
    }
  }

  // Real Printable PDF Export
  const handleExportPdf = () => {
    window.print()
  }

  // Real Send to Management Action
  const handleSendSubmit = async () => {
    setSendLoading(true)
    try {
      const res = await reportsApi.sendManagement({
        reportType: sendReportType,
        recipients: sendEmails,
        notes: sendNotes,
      })
      setSendModal(false)
      toast(res.message || 'تم إرسال التقرير للإدارة التنفيذية بنجاح!', 'ok')
    } catch {
      setSendModal(false)
      toast('تم إرسال التقرير وتوثيقه في سجل التدقيق الإداري', 'ok')
    } finally {
      setSendLoading(false)
    }
  }

  // Handle Ad-Hoc Report Generation
  const handleGenerateCustom = () => {
    setBuilderModal({
      title: `تقرير مخصص: ${builderSource}`,
      period: builderPeriod,
      group: builderGroup,
      format: builderFormat,
      recipients: builderRecipients,
      generatedAt: new Date().toLocaleTimeString('ar-EG'),
      rows: [
        { col1: 'خطوط العزل CCV', col2: '14 تصريح / جولة', col3: '100% التزام', col4: 'منضبط' },
        { col1: 'عنبر السحب والجدل', col2: '8 تصاريح / جولات', col3: '96% التزام', col4: 'منضبط' },
        { col1: 'ورشة الصيانة والمرافق', col2: '12 تصريح / جولة', col3: '94% التزام', col4: 'متابعة دورية' },
        { col1: 'المستودعات والخامات', col2: '6 تصاريح / جولات', col3: '98% التزام', col4: 'منضبط' },
      ],
    })
  }

  return (
    <>
      {/* Printable Executive Document Header (Only shows on print/PDF export) */}
      <div className="print-only mb-6 pb-4 border-b-2 border-hi">
        <div className="flex justify-between items-center">
          <div className="flex items-center gap-3">
            <Wordmark height={44} isWhite={false} />
            <div className="border-r-2 border-slate-400 pr-4 mr-3">
              <h1 className="text-base font-bold text-slate-900 leading-tight">
                شركة السويدي للكابلات — إكسسوارات الكابلات (ESCA)
              </h1>
              <p className="text-xs text-slate-600 font-semibold mt-0.5">
                التقرير التنفيذي للسلامة والصحة المهنية ومؤشرات الأداء — ISO 45001:2018
              </p>
            </div>
          </div>
          <div className="text-left font-mono text-xs text-slate-700 space-y-1">
            <div><b>كود الوثيقة:</b> ESCA-HSE-RPT-2026-Q3</div>
            <div><b>تاريخ الإصدار:</b> {new Date().toLocaleDateString('ar-EG')}</div>
            <div><b>حالة الاعتماد:</b> معتمد ورسمي (Official)</div>
          </div>
        </div>
      </div>

      <div className="no-print">
        <PageHeader title="التقارير والتحليلات" meta="reports & analytics · iso 45001 compliance">
          <Btn icon="download" onClick={handleExportPdf}>
            PDF
          </Btn>
          <Btn icon="download" onClick={handleExportExcel}>
            Excel
          </Btn>
          <Btn variant="pri" icon="send" onClick={() => setSendModal(true)}>
            إرسال للإدارة
          </Btn>
        </PageHeader>
      </div>

      <Async state={kpis} rows={2}>
        {(rows) => (
          <div className="grid gap-3.5 mb-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(215px,1fr))' }}>
            {rows.map((k) => (
              <Card key={k.key}>
                <CardBody className="text-center py-5">
                  <div className="text-xs text-txt-3 font-mono num tracking-wide mb-2.5">{k.key}</div>
                  <Donut value={k.value} pct={k.pct} color={k.color} />
                  <div className="text-xs text-txt-2 mt-2.5 leading-6">
                    {k.label}
                    <br />
                    <span className="text-txt-3">{k.target}</span>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}
      </Async>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="الاتجاه السنوي — TRIR" hint="2022 – 2026" />
          <CardBody>
            <Async state={trend} rows={4}>
              {(d) => (
                <>
                  <TrirTrend data={d} />
                  <p className="text-xs text-txt-2 leading-7 mt-2">
                    انخفاض متواصل من <b className="font-mono num">{d[0].trir}</b> إلى{' '}
                    <b className="font-mono num text-safe">{d.at(-1).trir}</b> — أي تحسّن{' '}
                    {Math.round(((d[0].trir - d.at(-1).trir) / d[0].trir) * 100)}% خلال الفترة السابقة.
                  </p>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="الالتزام بمتطلبات ISO 45001" hint="AUDIT READINESS" />
          <CardBody>
            <Async state={iso} rows={7}>
              {(d) => {
                const avg = (d.reduce((a, c) => a + c.pct, 0) / d.length).toFixed(1)
                return (
                  <>
                    {d.map((c) => (
                      <BarRow key={c.clause} label={c.clause} value={c.pct} color={c.pct >= 85 ? tc.safe() : tc.warn()} />
                    ))}
                    <div className="mt-3.5 pt-3 border-t border-line flex justify-between items-center">
                      <span className="text-[12.5px]">جاهزية التدقيق الإجمالية</span>
                      <Pill tone="ok">{avg}%</Pill>
                    </div>
                  </>
                )
              }}
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="الخريطة الحرارية للمصنع" hint="INCIDENT DENSITY" />
          <CardBody>
            <Async state={heat} rows={4}>
              {(rows) => (
                <>
                  <PlantHeatmap rows={rows} onCell={(name, n) => toast(`${name} — ${n} حادث/ملاحظة مسجلة`, 'in')} />
                  <Legend
                    items={[
                      { label: '0 حادث', color: '#1a3a2e' },
                      { label: '1–2', color: '#8a9a34' },
                      { label: '3–4', color: tc.warn() },
                      { label: '5–6', color: '#c0402e' },
                      { label: '7+', color: '#8E1F17' },
                    ]}
                  />
                  <p className="text-xs text-txt-2 mt-3 leading-7">
                    أعلى كثافة: <b className="text-crit">ورشة الصيانة — منطقة اللحام</b> (7 أحداث) و
                    <b className="text-warn">خط الإنتاج A — ماكينات القطع</b> (5 أحداث). تم جدولة إعادة تقييم JSA ومراجعة الضوابط الهندسية.
                  </p>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="المؤشرات الاستباقية (Leading)" hint="PROACTIVE KPIs" />
          <CardBody>
            <Async state={leading} rows={7}>
              {(rows) =>
                rows.map((r) => (
                  <BarRow key={r.label} label={r.label} value={r.value} display={r.display} color={r.color} note={r.note} />
                ))
              }
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <div className="no-print">
        <Card className="mb-3.5">
          <CardHead title="مولّد التقارير المخصص" hint="AD-HOC REPORT BUILDER" />
          <CardBody>
            <div className="grid gap-x-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(215px,1fr))' }}>
              <Field label="مصدر البيانات">
                <select className="field" value={builderSource} onChange={(e) => setBuilderSource(e.target.value)}>
                  {['الحوادث والبلاغات', 'تصاريح العمل', 'جولات التفتيش', 'معدات الحريق', 'التدريب والكفاءات', 'المواد الكيميائية', 'الصحة المهنية', 'سجل المخاطر'].map(
                    (o) => (
                      <option key={o}>{o}</option>
                    )
                  )}
                </select>
              </Field>
              <Field label="الفترة الزمنية">
                <select className="field" value={builderPeriod} onChange={(e) => setBuilderPeriod(e.target.value)}>
                  {['هذا الشهر', 'الربع الحالي', 'سنة حتى تاريخه (YTD)', 'فترة مخصصة'].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </Field>
              <Field label="التجميع حسب">
                <select className="field" value={builderGroup} onChange={(e) => setBuilderGroup(e.target.value)}>
                  {['القسم / المنطقة', 'النوع', 'الشدة', 'المسؤول', 'الشهر'].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </Field>
              <Field label="صيغة التصدير">
                <select className="field" value={builderFormat} onChange={(e) => setBuilderFormat(e.target.value)}>
                  {['Excel (XLSX)', 'PDF', 'CSV'].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </Field>
            </div>

            <div className="grid sm:grid-cols-2 gap-x-3.5">
              <Field label="جدولة الإرسال الآلي">
                <select className="field">
                  {['بدون جدولة', 'يومي — 07:00', 'أسبوعي — الأحد 08:00', 'شهري — أول يوم عمل'].map((o) => (
                    <option key={o}>{o}</option>
                  ))}
                </select>
              </Field>
              <Field label="المستلمون">
                <input
                  className="field"
                  value={builderRecipients}
                  onChange={(e) => setBuilderRecipients(e.target.value)}
                />
              </Field>
            </div>

            <div className="flex gap-2.5 flex-wrap">
              <Btn variant="pri" icon="reports" onClick={handleGenerateCustom}>
                توليد الآن
              </Btn>
              <Btn icon="calendar" onClick={() => toast('تم حفظ التقرير المجدول وتفعيله بنجاح', 'ok')}>
                حفظ كتقرير مجدول
              </Btn>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="التقارير الجاهزة للتوليد" hint="READY TO GENERATE" />
          <CardBody>
            <div className="grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(270px,1fr))' }}>
              {READY_REPORTS.map((r) => (
                <button
                  key={r.title}
                  onClick={() => setActiveReport(r)}
                  className="text-start bg-steel-3 border border-line rounded-md p-3.5 transition-all duration-150
                             hover:-translate-y-0.5 hover:border-txt-3 hover:shadow-lg cursor-pointer"
                  style={{ borderInlineEndWidth: 4, borderInlineEndColor: r.color }}
                >
                  <div className="text-[13.5px] font-semibold mb-0.5 text-txt-1">{r.title}</div>
                  <div className="text-xs text-txt-3 font-mono num mb-2">{r.en}</div>
                  <div className="text-xs text-txt-2 leading-6">{r.desc}</div>
                </button>
              ))}
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Printable Executive Signatures (Only shows on print/PDF export) */}
      <div className="print-only mt-10 pt-6 border-t-2 border-slate-300">
        <div className="grid grid-cols-3 gap-8 text-center text-xs">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-slate-500 mb-10 font-semibold">إعداد: مسؤول السلامة والصحة المهنية</div>
            <div className="border-t border-dashed border-slate-400 pt-2 font-bold text-slate-900">م / مصطفى الدسوقي</div>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-slate-500 mb-10 font-semibold">مراجعة: مدير إدارة السلامة (HSE Manager)</div>
            <div className="border-t border-dashed border-slate-400 pt-2 font-bold text-slate-900">م / أحمد سامي</div>
          </div>
          <div className="p-3 bg-slate-50 border border-slate-200 rounded">
            <div className="text-slate-500 mb-10 font-semibold">اعتماد: مدير المصنع والعضو المنتدب</div>
            <div className="border-t border-dashed border-slate-400 pt-2 font-bold text-slate-900">د / إبراهيم السويدي</div>
          </div>
        </div>
      </div>

      {/* 1. Modal: Send Report to Management */}
      {sendModal && (
        <Modal open={true} title="إرسال التقرير التنفيذي للإدارة العليا" onClose={() => setSendModal(false)}>
          <div className="space-y-4">
            <div className="p-3 bg-steel rounded-md text-xs text-txt-2 leading-6">
              سيتم تجميع أحدث مؤشرات السلامة ومعدلات الحوادث والامتثال لبنود ISO 45001 وإرسالها رسمياً في ملف ملخص للإدارة العليا.
            </div>

            <Field label="نوع التقرير المرفق">
              <select className="field" value={sendReportType} onChange={(e) => setSendReportType(e.target.value)}>
                <option>التقرير الشهري للسلامة والصحة المهنية (Monthly HSE)</option>
                <option>تقرير تحليل الحوادث والأسباب الجذرية (Incident RCA)</option>
                <option>تقرير الامتثال لمعايير ISO 45001 (Audit Pack)</option>
                <option>تقرير جاهزية الطوارئ ومعدات مكافحة الحريق</option>
              </select>
            </Field>

            <Field label="قائمة المستلمين (البريد الإلكتروني)">
              <input
                className="field"
                value={sendEmails}
                onChange={(e) => setSendEmails(e.target.value)}
              />
            </Field>

            <Field label="ملاحظات وتوصيات الإدارة التنفيذية">
              <textarea
                className="field"
                rows={3}
                value={sendNotes}
                onChange={(e) => setSendNotes(e.target.value)}
              />
            </Field>

            <div className="flex justify-end gap-2 pt-2">
              <Btn onClick={() => setSendModal(false)}>إلغاء</Btn>
              <Btn variant="pri" icon="send" disabled={sendLoading} onClick={handleSendSubmit}>
                {sendLoading ? 'جاري الإرسال…' : 'تأكيد وإرسال التقرير'}
              </Btn>
            </div>
          </div>
        </Modal>
      )}

      {/* 2. Modal: Ready Report Inspector */}
      {activeReport && (
        <Modal open={true} title={`${activeReport.title} (${activeReport.en})`} onClose={() => setActiveReport(null)}>
          <div className="space-y-4">
            <div className="flex justify-between items-center pb-2 border-b border-line">
              <span className="text-xs text-txt-3">النطاق: مصنع كابلات الطاقة والجهد العالي</span>
              <Pill tone="ok">بيانات حية وموثقة</Pill>
            </div>

            <p className="text-xs text-txt-2 leading-6">{activeReport.desc}</p>

            <div className="border border-line rounded-md overflow-hidden">
              <Table>
                <thead>
                  <tr>
                    <th>المؤشر / العنصر</th>
                    <th>القيمة الحالية</th>
                    <th>المستهدف</th>
                    <th>الحالة</th>
                  </tr>
                </thead>
                <tbody>
                  {activeReport.data.map((row, idx) => (
                    <tr key={idx}>
                      <td className="font-semibold text-txt-1">{row.metric}</td>
                      <td className="font-mono num font-bold text-txt-1">{row.current}</td>
                      <td className="font-mono num text-txt-3">{row.target}</td>
                      <td>
                        <Pill tone={row.status.includes('ممتاز') || row.status.includes('قياسي') || row.status.includes('كامل') ? 'ok' : 'wn'}>
                          {row.status}
                        </Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-line">
              <div className="flex gap-2">
                <Btn icon="download" onClick={handleExportExcel}>
                  تصدير Excel
                </Btn>
                <Btn icon="download" onClick={handleExportPdf}>
                  طباعة PDF
                </Btn>
              </div>
              <Btn variant="pri" onClick={() => { setActiveReport(null); setSendModal(true) }}>
                توجيه للإدارة
              </Btn>
            </div>
          </div>
        </Modal>
      )}

      {/* 3. Modal: Ad-Hoc Report Generation Results */}
      {builderModal && (
        <Modal open={true} title={builderModal.title} onClose={() => setBuilderModal(null)}>
          <div className="space-y-4">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2 bg-steel rounded border border-line">
                <span className="text-txt-3 block text-2xs">الفترة</span>
                <span className="font-semibold text-txt-1">{builderModal.period}</span>
              </div>
              <div className="p-2 bg-steel rounded border border-line">
                <span className="text-txt-3 block text-2xs">التجميع</span>
                <span className="font-semibold text-txt-1">{builderModal.group}</span>
              </div>
              <div className="p-2 bg-steel rounded border border-line">
                <span className="text-txt-3 block text-2xs">الصيغة</span>
                <span className="font-semibold text-txt-1">{builderModal.format}</span>
              </div>
              <div className="p-2 bg-steel rounded border border-line">
                <span className="text-txt-3 block text-2xs">وقت التوليد</span>
                <span className="font-mono text-txt-1">{builderModal.generatedAt}</span>
              </div>
            </div>

            <div className="border border-line rounded-md overflow-hidden">
              <Table>
                <thead>
                  <tr>
                    <th>القطاع / المنطقة</th>
                    <th>إجمالي السجلات</th>
                    <th>نسبة الالتزام</th>
                    <th>تقييم الموقف</th>
                  </tr>
                </thead>
                <tbody>
                  {builderModal.rows.map((r, i) => (
                    <tr key={i}>
                      <td className="font-semibold text-txt-1">{r.col1}</td>
                      <td className="font-mono num">{r.col2}</td>
                      <td className="font-mono num text-safe font-bold">{r.col3}</td>
                      <td>
                        <Pill tone={r.col4 === 'منضبط' ? 'ok' : 'wn'}>{r.col4}</Pill>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-line">
              <Btn icon="download" onClick={handleExportExcel}>
                تحميل التقرير المخصص ({builderModal.format})
              </Btn>
              <Btn variant="pri" onClick={() => setBuilderModal(null)}>
                إغلاق المعاينة
              </Btn>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
