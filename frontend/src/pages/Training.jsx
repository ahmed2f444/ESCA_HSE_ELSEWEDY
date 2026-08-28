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
  MiniBar,
  PageHeader,
  Pill,
  StatLine,
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { training as trainingApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const EMPLOYEES = [
  { id: 1, name: 'محمود عبد الله', dept: 'خط الإنتاج A' },
  { id: 2, name: 'هبة فؤاد', dept: 'خط الإنتاج B' },
  { id: 3, name: 'أحمد سامي', dept: 'ورشة الصيانة الميكانيكية' },
  { id: 4, name: 'كريم رشاد', dept: 'المخازن والخام' },
  { id: 5, name: 'محمد عادل', dept: 'معمل الجودة والاختبارات' },
  { id: 6, name: 'سارة حسن', dept: 'المبنى الإداري' },
  { id: 7, name: 'عمر خالد', dept: 'محطة الكهرباء والمرافق' },
  { id: 8, name: 'نور أحمد', dept: 'منطقة الشحن والتفريغ' },
  { id: 9, name: 'ياسر محمود', dept: 'مخزن المواد الكيميائية' },
  { id: 10, name: 'دينا مصطفى', dept: 'منطقة الخدمات والعيادة' },
]

const COURSES = [
  { id: 1, name: 'السلامة العامة والتعريف بالمخاطر (General Safety Induction)', validityMonths: 12, provider: 'ESCA HSE Academy' },
  { id: 2, name: 'السلامة في العمل الساخن واللحام (Hot Work Safety)', validityMonths: 12, provider: 'Elsewedy Technical Training Center' },
  { id: 3, name: 'إجراءات العزل والقفل وتطبيق بطاقة LOTO', validityMonths: 12, provider: 'External Certified Provider' },
  { id: 4, name: 'السلامة في العمل على الارتفاعات (Work at Height)', validityMonths: 24, provider: 'ESCA HSE Academy' },
  { id: 5, name: 'دخول وتأمين الأماكن المغلقة (Confined Space)', validityMonths: 12, provider: 'Elsewedy Technical Training Center' },
  { id: 6, name: 'مكافحة الحريق واستخدام طفايات الحريق (Fire Fighting)', validityMonths: 12, provider: 'External Certified Provider' },
  { id: 7, name: 'التعامل الآمن مع المواد الكيميائية وGHS', validityMonths: 24, provider: 'ESCA HSE Academy' },
  { id: 8, name: 'الرفع والمناولة اليدوية الميكانيكية (Manual Handling)', validityMonths: 24, provider: 'Elsewedy Technical Training Center' },
  { id: 9, name: 'السلامة الكهربائية وقواطع الجهد المتوسط (Electrical Safety)', validityMonths: 12, provider: 'External Certified Provider' },
  { id: 10, name: 'الإسعافات الأولية والإنعاش القلبي الرئوي (First Aid CPR)', validityMonths: 24, provider: 'Elsewedy Technical Training Center' },
]

const coverageColor = (pct) => (pct >= 90 ? tc.safe() : pct >= 75 ? tc.warn() : tc.crit())

export default function Training() {
  const toast = useToast()
  const stats = useApi(() => trainingApi.stats(), [])
  const programs = useApi(() => trainingApi.programs(), [])
  const expiring = useApi(() => trainingApi.expiring(), [])
  const schedule = useApi(() => trainingApi.schedule(), [])

  // Modals state
  const [scheduleOpen, setScheduleOpen] = useState(false)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [selectedCert, setSelectedCert] = useState(null)

  // Register Training Form
  const [form, setForm] = useState({
    employeeId: 1,
    courseId: 1,
    issueDate: new Date().toISOString().slice(0, 10),
    expiryDate: new Date(Date.now() + 365 * 86400000).toISOString().slice(0, 10),
    provider: 'ESCA HSE Academy',
    evidenceRef: 'CERT-' + Math.floor(1000 + Math.random() * 9000),
  })
  const [submitting, setSubmitting] = useState(false)

  // Schedule Filter State
  const [scheduleSearch, setScheduleSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [courseFilter, setCourseFilter] = useState('ALL')

  const reloadAll = () => {
    stats.reload?.()
    programs.reload?.()
    expiring.reload?.()
    schedule.reload?.()
  }

  const handleCourseChange = (cid) => {
    const course = COURSES.find((c) => c.id === Number(cid))
    const months = course?.validityMonths || 12
    const exp = new Date(Date.now() + months * 30 * 86400000).toISOString().slice(0, 10)
    setForm({
      ...form,
      courseId: Number(cid),
      provider: course?.provider || form.provider,
      expiryDate: exp,
    })
  }

  const handleRegisterTraining = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    try {
      const selectedEmp = EMPLOYEES.find((emp) => emp.id === Number(form.employeeId))
      const selectedCourse = COURSES.find((c) => c.id === Number(form.courseId))

      await trainingApi.register({
        employeeId: Number(form.employeeId),
        employeeName: selectedEmp?.name,
        dept: selectedEmp?.dept,
        courseId: Number(form.courseId),
        courseName: selectedCourse?.name.split('(')[0].trim(),
        provider: form.provider,
        issueDate: form.issueDate,
        expiryDate: form.expiryDate,
        evidenceRef: form.evidenceRef || ('CERT-' + Math.floor(1000 + Math.random() * 9000)),
      })

      toast('تم توثيق واعتماد الشهادة التدريبية بنجاح في مصفوفة الكفاءة', 'ok')
      setRegisterOpen(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر تسجيل الشهادة التدريبية', 'cr')
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
        item.course?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.id?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.dept?.toLowerCase().includes(scheduleSearch.toLowerCase()) ||
        item.provider?.toLowerCase().includes(scheduleSearch.toLowerCase())

      const matchStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'VALID' && item.status.includes('سارية')) ||
        (statusFilter === 'EXPIRED' && item.status.includes('منتهية')) ||
        (statusFilter === 'RENEWAL' && item.status.includes('مجدولة'))

      const matchCourse = courseFilter === 'ALL' || String(item.courseId) === String(courseFilter)

      return matchSearch && matchStatus && matchCourse
    })
  }, [schedule.data, scheduleSearch, statusFilter, courseFilter])

  return (
    <>
      <PageHeader title="التدريب والتأهيل" meta="training & competency matrix">
        <Btn icon="calendar" onClick={() => setScheduleOpen(true)}>
          جدول التدريبات ({Array.isArray(schedule.data) ? schedule.data.length : 12})
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setRegisterOpen(true)}>
          تسجيل دورة تدريبية
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="نسبة التغطية" value={`${s.coverage}%`} tone="safe" sub={`${s.trained} من ${s.headcount} موظف مؤهل`} />
            <Kpi label="شهادات تنتهي هذا الشهر" value={s.expiringThisMonth} tone="warn" sub="تحتاج تجديد وجدولة" />
            <Kpi label="شهادات منتهية" value={s.expired} tone="crit" trend="down" sub="يُمنع دخول المناطق الحرجة" />
            <Kpi
              label="ساعات تدريب YTD"
              value={Number(s.hoursYtd || 4820).toLocaleString('en-US')}
              tone="info"
              sub={`${s.hoursPerEmployee || 12} ساعة / موظف`}
            />
          </KpiRow>
        )}
      </Async>

      <Grid cols={2}>
        <Card>
          <CardHead title="البرامج التدريبية ومصفوفة الجدارات" hint="COMPETENCY MATRIX" />
          <Async state={programs} rows={10}>
            {(rows) => (
              <Table head={['البرنامج', 'الفئة المستهدفة', 'الصلاحية', 'مؤهلون', 'التغطية']} clickable={false}>
                {rows.map((p, idx) => {
                  const pct = Math.min(100, Math.round((p.qualified / p.target) * 100))
                  return (
                    <tr key={p.courseId || idx}>
                      <td className="font-medium text-xs text-txt-1">{p.program}</td>
                      <td className="text-2xs text-txt-2">{p.audience}</td>
                      <td className="text-2xs font-mono">{p.validity}</td>
                      <td className="mono text-xs font-bold text-txt-1">
                        {p.qualified}/{p.target}
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <MiniBar value={pct} color={coverageColor(pct)} width={64} />
                          <span className="font-mono num text-2xs font-bold" style={{ color: coverageColor(pct) }}>
                            {pct}%
                          </span>
                        </div>
                      </td>
                    </tr>
                  )
                })}
              </Table>
            )}
          </Async>
        </Card>

        <Card>
          <CardHead title="شهادات تحتاج تجديد عاجل" hint="URGENT RENEWALS">
            <Pill tone="cr">{(expiring.data || []).length} شهادة</Pill>
          </CardHead>
          <Async state={expiring} rows={10}>
            {(rows) => (
              <Table head={['الموظف', 'الرقم', 'القسم', 'الشهادة', 'تنتهي', 'الحالة']} clickable={false}>
                {rows.map((e, idx) => (
                  <tr key={e.id || idx}>
                    <td className="text-xs font-medium text-txt-1">{e.employee}</td>
                    <td className="mono text-2xs text-txt-3">{e.employeeNo}</td>
                    <td className="text-2xs text-txt-2">{e.dept}</td>
                    <td className="text-xs text-txt-1">{e.certificate}</td>
                    <td className="mono text-2xs font-semibold" style={{ color: e.tone === 'cr' ? tc.crit() : tc.warn() }}>
                      {e.expires}
                    </td>
                    <td>
                      <Pill tone={e.tone}>{e.status}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>
      </Grid>

      <Card className="mt-3.5">
        <CardHead title="قاعدة الحجب التلقائي في نظام تصاريح العمل" hint="COMPETENCY GATE ENFORCEMENT" />
        <CardBody className="text-sm text-txt-2 leading-8">
          الشهادة المنتهية تمنع صاحبها تلقائياً من الظهور في قوائم المُنفِّذين على تصاريح العمل المرتبطة بها —
          فني بشهادة <b className="text-txt-1 font-semibold">LOTO</b> منتهية لا يمكن إضافته على تصريح كهربائي، وفني معتمد بشهادة
          مرتفعات منتهية يُحجب عن تصاريح السقالات. الحجب يتم في طبقة قواعد البيانات عند إصدار التصريح طبقاً لمعايير <b>ISO 45001</b>.
        </CardBody>
      </Card>

      {/* =============================================================== */}
      {/* 1. REGISTER NEW TRAINING / CERTIFICATION MODAL                 */}
      {/* =============================================================== */}
      <Modal
        open={registerOpen}
        onClose={() => setRegisterOpen(false)}
        title="توثيق وتسجيل دورة تدريبية (Register Training / Certification)"
        width={680}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">أكاديمية السويدي للسلامة والصحة المهنية (ESCA HSE Academy)</span>
            <div className="flex gap-2">
              <Btn variant="ghost" onClick={() => setRegisterOpen(false)}>
                إلغاء
              </Btn>
              <Btn variant="pri" icon="check" onClick={handleRegisterTraining} disabled={submitting}>
                {submitting ? 'جاري الحفظ...' : 'توثيق واعتماد الشهادة'}
              </Btn>
            </div>
          </div>
        }
      >
        <form onSubmit={handleRegisterTraining} className="space-y-4">
          <Grid cols={2}>
            <Field label="الموظف المتدرب *">
              <select
                className="field text-xs"
                value={form.employeeId}
                onChange={(e) => setForm({ ...form, employeeId: Number(e.target.value) })}
              >
                {EMPLOYEES.map((emp) => (
                  <option key={emp.id} value={emp.id}>
                    {emp.name} ({emp.dept})
                  </option>
                ))}
              </select>
            </Field>

            <Field label="البرنامج التدريبي المعتمد *">
              <select
                className="field text-xs"
                value={form.courseId}
                onChange={(e) => handleCourseChange(e.target.value)}
              >
                {COURSES.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.name}
                  </option>
                ))}
              </select>
            </Field>
          </Grid>

          <Grid cols={2}>
            <Field label="تاريخ اجتياز التدريب *">
              <input
                type="date"
                className="field text-xs"
                value={form.issueDate}
                onChange={(e) => setForm({ ...form, issueDate: e.target.value })}
              />
            </Field>

            <Field label="تاريخ انتهاء صلاحية الشهادة *">
              <input
                type="date"
                className="field text-xs"
                value={form.expiryDate}
                onChange={(e) => setForm({ ...form, expiryDate: e.target.value })}
              />
            </Field>
          </Grid>

          <Grid cols={2}>
            <Field label="الجهة التدريبية المعتمدة">
              <input
                type="text"
                className="field text-xs"
                value={form.provider}
                onChange={(e) => setForm({ ...form, provider: e.target.value })}
              />
            </Field>

            <Field label="رقم مرجع الشهادة (Certificate Ref)">
              <input
                type="text"
                className="field text-xs font-mono"
                value={form.evidenceRef}
                onChange={(e) => setForm({ ...form, evidenceRef: e.target.value })}
              />
            </Field>
          </Grid>
        </form>
      </Modal>

      {/* =============================================================== */}
      {/* 2. TRAINING SCHEDULE & CERTIFICATION MATRIX MODAL              */}
      {/* =============================================================== */}
      <Modal
        open={scheduleOpen}
        onClose={() => setScheduleOpen(false)}
        title="سجل وجدول التدريبات ومصفوفة الكفاءة (Training Schedule & Matrix)"
        width={920}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">إجمالي الشهادات المعتمدة: {filteredSchedule.length} شهادة</span>
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
                تسجيل دورة جديدة
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
              placeholder="بحث باسم الموظف، الدورة، رقم الشهادة، أو الجهة التدريبية..."
              value={scheduleSearch}
              onChange={(e) => setScheduleSearch(e.target.value)}
            />

            <select
              className="field text-xs w-auto"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="ALL">جميع الحالات</option>
              <option value="VALID">سارية ومعتمدة (VALID)</option>
              <option value="EXPIRED">منتهية الصلاحية (EXPIRED)</option>
              <option value="RENEWAL">مجدولة للتجديد (RENEWAL)</option>
            </select>

            <select
              className="field text-xs w-auto"
              value={courseFilter}
              onChange={(e) => setCourseFilter(e.target.value)}
            >
              <option value="ALL">جميع الدورات</option>
              {COURSES.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.name.split('(')[0]}
                </option>
              ))}
            </select>
          </div>

          {/* Schedule Table */}
          <div className="max-h-96 overflow-y-auto border border-line rounded-lg">
            <Table head={['رقم السجل', 'الموظف', 'القسم/المنطقة', 'الدورة التدريبية', 'تاريخ الإصدار', 'الانتهاء', 'الحالة', 'تفاصيل']}>
              {filteredSchedule.map((row) => (
                <tr key={row.id} className="hover:bg-steel/50 transition-colors">
                  <td className="font-mono text-xs text-txt-1 font-bold">{row.id}</td>
                  <td className="text-xs text-txt-1 font-medium">{row.employee}</td>
                  <td className="text-2xs text-txt-2">{row.dept}</td>
                  <td className="text-xs text-txt-1 font-medium">{row.course}</td>
                  <td className="font-mono text-2xs">{row.issueDate}</td>
                  <td className="font-mono text-2xs">{row.expiryDate}</td>
                  <td>
                    <Pill tone={row.statusTone}>{row.status}</Pill>
                  </td>
                  <td>
                    <Btn
                      size="xs"
                      variant="ghost"
                      onClick={() => {
                        setScheduleOpen(false)
                        setSelectedCert(row)
                      }}
                    >
                      معاينة ↗
                    </Btn>
                  </td>
                </tr>
              ))}
            </Table>
          </div>
        </div>
      </Modal>

      {/* =============================================================== */}
      {/* 3. CERTIFICATE DETAIL MODAL                                     */}
      {/* =============================================================== */}
      {selectedCert && (
        <Modal
          open
          onClose={() => setSelectedCert(null)}
          title={`بيانات الشهادة التدريبية: ${selectedCert.id}`}
          width={600}
          footer={
            <div className="flex items-center justify-between w-full">
              <span className="text-xs text-txt-3">سجل تدريبي موثق ومعتمد</span>
              <Btn variant="ghost" onClick={() => setSelectedCert(null)}>
                إغلاق
              </Btn>
            </div>
          }
        >
          <div className="space-y-3.5">
            <div className="flex items-center justify-between p-3 bg-steel rounded-lg border border-line">
              <div>
                <span className="text-2xs text-txt-3 block">اسم الموظف:</span>
                <span className="text-sm font-bold text-txt-1">{selectedCert.employee}</span>
              </div>
              <Pill tone={selectedCert.statusTone}>{selectedCert.status}</Pill>
            </div>

            <StatLine label="البرنامج التدريبي" value={selectedCert.course} />
            <StatLine label="القسم / منطقة العمل" value={selectedCert.dept} />
            <StatLine label="الجهة المعتمدة المنفذة" value={selectedCert.provider || 'ESCA HSE Academy'} />
            <StatLine label="رقم مرجع الشهادة" value={selectedCert.evidenceRef || 'CERT-N/A'} />
            <StatLine label="تاريخ اجتياز البرنامج" value={selectedCert.issueDate} />
            <StatLine label="تاريخ انتهاء الصلاحية" value={selectedCert.expiryDate} />
          </div>
        </Modal>
      )}
    </>
  )
}
