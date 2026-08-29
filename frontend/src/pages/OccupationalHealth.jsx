import { useState, useMemo } from 'react'
import {
  Async,
  Btn,
  Card,
  CardBody,
  CardHead,
  Field,
  Grid,
  Kpi,
  KpiRow,
  PageHeader,
  Pill,
  StatLine,
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { health as healthApi } from '../api/endpoints.js'
import { getLocalDateString, useApi, useCan, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const EMPLOYEES = [
  'محمود عبد الله (خط الإنتاج A)',
  'هبة فؤاد (خط الإنتاج B)',
  'أحمد سامي (ورشة الصيانة الميكانيكية)',
  'كريم رشاد (المخازن والخام)',
  'محمد عادل (معمل الجودة والاختبارات)',
  'سارة حسن (المبنى الإداري)',
  'عمر خالد (محطة الكهرباء والمرافق)',
  'نور أحمد (منطقة الشحن والتفريغ)',
  'ياسر محمود (مخزن المواد الكيميائية)',
  'دينا مصطفى (منطقة الخدمات والعيادة)',
]

const PROTOCOLS = [
  { id: 1, name: 'فحص قياس السمع الدوري السنوي (Audiometry)', target: 'عمال عنبر السحب والمولدات' },
  { id: 2, name: 'فحص كفاءة وظائف التنفس والرئة (Spirometry)', target: 'عمال خلط البوليمرات والكيماويات' },
  { id: 3, name: 'فحص اللياقة للعمل على الارتفاعات والأماكن المغلقة', target: 'فنيو الصيانة والمقاولون' },
  { id: 4, name: 'الفحص الطبي الشامل الدوري للموظفين', target: 'جميع العاملين بالمصنع' },
  { id: 5, name: 'فحص المناولة اليدوية والإجهاد العضلي (Ergonomics)', target: 'عمال الشحن والتعبئة' },
]

export default function OccupationalHealth() {
  const toast = useToast()
  const stats = useApi(() => healthApi.stats(), [])
  const exams = useApi(() => healthApi.exams(), [])
  const exposure = useApi(() => healthApi.exposure(), [])
  const schedule = useApi(() => healthApi.schedule(), [])

  // Modals state
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [selectedExam, setSelectedExam] = useState(null)

  // Register Exam Form
  const [form, setForm] = useState({
    employeeName: EMPLOYEES[0],
    protocolId: 1,
    scheduledDate: getLocalDateString(new Date()),
    nextDueDate: getLocalDateString(new Date(Date.now() + 180 * 86400000)),
    fitnessResultId: 1,
    restrictions: 'لائق طبياً لممارسة مهام العمل دون قيود',
    doctor: 'د. حازم القاضي (استشاري طب الصناعات)',
  })
  const [submitting, setSubmitting] = useState(false)

  // Schedule Filter State
  const [scheduleSearch, setScheduleSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [protocolFilter, setProtocolFilter] = useState('ALL')

  const reloadAll = () => {
    stats.reload?.()
    exams.reload?.()
    exposure.reload?.()
    schedule.reload?.()
  }

  const handleRegisterExam = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const selectedProtocol = PROTOCOLS.find((p) => p.id === Number(form.protocolId))
      await healthApi.registerExam({
        employeeName: form.employeeName.split(' ')[0] + ' ' + (form.employeeName.split(' ')[1] || ''),
        protocolId: Number(form.protocolId),
        protocolName: selectedProtocol?.name,
        scheduledDate: form.scheduledDate,
        nextDueDate: form.nextDueDate,
        fitnessResultId: Number(form.fitnessResultId),
        restrictions: form.restrictions,
        doctor: form.doctor,
      })

      toast('تم تسجيل وتوثيق الفحص الطبي بنجاح في سجل الصحة المهنية', 'ok')
      setRegisterOpen(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر تسجيل الفحص الطبي', 'cr')
    } finally {
      setSubmitting(false)
    }
  }

  // Filtered Schedule items
  const filteredSchedule = useMemo(() => {
    const rows = Array.isArray(schedule.data) ? schedule.data : []
    return rows.filter((item) => {
      const matchSearch =
        !scheduleSearch ||
        item.employee?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.protocol?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.id?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.doctor?.toLowerCase().includes(scheduleSearch.toLowerCase())

      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'COMPLETED' && item.status === 'مكتمل') ||
        (statusFilter === 'SCHEDULED' && item.status === 'مجدول') ||
        (statusFilter === 'OVERDUE' && item.status === 'متأخر')

      const matchProtocol = protocolFilter === 'ALL' || String(item.protocolId) === String(protocolFilter)

      return matchSearch && matchStatus && matchProtocol
    })
  }, [schedule.data, scheduleSearch, statusFilter, protocolFilter])

  return (
    <>
      <PageHeader title="الصحة المهنية" meta="occupational health · medical surveillance">
        <Btn icon="calendar" onClick={() => setScheduleOpen(true)}>
          جدول الفحوص ({Array.isArray(schedule.data) ? schedule.data.length : 12})
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setRegisterOpen(true)}>
          تسجيل فحص طبي
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="فحوص منفّذة YTD" value={s.examsYtd} tone="safe" sub="حسب خطة المراقبة الطبية" />
            <Kpi label="مستحقة هذا الشهر" value={s.dueThisMonth} tone="warn" sub="تحتاج جدولة ومتابعة" />
            <Kpi label="قيود طبية سارية" value={s.restrictions} tone="info" sub="تُراعى عند توزيع المهام" />
            <Kpi label="حالات تعرّض للضوضاء" value={s.audiometryFlags} tone="crit" sub="تحتاج قياس سمع دوري" />
            <Kpi label="فحوص متأخرة" value={s.overdue} tone="hi" sub="تجاوزت موعدها المحدد" />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2}>
        <Card>
          <CardHead title="خطة الفحوص الطبية" hint="MEDICAL SURVEILLANCE" />
          <Async state={exams} rows={6}>
            {(rows) => (
              <Table head={['نوع الفحص', 'الفئة المستهدفة', 'التكرار', 'منفّذ', 'مستحق']} clickable={false}>
                {rows.map((e, idx) => (
                  <tr key={idx}>
                    <td className="font-medium">{e.type}</td>
                    <td className="text-xs text-txt-2">{e.target}</td>
                    <td className="text-xs font-mono">{e.frequency}</td>
                    <td className="mono text-safe font-bold">{e.done}</td>
                    <td className="mono" style={{ color: e.due > 0 ? tc.warn() : undefined }}>
                      {e.due}
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>

        <Card>
          <CardHead title="قياسات التعرض المهني" hint="EXPOSURE MONITORING" />
          <Async state={exposure} rows={6}>
            {(rows) => (
              <Table head={['العامل الضار', 'المنطقة', 'القياس', 'الحد المسموح', 'الحالة']} clickable={false}>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td className="font-medium">{r.agent}</td>
                    <td className="text-xs text-txt-2">{r.zone}</td>
                    <td className="mono font-semibold" style={{ color: r.tone === 'wn' ? tc.warn() : tc.safe() }}>
                      {r.measured}
                    </td>
                    <td className="text-xs text-txt-3">{r.limit}</td>
                    <td>
                      <Pill tone={r.tone}>{r.tone === 'ok' ? 'ضمن الحد' : 'قرب الحد'}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>
      </Grid>

      <Card className="mt-3.5">
        <CardHead title="نطاق البيانات الطبية في هذا النظام" hint="DATA SCOPE & PRIVACY" />
        <CardBody className="text-sm text-txt-2 leading-8">
          النظام بيسجّل <b className="text-txt-1 font-semibold">نتيجة اللياقة فقط</b> — لائق / لائق بقيود / غير لائق — والتاريخ
          وموعد الفحص القادم. التقارير الطبية التفصيلية والملفات الإكلينيكية مشفرة ومحفوظة بالعيادة الصناعية المعتمدة لضمان
          سرية البيانات الصحية للعاملين طبقاً لمعايير <b>ISO 45001</b> وقانون العمل والسلامة والصحة المهنية.
        </CardBody>
      </Card>

      {/* =============================================================== */}
      {/* 1. REGISTER NEW MEDICAL EXAM MODAL                              */}
      {/* =============================================================== */}
      <Modal
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
        title="تسجيل فحص طبي جديد (Medical Examination Record)"
        width={680}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">العيادة الصناعية — نظام الصحة المهنية ESCA</span>
            <div className="flex gap-2">
              <Btn variant="ghost" onClick={() => setRegisterOpen(false)}>
                إلغاء
              </Btn>
              <Btn variant="pri" icon="check" onClick={handleRegisterExam} disabled={submitting}>
                {submitting ? 'جاري الحفظ...' : 'اعتماد وتسجيل الفحص الطبي'}
              </Btn>
            </div>
          </div>
        }
      >
        <form onSubmit={handleRegisterExam} className="space-y-4">
          <Grid cols={2}>
            <Field label="الموظف الخاضع للفحص *">
              <select
                className="field text-xs"
                value={form.employeeName}
                onChange={(e) => setForm({ ...form, employeeName: e.target.value })}
              >
                {EMPLOYEES.map((emp) => (
                  <option key={emp} value={emp}>
                    {emp}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="بروتوكول الفحص الطبي *">
              <select
                className="field text-xs"
                value={form.protocolId}
                onChange={(e) => setForm({ ...form, protocolId: Number(e.target.value) })}
              >
                {PROTOCOLS.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </Field>
          </Grid>

          <Grid cols={2}>
            <Field label="تاريخ إجراء الفحص *">
              <input
                type="date"
                className="field text-xs"
                value={form.scheduledDate}
                onChange={(e) => setForm({ ...form, scheduledDate: e.target.value })}
              />
            </Field>

            <Field label="موعد الفحص الدوري القادم *">
              <input
                type="date"
                className="field text-xs"
                value={form.nextDueDate}
                onChange={(e) => setForm({ ...form, nextDueDate: e.target.value })}
              />
            </Field>
          </Grid>

          <Grid cols={2}>
            <Field label="نتيجة اللياقة الطبية (Fitness Result) *">
              <select
                className="field text-xs"
                value={form.fitnessResultId}
                onChange={(e) => setForm({ ...form, fitnessResultId: Number(e.target.value) })}
              >
                <option value={1}>✅ لائق طبياً بدون أي قيود (FIT)</option>
                <option value={2}>⚠️ لائق مع قيود تشغيلية محددة (FIT WITH RESTRICTIONS)</option>
                <option value={3}>❌ غير لائق مؤقتاً لممارسة المهام (UNFIT)</option>
              </select>
            </Field>

            <Field label="الطبيب المعالج أو جهة الفحص">
              <input
                type="text"
                className="field text-xs"
                value={form.doctor}
                onChange={(e) => setForm({ ...form, doctor: e.target.value })}
              />
            </Field>
          </Grid>

          <Field label="ملخص القيود والتوصيات التشغيلية (إن وُجدت)">
            <textarea
              rows={3}
              className="field text-xs"
              placeholder="مثال: يمنع العمل على ارتفاعات، يلزم ارتداء سدادات أذن مزدوجة، تجنب رفع أوزان أكثر من 15 كجم..."
              value={form.restrictions}
              onChange={(e) => setForm({ ...form, restrictions: e.target.value })}
            />
          </Field>
        </form>
      </Modal>

      {/* =============================================================== */}
      {/* 2. MEDICAL EXAMINATION SCHEDULE MODAL                           */}
      {/* =============================================================== */}
      <Modal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        title="جدول الفحوصات الطبية والمراقبة الصحية (Medical Exams Schedule)"
        width={900}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">إجمالي السجلات: {filteredSchedule.length} فحص</span>
            <div className="flex gap-2">
              <Btn
                variant="pri"
                size="sm"
                icon="plus"
                onClick={() => {
                  setScheduleOpen(false)
                  setRegisterOpen(true)
                }}
              >
                تسجيل فحص جديد
              </Btn>
              <Btn variant="ghost" size="sm" onClick={() => setScheduleOpen(false)}>
                إغلاق
              </Btn>
            </div>
          </div>
        }
      >
        <div className="space-y-3.5">
          {/* Filter Bar */}
          <div className="flex flex-wrap items-center gap-2 p-2.5 bg-steel rounded-lg border border-line">
            <input
              type="text"
              className="field text-xs flex-1 min-w-[200px]"
              placeholder="بحث باسم الموظف، الفحص، الطبيب، أو رقم السجل..."
              value={scheduleSearch}
              onChange={(e) => setScheduleSearch(e.target.value)}
            />

            <select
              className="field text-xs w-auto"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">جميع الحالات</option>
              <option value="COMPLETED">مكتمل (COMPLETED)</option>
              <option value="SCHEDULED">مجدول (SCHEDULED)</option>
              <option value="OVERDUE">متأخر (OVERDUE)</option>
            </select>

            <select
              className="field text-xs w-auto"
              value={protocolFilter}
              onChange={(e) => setProtocolFilter(e.target.value)}
            >
              <option value="ALL">جميع البروتوكولات</option>
              {PROTOCOLS.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name.split('(')[0]}
                </option>
              ))}
            </select>
          </div>

          {/* Schedule Table */}
          <div className="max-h-96 overflow-y-auto border border-line rounded-lg">
            <Table head={['رقم الفحص', 'الموظف', 'نوع الفحص الطبي', 'التاريخ', 'اللياقة الطبية', 'الطبيب', 'الحالة', 'معاينة']}>
              {filteredSchedule.map((row) => (
                <tr key={row.id} className="hover:bg-steel/50 transition-colors">
                  <td className="font-mono text-xs text-txt-1 font-bold">{row.id}</td>
                  <td className="text-xs text-txt-1 font-medium">{row.employee}</td>
                  <td className="text-xs text-txt-2">{row.protocol}</td>
                  <td className="font-mono text-2xs">{row.scheduledDate}</td>
                  <td>
                    <Pill tone={row.fitnessTone}>{row.fitness}</Pill>
                  </td>
                  <td className="text-xs text-txt-3">{row.doctor}</td>
                  <td>
                    <Pill tone={row.statusTone}>{row.status}</Pill>
                  </td>
                  <td>
                    <Btn
                      size="xs"
                      variant="ghost"
                      onClick={() => {
                        setScheduleOpen(false)
                        setSelectedExam(row)
                      }}
                    >
                      تفاصيل ↗
                    </Btn>
                  </td>
                </tr>
              ))}
            </Table>
          </div>
        </div>
      </Modal>

      {/* =============================================================== */}
      {/* 3. EXAM DETAIL MODAL                                            */}
      {/* =============================================================== */}
      {selectedExam && (
        <Modal
          open
          onClose={() => setSelectedExam(null)}
          title={`تقرير الفحص الطبي: ${selectedExam.id}`}
          width={600}
          footer={
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-txt-3">سجل طبي موثق ومعتمد</span>
              <Btn variant="ghost" onClick={() => setSelectedExam(null)}>
                إغلاق
              </Btn>
            </div>
          }
        >
          <div className="space-y-3.5">
            <div className="flex items-center justify-between p-3 bg-steel rounded-lg border border-line">
              <div>
                <span className="text-2xs text-txt-3 block">اسم الموظف:</span>
                <span className="text-sm font-bold text-txt-1">{selectedExam.employee}</span>
              </div>
              <Pill tone={selectedExam.fitnessTone}>{selectedExam.fitness}</Pill>
            </div>

            <StatLine label="نوع الفحص الطبي" value={selectedExam.protocol} />
            <StatLine label="تاريخ الفحص الطبي" value={selectedExam.scheduledDate} />
            <StatLine label="تاريخ الفحص الدوري القادم" value={selectedExam.nextDueDate} />
            <StatLine label="الطبيب المعتمد" value={selectedExam.doctor} />

            <div className="p-3 bg-steel-2 rounded-lg border border-line mt-3">
              <span className="text-xs font-semibold text-txt-1 block mb-1">القيود والتوصيات التشغيلية:</span>
              <p className="text-xs text-txt-2 leading-relaxed">{selectedExam.restrictions || 'لا توجد قيود'}</p>
            </div>
          </div>
        </Modal>
      )}
    </>
  )
}
