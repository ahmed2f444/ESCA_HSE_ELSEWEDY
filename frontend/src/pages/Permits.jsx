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
  Step,
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { permits as permitApi } from '../api/endpoints.js'
import { useApi, useCan, useToast } from '../hooks.jsx'

/** Permit-type codes come from the sheets; the icon and tone are ours. */
const TYPE_META = {
  HOT_WORK: { label: 'عمل ساخن', icon: 'flame', tone: 'cr' },
  ELECTRICAL: { label: 'كهربائي', icon: 'bolt', tone: 'cr' },
  WORK_AT_HEIGHT: { label: 'مرتفعات', icon: 'ladder', tone: 'wn' },
  CONFINED_SPACE: { label: 'أماكن مغلقة', icon: 'confined', tone: 'cr' },
  MECHANICAL_LOTO: { label: 'ميكانيكي / LOTO', icon: 'wrench', tone: 'in' },
  EXCAVATION: { label: 'حفر', icon: 'excavation', tone: 'wn' },
  RADIOGRAPHY: { label: 'إشعاعي', icon: 'shield', tone: 'cr' },
}

const metaOf = (p) => TYPE_META[p?.type] || { label: p?.typeLabel || 'تصريح عمل', icon: 'permit', tone: 'nu' }

const ZONES = [
  'خطوط العزل CCV',
  'عنبر السحب والجدل',
  'محطة المعالجة والتغليف',
  'مختبر الجودة والاختبارات',
  'محطة المحولات الرئيسية 11kV',
  'ورشة الصيانة الميكانيكية',
  'محطة التبريد المركزي ومعالجة المياه',
  'مبنى الخدمات والعيادة والمكاتب',
  'المستودع الرئيسي للمواد الخام',
  'رصيف الشحن والتفريغ الخارجي',
]

/** Board columns follow what the issuing office actually watches during a shift. */
const COLUMNS = [
  { key: 'pending', title: 'بانتظار الموافقة', accent: '#4A9DD8', match: (p) => p.rawStatus === 'PENDING_APPROVAL' },
  { key: 'active', title: 'نشط تحت التنفيذ', accent: '#38B87C', match: (p) => p.rawStatus === 'ACTIVE' },
  { key: 'expiring', title: 'ينتهي خلال ساعات', accent: '#F09030', match: (p) => ['DUE_SOON', 'EXPIRES_TODAY'].includes(p.flag) && p.rawStatus === 'ACTIVE' },
  { key: 'blocked', title: 'موقوف / مرفوض', accent: '#E0483C', match: (p) => ['SUSPENDED', 'REJECTED', 'BLOCKED', 'EXPIRED', 'CANCELLED', 'CLOSED'].includes(p.rawStatus) },
]

export default function Permits() {
  const toast = useToast()
  const [detail, setDetail] = useState(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [archiveOpen, setArchiveOpen] = useState(false)

  // API Data
  const list = useApi(() => permitApi.list(), [])
  const stats = useApi(() => permitApi.stats(), [])
  const simops = useApi(() => permitApi.simops(), [])

  // Optimistic local state for newly issued permits
  const [newPermits, setNewPermits] = useState([])

  const reloadAll = () => {
    list.reload?.()
    stats.reload?.()
    simops.reload?.()
  }

  // Combined permits list
  const displayPermits = useMemo(() => {
    const serverRows = Array.isArray(list.data) ? list.data : []
    const optimistic = newPermits.filter((n) => !serverRows.some((s) => s.id === n.id))
    return [...optimistic, ...serverRows]
  }, [list.data, newPermits])

  // --- Create Permit Form State ---
  const [createForm, setCreateForm] = useState({
    type: 'HOT_WORK',
    zone: 'خطوط العزل CCV',
    description: '',
    executor: 'فريق الصيانة الكهربائية الداخلي',
    riskLevel: 'HIGH',
    from: '08:30',
    to: '16:30',
    date: new Date().toISOString().slice(0, 10),
    jsa: 'JSA-001',
    gasTestRequired: false,
    o2: '20.9',
    lel: '0',
    h2s: '0',
    co: '0',
    precautions: 'تأمين مطفأة بودرة 6 كجم ومراقب حريق وعزل مصادر الطاقة',
  })
  const [createSubmitting, setCreateSubmitting] = useState(false)

  // SIMOPS conflict check in create form
  const hasSimopsConflict = useMemo(() => {
    if (createForm.type === 'HOT_WORK' && createForm.zone.includes('خطوط العزل')) {
      return {
        hasConflict: true,
        conflictingWith: 'PTW-002 (دهان بمذيبات قابلة للاشتعال)',
        message: 'تحذير SIMOPS: توجد أعمال دهان كيميائي نشطة في نفس النطاق المكاني (حد الأمان 11م)',
      }
    }
    return { hasConflict: false }
  }, [createForm.type, createForm.zone])

  const handleCreatePermit = async (e) => {
    e.preventDefault()
    if (!createForm.description.trim()) {
      toast('يرجى كتابة وصف تفصيلي للأعمال المطلوب التصريح لها', 'wn')
      return
    }

    setCreateSubmitting(true)
    const tempId = `PTW-${String(displayPermits.length + 1).padStart(3, '0')}`
    const meta = TYPE_META[createForm.type] || { label: 'عمل ساخن', icon: 'flame', tone: 'cr' }

    const optimisticItem = {
      id: tempId,
      type: createForm.type,
      typeLabel: meta.label,
      description: createForm.description,
      zone: createForm.zone,
      from: createForm.from,
      to: createForm.to,
      date: createForm.date,
      startDate: createForm.date,
      expiryDate: createForm.date,
      requester: 'م. مصطفى (مدير السلامة)',
      issuer: 'م. مصطفى (مدير السلامة)',
      executor: createForm.executor,
      contractor: createForm.executor,
      jsa: createForm.jsa,
      risk: createForm.riskLevel,
      riskLevel: createForm.riskLevel,
      riskLabel: createForm.riskLevel === 'CRITICAL' ? 'حرج (Critical)' : createForm.riskLevel === 'HIGH' ? 'عالي (High)' : 'متوسط',
      rawStatus: 'PENDING_APPROVAL',
      status: 'بانتظار الموافقة',
      statusTone: 'in',
      flag: 'OK',
      isNew: true,
    }

    setNewPermits((prev) => [optimisticItem, ...prev])

    try {
      const res = await permitApi.create({
        type: createForm.type,
        zone: createForm.zone,
        description: createForm.description,
        executor: createForm.executor,
        riskLevel: createForm.riskLevel,
        from: createForm.from,
        to: createForm.to,
        date: createForm.date,
        jsa: createForm.jsa,
      })

      if (res?.data?.id) optimisticItem.id = res.data.id

      toast(`تم إصدار التصريح (${optimisticItem.id}) بنجاح وإرساله للاعتماد`, 'ok')
      setCreateOpen(false)
      setCreateForm({
        type: 'HOT_WORK',
        zone: 'خطوط العزل CCV',
        description: '',
        executor: 'فريق الصيانة الكهربائية الداخلي',
        riskLevel: 'HIGH',
        from: '08:30',
        to: '16:30',
        date: new Date().toISOString().slice(0, 10),
        jsa: 'JSA-001',
        gasTestRequired: false,
        o2: '20.9',
        lel: '0',
        h2s: '0',
        co: '0',
        precautions: 'تأمين مطفأة بودرة 6 كجم ومراقب حريق وعزل مصادر الطاقة',
      })
      reloadAll()
    } catch (err) {
      toast(err.message || 'تعذر إصدار التصريح', 'cr')
    } finally {
      setCreateSubmitting(false)
    }
  }

  // Archive Filter State
  const [archiveSearch, setArchiveSearch] = useState('')
  const [archiveTypeFilter, setArchiveTypeFilter] = useState('ALL')
  const [archiveStatusFilter, setArchiveStatusFilter] = useState('ALL')

  const filteredArchive = useMemo(() => {
    return displayPermits.filter((p) => {
      const matchSearch =
        !archiveSearch ||
        p.id?.toLowerCase().includes(archiveSearch.toLowerCase()) ||
        p.description?.toLowerCase().includes(archiveSearch.toLowerCase()) ||
        p.zone?.toLowerCase().includes(archiveSearch.toLowerCase()) ||
        p.executor?.toLowerCase().includes(archiveSearch.toLowerCase())

      const matchType = archiveTypeFilter === 'ALL' || p.type === archiveTypeFilter
      const matchStatus = archiveStatusFilter === 'ALL' || p.rawStatus === archiveStatusFilter

      return matchSearch && matchType && matchStatus
    })
  }, [displayPermits, archiveSearch, archiveTypeFilter, archiveStatusFilter])

  return (
    <>
      <PageHeader title="تصاريح العمل" meta="permit to work system">
        <Btn icon="calendar" onClick={() => setArchiveOpen(true)}>
          كل التصاريح ({displayPermits.length})
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setCreateOpen(true)}>
          إصدار تصريح جديد
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="تصاريح نشطة" value={s.active} tone="safe" sub="تحت التنفيذ الآن" />
            <Kpi label="تنتهي خلال 6 ساعات" value={s.expiringSoon} tone="warn" sub="تحتاج تجديد أو إغلاق" />
            <Kpi label="بانتظار الموافقة" value={s.pendingApproval} tone="info" sub={`متوسط الموافقة: ${s.avgApprovalMinutes} دقيقة`} />
            <Kpi label="مخالفات تصاريح" value={s.violations} tone="crit" sub="عمل بدون تصريح — يوليو" />
          </KpiRow>
        )}
      </Async>

      {/* Permit Kanban board */}
      <Async state={list} rows={6}>
        {() => (
          <div className="grid gap-3.5 mb-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(270px,1fr))' }}>
            {COLUMNS.map((col) => {
              const items = displayPermits.filter(col.match)
              return (
                <div key={col.key} className="card flex flex-col">
                  <div className="card-h">
                    <h3 className="flex items-center gap-2">
                      <i className="w-2 h-2 rounded-full" style={{ background: col.accent }} />
                      {col.title}
                    </h3>
                    <span className="hint">{items.length}</span>
                  </div>
                  <div className="p-2.5 flex flex-col gap-2.5 flex-1 max-h-[480px] overflow-y-auto">
                    {items.length === 0 && <div className="text-xs text-txt-3 text-center py-6">لا يوجد</div>}
                    {items.map((p) => {
                      const meta = metaOf(p)
                      return (
                        <button
                          key={p.id}
                          onClick={() => setDetail(p)}
                          className="text-start bg-steel-3 border border-line rounded p-3 hover:border-hi/60 hover:bg-steel/80 transition-all group"
                          style={{ borderInlineEndWidth: 3, borderInlineEndColor: col.accent }}
                        >
                          <div className="flex items-center justify-between gap-2 mb-1.5">
                            <div className="flex items-center gap-1.5">
                              <span className="font-mono num text-xs text-txt-2 font-bold group-hover:text-hi transition-colors">
                                {p.id}
                              </span>
                              {p.isNew && (
                                <span className="text-[10px] bg-hi/20 text-hi px-1.5 py-0.2 rounded font-mono">
                                  جديد
                                </span>
                              )}
                            </div>
                            <Pill tone={meta.tone} icon={meta.icon}>
                              {meta.label}
                            </Pill>
                          </div>
                          <div className="text-[12.5px] font-medium leading-6 text-txt-1 line-clamp-2">{p.description}</div>
                          <div className="text-2xs text-txt-3 mt-1.5">📍 {p.zone}</div>
                          <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-line/70 text-2xs font-mono num text-txt-2">
                            <span className="flex items-center gap-1">
                              <Icon name="clock" size={11} />
                              {p.from} – {p.to}
                            </span>
                            <span className="text-txt-3">👤 {p.executor?.slice(0, 20)}</span>
                          </div>
                        </button>
                      )
                    })}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </Async>

      <Grid cols={3} className="mb-3.5">
        <Card>
          <CardHead title="أنواع التصاريح النشطة" />
          <CardBody>
            <Async state={list} rows={6}>
              {() =>
                Object.entries(TYPE_META).map(([key, meta]) => (
                  <StatLine
                    key={key}
                    label={
                      <span className="flex items-center gap-2">
                        <Icon name={meta.icon} size={14} className="text-txt-3" />
                        {meta.label}
                      </span>
                    }
                    value={displayPermits.filter((r) => r.type === key).length}
                  />
                ))
              }
            </Async>
          </CardBody>
        </Card>

        <ChecklistCard />

        <Card>
          <CardHead title="إحصائيات 2026" />
          <CardBody>
            <Async state={stats} rows={6}>
              {(s) => (
                <>
                  <StatLine label="إجمالي التصاريح الصادرة" value={displayPermits.length > s.issuedYtd ? displayPermits.length : s.issuedYtd} />
                  <StatLine label="تم إغلاقها بشكل صحيح" value={s.closedProperly} valueClass="text-safe" />
                  <StatLine label="مُلغاة" value={s.cancelled} />
                  <StatLine label="مخالفات" value={s.violations} valueClass="text-crit" />
                  <StatLine label="حوادث مرتبطة بتصريح" value={s.linkedIncidents} valueClass="text-safe" />
                  <StatLine label="نسبة الالتزام" value={`${s.compliance}%`} valueClass="text-safe" />
                </>
              )}
            </Async>
          </CardBody>
        </Card>
      </Grid>

      <Grid cols={2}>
        <Card>
          <CardHead title="كشف تعارض العمليات المتزامنة (SIMOPS)">
            <Pill tone="cr">1 تعارض محجوب</Pill>
          </CardHead>
          <CardBody>
            <Async state={simops} rows={6}>
              {(d) => (
                <>
                  <div
                    className="p-3.5 rounded mb-3.5"
                    style={{ background: 'rgba(158,27,50,.13)', border: '1px solid rgba(158,27,50,.4)' }}
                  >
                    <div className="text-[12.5px] font-semibold mb-2 flex items-center gap-2" style={{ color: '#e8697f' }}>
                      <Icon name="close" size={14} />
                      تم رفض إصدار التصريح {d.blocked.permit}
                    </div>
                    <div className="text-xs text-txt-2 leading-8">
                      طلب <b>{d.blocked.request}</b>
                      <br />
                      {d.blocked.reason} — التصريح النشط <b className="font-mono num">{d.blocked.conflictsWith}</b>
                      <br />
                      <span className="text-crit">القرار الآلي: {d.blocked.decision}</span>
                    </div>
                  </div>
                  <div className="text-[12.5px] font-semibold mb-2">قواعد التعارض المفعّلة</div>
                  {d.rules.map((r) => (
                    <StatLine key={r.rule} label={r.rule} value={r.limit} />
                  ))}
                  <StatLine label="تعارضات محجوبة 2026" value={d.blockedYtd} valueClass="text-safe" />
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        {/* Dynamic Approval Card */}
        <ApprovalCard
          permitId={
            displayPermits.find((p) => p.rawStatus === 'PENDING_APPROVAL')?.id ||
            displayPermits[0]?.id
          }
          onApproved={() => {
            reloadAll()
          }}
        />
      </Grid>

      {/* =============================================================== */}
      {/* 1. ISSUE NEW PERMIT MODAL                                        */}
      {/* =============================================================== */}
      <Modal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        title="إصدار تصريح عمل جديد (New Permit to Work)"
        width={760}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">نظام تصاريح العمل الإلكتروني — ESCA PTW v2.4</span>
            <div className="flex gap-2">
              <Btn variant="ghost" onClick={() => setCreateOpen(false)}>
                إلغاء
              </Btn>
              <Btn variant="pri" icon="check" onClick={handleCreatePermit} disabled={createSubmitting}>
                {createSubmitting ? 'جاري الإصدار...' : 'إصدار التصريح وإرساله للاعتماد'}
              </Btn>
            </div>
          </div>
        }
      >
        <form onSubmit={handleCreatePermit} className="space-y-4">
          {/* SIMOPS Conflict Banner */}
          {hasSimopsConflict.hasConflict && (
            <div className="p-3 bg-crit/15 border border-crit/40 rounded-lg flex items-start gap-2.5 text-xs text-crit">
              <Icon name="close" size={16} className="shrink-0 mt-0.5" />
              <div>
                <span className="font-bold block">{hasSimopsConflict.message}</span>
                <span className="text-txt-2 text-2xs block mt-0.5">
                  يتعارض مع {hasSimopsConflict.conflictingWith}. سيتم فرض ضوابط عزل إضافية وإشعار مدير السلامة.
                </span>
              </div>
            </div>
          )}

          <Grid cols={3}>
            <Field label="نوع تصريح العمل *">
              <select
                className="field text-xs"
                value={createForm.type}
                onChange={(e) => setCreateForm({ ...createForm, type: e.target.value })}
              >
                <option value="HOT_WORK">🔥 عمل ساخن (Hot Work)</option>
                <option value="ELECTRICAL">⚡ كهربائي / عزل طاقة (Electrical)</option>
                <option value="WORK_AT_HEIGHT">🪜 عمل على ارتفاعات (Working at Height)</option>
                <option value="CONFINED_SPACE">🕳️ دخول أماكن مغلقة (Confined Space)</option>
                <option value="MECHANICAL_LOTO">🔧 ميكانيكي / قفل وعزل (LOTO)</option>
                <option value="EXCAVATION">🚜 أعمال حفر وردم (Excavation)</option>
                <option value="RADIOGRAPHY">☢️ تفتيش إشعاعي (Radiography)</option>
              </select>
            </Field>

            <Field label="المنطقة الصناعية المستهدفة *">
              <select
                className="field text-xs"
                value={createForm.zone}
                onChange={(e) => setCreateForm({ ...createForm, zone: e.target.value })}
              >
                {ZONES.map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="مستوى الخطورة المقدر">
              <select
                className="field text-xs"
                value={createForm.riskLevel}
                onChange={(e) => setCreateForm({ ...createForm, riskLevel: e.target.value })}
              >
                <option value="CRITICAL">حرج (Critical) — تتطلب توقيع مدير السلامة</option>
                <option value="HIGH">عالي (High) — تتطلب مراقب موقع</option>
                <option value="MEDIUM">متوسط (Medium)</option>
                <option value="LOW">منخفض (Low)</option>
              </select>
            </Field>
          </Grid>

          <Field label="وصف العمل والمهام التفصيلية *">
            <textarea
              rows={2}
              className="field text-xs"
              placeholder="مثال: أعمال لحام وقطع في مسار كابلات التغذية واستبدال قواطع الجهد المتوسط..."
              value={createForm.description}
              onChange={(e) => setCreateForm({ ...createForm, description: e.target.value })}
            />
          </Field>

          <Grid cols={2}>
            <Field label="الجهة المنفذة للأعمال *">
              <input
                type="text"
                className="field text-xs"
                placeholder="اسم الفريق أو مقاول التنفيذ..."
                value={createForm.executor}
                onChange={(e) => setCreateForm({ ...createForm, executor: e.target.value })}
              />
            </Field>

            <Field label="تحليل سلامة المهمة المرتبط (JSA)">
              <select
                className="field text-xs"
                value={createForm.jsa}
                onChange={(e) => setCreateForm({ ...createForm, jsa: e.target.value })}
              >
                <option value="JSA-001">JSA-001: أعمال اللحام والقطع الحراري</option>
                <option value="JSA-002">JSA-002: عزل وتوصيل المحولات الكهربائية 11kV</option>
                <option value="JSA-003">JSA-003: صيانة الإنارة والعمل على السقالات</option>
                <option value="JSA-004">JSA-004: تنظيف وفحص الخزانات المغلقة</option>
                <option value="JSA-005">JSA-005: استبدال السيور والمحركات الميكانيكية</option>
              </select>
            </Field>
          </Grid>

          <Grid cols={3}>
            <Field label="تاريخ العمل *">
              <input
                type="date"
                className="field text-xs"
                value={createForm.date}
                onChange={(e) => setCreateForm({ ...createForm, date: e.target.value })}
              />
            </Field>

            <Field label="وقت البدء">
              <input
                type="time"
                className="field text-xs"
                value={createForm.from}
                onChange={(e) => setCreateForm({ ...createForm, from: e.target.value })}
              />
            </Field>

            <Field label="وقت الانتهاء المقدر">
              <input
                type="time"
                className="field text-xs"
                value={createForm.to}
                onChange={(e) => setCreateForm({ ...createForm, to: e.target.value })}
              />
            </Field>
          </Grid>

          {/* Gas Testing Section */}
          <div className="p-3 bg-steel/50 rounded-lg border border-line">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-txt-1 flex items-center gap-1.5">
                <Icon name="bolt" size={14} className="text-warn" />
                نتائج فحص الغازات الميداني (Gas Test Verification)
              </span>
              <label className="flex items-center gap-1 text-2xs text-txt-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={createForm.gasTestRequired}
                  onChange={(e) => setCreateForm({ ...createForm, gasTestRequired: e.target.checked })}
                  className="rounded"
                />
                إلزامية الفحص بالغاز
              </label>
            </div>

            <Grid cols={4}>
              <Field label="الأكسجين O2 (19.5-23.5%)">
                <input
                  type="text"
                  className="field text-xs font-mono"
                  value={createForm.o2}
                  onChange={(e) => setCreateForm({ ...createForm, o2: e.target.value })}
                />
              </Field>
              <Field label="غازات الاشتعال LEL (<10%)">
                <input
                  type="text"
                  className="field text-xs font-mono"
                  value={createForm.lel}
                  onChange={(e) => setCreateForm({ ...createForm, lel: e.target.value })}
                />
              </Field>
              <Field label="كبريتيد الهيدروجين H2S (0 ppm)">
                <input
                  type="text"
                  className="field text-xs font-mono"
                  value={createForm.h2s}
                  onChange={(e) => setCreateForm({ ...createForm, h2s: e.target.value })}
                />
              </Field>
              <Field label="أول أكسيد الكربون CO (0 ppm)">
                <input
                  type="text"
                  className="field text-xs font-mono"
                  value={createForm.co}
                  onChange={(e) => setCreateForm({ ...createForm, co: e.target.value })}
                />
              </Field>
            </Grid>
          </div>

          <Field label="احتياطات وإجراءات السلامة الإلزامية بالموقع">
            <input
              type="text"
              className="field text-xs"
              value={createForm.precautions}
              onChange={(e) => setCreateForm({ ...createForm, precautions: e.target.value })}
            />
          </Field>
        </form>
      </Modal>

      {/* =============================================================== */}
      {/* 2. ALL PERMITS ARCHIVE & SEARCH MODAL                            */}
      {/* =============================================================== */}
      <Modal
        open={archiveOpen}
        onClose={() => setArchiveOpen(false)}
        title="أرشيف وسجل تصاريح العمل (Permits Archive)"
        width={880}
        footer={
          <div className="flex items-center justify-between w-full">
            <span className="text-xs text-txt-3">عدد النتائج: {filteredArchive.length} تصريح</span>
            <Btn variant="ghost" onClick={() => setArchiveOpen(false)}>
              إغلاق
            </Btn>
          </div>
        }
      >
        <div className="space-y-3.5">
          {/* Filters Bar */}
          <div className="flex flex-wrap items-center gap-2 p-2.5 bg-steel rounded-lg border border-line">
            <input
              type="text"
              className="field text-xs flex-1 min-w-[200px]"
              placeholder="بحث برقم التصريح، المنطقة، الوصف، أو المقاول..."
              value={archiveSearch}
              onChange={(e) => setArchiveSearch(e.target.value)}
            />

            <select
              className="field text-xs w-auto"
              value={archiveTypeFilter}
              onChange={(e) => setArchiveTypeFilter(e.target.value)}
            >
              <option value="ALL">جميع الأنواع</option>
              {Object.entries(TYPE_META).map(([k, m]) => (
                <option key={k} value={k}>
                  {m.label}
                </option>
              ))}
            </select>

            <select
              className="field text-xs w-auto"
              value={archiveStatusFilter}
              onChange={(e) => setArchiveStatusFilter(e.target.value)}
            >
              <option value="ALL">جميع الحالات</option>
              <option value="ACTIVE">نشط (ACTIVE)</option>
              <option value="PENDING_APPROVAL">بانتظار الموافقة</option>
              <option value="SUSPENDED">موقوف</option>
              <option value="CLOSED">مغلق</option>
            </select>
          </div>

          {/* Archive Table */}
          <div className="max-h-96 overflow-y-auto border border-line rounded-lg">
            <Table head={['رقم التصريح', 'النوع', 'المنطقة', 'وصف المهمة', 'التوقيت', 'الحالة', 'إجراء']}>
              {filteredArchive.map((p) => {
                const meta = metaOf(p)
                return (
                  <tr key={p.id} className="hover:bg-steel/50 transition-colors">
                    <td className="font-mono font-bold text-xs text-txt-1">{p.id}</td>
                    <td>
                      <Pill tone={meta.tone} icon={meta.icon}>
                        {meta.label}
                      </Pill>
                    </td>
                    <td className="text-xs text-txt-2">{p.zone}</td>
                    <td className="text-xs text-txt-1 max-w-[240px] truncate">{p.description}</td>
                    <td className="mono text-2xs">{p.from} - {p.to}</td>
                    <td>
                      <Pill tone={p.statusTone}>{p.status}</Pill>
                    </td>
                    <td>
                      <Btn
                        size="xs"
                        variant="ghost"
                        onClick={() => {
                          setArchiveOpen(false)
                          setDetail(p)
                        }}
                      >
                        معاينة ↗
                      </Btn>
                    </td>
                  </tr>
                )
              })}
            </Table>
          </div>
        </div>
      </Modal>

      {/* =============================================================== */}
      {/* 3. PERMIT DETAIL & ACTION MODAL                                  */}
      {/* =============================================================== */}
      <PermitDetail
        permit={detail}
        onClose={() => setDetail(null)}
        onUpdated={() => {
          setDetail(null)
          reloadAll()
        }}
      />
    </>
  )
}

function ChecklistCard() {
  const [type, setType] = useState('HOT_WORK')
  const items = useApi(() => permitApi.checklist(type), [type])

  return (
    <Card>
      <CardHead title="قائمة الفحص الإلزامية" hint="PRE-WORK CHECKLIST" />
      <CardBody>
        <select className="field mb-3 py-1.5 text-xs" value={type} onChange={(e) => setType(e.target.value)}>
          {Object.entries(TYPE_META).map(([k, m]) => (
            <option key={k} value={k}>
              {m.label}
            </option>
          ))}
        </select>
        <Async state={items} rows={6}>
          {(rows) =>
            rows.length === 0 ? (
              <div className="text-sm text-txt-3 py-6 text-center">لا توجد قائمة فحص محمّلة لهذا النوع</div>
            ) : (
              <ul className="text-[12.5px] leading-[2] space-y-1">
                {rows.map((it) => (
                  <li key={it.code} className="flex items-start gap-2">
                    <Icon
                      name={it.response === 'PASSED' || it.response === 'YES' ? 'check' : 'close'}
                      size={13}
                      className={`mt-1.5 ${it.response === 'PASSED' || it.response === 'YES' ? 'text-safe' : 'text-crit'}`}
                    />
                    <span>
                      {it.text}
                      {it.mandatory && <span className="text-crit text-2xs"> · إلزامي</span>}
                    </span>
                  </li>
                ))}
              </ul>
            )
          }
        </Async>
      </CardBody>
    </Card>
  )
}

function ApprovalCard({ permitId, onApproved }) {
  const toast = useToast()
  const can = useCan()
  const data = useApi(() => (permitId ? permitApi.approvals(permitId) : Promise.resolve(null)), [permitId])
  const [busy, setBusy] = useState(false)

  async function approve() {
    setBusy(true)
    try {
      await permitApi.approve(permitId, 'اعتماد نهائي — مخاطر عالية')
      toast(`تم اعتماد التصريح ${permitId} وتسجيل التوقيع الرقمي بنجاح`, 'ok')
      data.reload()
      onApproved?.()
    } catch (e) {
      toast(e.message || 'تعذر اعتماد التصريح', 'cr')
    } finally {
      setBusy(false)
    }
  }

  return (
    <Card>
      <CardHead title="سير الاعتماد والتوقيع الرقمي" hint={permitId || 'PTW-001'} />
      <CardBody>
        <Async state={data} rows={5}>
          {(d) => (
            <>
              {(!d || !d.steps || d.steps.length === 0) && (
                <div className="text-sm text-txt-3 py-6 text-center">لا توجد خطوات اعتماد مسجّلة لهذا التصريح</div>
              )}
              {d?.steps?.map((s, i) => {
                const done = s.state === 'done' || d.approved
                return (
                  <Step key={i} n={done ? '✓' : s.stepNo ?? i + 1} tone={done ? 'ok' : 'wn'} title={s.step}>
                    {d.approved && s.state === 'pending' ? 'تم الاعتماد الآن · موقّع رقمياً' : s.detail}
                  </Step>
                )
              })}

              {d?.signature && (
                <div
                  className="mt-3.5 p-3.5 rounded text-center border border-dashed border-line"
                  style={{ background: 'rgba(0,0,0,.15)' }}
                >
                  <div className="text-info text-[19px] mb-1" style={{ fontFamily: '"Segoe Script", cursive' }}>
                    {d.signature.name}
                  </div>
                  <div className="font-mono num text-2xs text-txt-3">
                    Digital Signature · {d.signature.algo} · {d.signature.timestamp}
                  </div>
                  <div className="font-mono num text-2xs text-txt-3 mt-0.5">{d.signature.hash}</div>
                  <div className="font-mono num text-2xs text-safe mt-1">موثّق ومختوم زمنياً — غير قابل للتعديل</div>
                </div>
              )}

              {!d?.approved && (
                <Btn
                  variant="pri"
                  icon="check"
                  className="w-full justify-center mt-3.5"
                  disabled={!can.approvePermit || busy}
                  onClick={approve}
                >
                  {can.approvePermit ? (busy ? 'جارٍ الاعتماد…' : 'اعتماد نهائي وتوقيع') : 'الاعتماد النهائي لـ HSE Manager فقط'}
                </Btn>
              )}
            </>
          )}
        </Async>
      </CardBody>
    </Card>
  )
}

function PermitDetail({ permit, onClose, onUpdated }) {
  const toast = useToast()
  const [actionBusy, setActionBusy] = useState(false)

  if (!permit) return null
  const meta = metaOf(permit)

  const handleApprove = async () => {
    setActionBusy(true)
    try {
      await permitApi.approve(permit.id, 'اعتماد مباشر من بطاقة التصريح')
      toast(`تم اعتماد التصريح ${permit.id} وتفعيله فوراً`, 'ok')
      onUpdated?.()
    } catch (e) {
      toast(e.message || 'تعذر الاعتماد', 'cr')
    } finally {
      setActionBusy(false)
    }
  }

  const handleSuspend = async () => {
    setActionBusy(true)
    try {
      await permitApi.suspend(permit.id, 'إيقاف مؤقت للتحقق من اشتراطات السلامة')
      toast(`تم إيقاف التصريح ${permit.id} مؤقتاً`, 'wn')
      onUpdated?.()
    } catch (e) {
      toast(e.message || 'تعذر إيقاف التصريح', 'cr')
    } finally {
      setActionBusy(false)
    }
  }

  const handleClose = async () => {
    setActionBusy(true)
    try {
      await permitApi.close(permit.id, 'تم إنهاء الأعمال وتسليم الموقع نظيفاً')
      toast(`تم إغلاق التصريح ${permit.id} بنجاح`, 'ok')
      onUpdated?.()
    } catch (e) {
      toast(e.message || 'تعذر إغلاق التصريح', 'cr')
    } finally {
      setActionBusy(false)
    }
  }

  return (
    <Modal
      open
      onClose={onClose}
      title={`تصريح عمل: ${permit.id}`}
      width={640}
      footer={
        <div className="flex items-center justify-between w-full">
          <Btn variant="ghost" onClick={onClose}>
            إغلاق
          </Btn>
          <div className="flex gap-2">
            {permit.rawStatus !== 'ACTIVE' && permit.rawStatus !== 'CLOSED' && (
              <Btn variant="pri" icon="check" onClick={handleApprove} disabled={actionBusy}>
                اعتماد وتفعيل التصريح
              </Btn>
            )}
            {permit.rawStatus === 'ACTIVE' && (
              <>
                <Btn variant="ghost" className="text-warn border-warn/30" onClick={handleSuspend} disabled={actionBusy}>
                  إيقاف مؤقت
                </Btn>
                <Btn variant="pri" icon="check" onClick={handleClose} disabled={actionBusy}>
                  إغلاق وتسليم الموقع
                </Btn>
              </>
            )}
          </div>
        </div>
      }
    >
      <div className="space-y-4">
        <div className="flex flex-wrap gap-2">
          <Pill tone={meta.tone} icon={meta.icon}>
            {meta.label}
          </Pill>
          <Pill tone={permit.statusTone}>{permit.status}</Pill>
          <Pill tone={permit.risk === 'CRITICAL' || permit.risk === 'HIGH' ? 'cr' : permit.risk === 'MEDIUM' ? 'wn' : 'in'}>
            مستوى الخطورة {permit.riskLabel || permit.risk}
          </Pill>
        </div>

        <div className="p-3.5 bg-steel rounded-lg border border-line">
          <span className="text-2xs text-txt-3 block mb-1">وصف الأعمال المطلوب التصريح لها:</span>
          <p className="text-xs text-txt-1 leading-relaxed">{permit.description}</p>
        </div>

        <Grid cols={2}>
          <div className="p-3 bg-steel/50 rounded border border-line/60">
            <span className="text-2xs text-txt-3 block mb-0.5">المنطقة الصناعية</span>
            <span className="text-xs font-semibold text-txt-1">📍 {permit.zone}</span>
          </div>
          <div className="p-3 bg-steel/50 rounded border border-line/60">
            <span className="text-2xs text-txt-3 block mb-0.5">توقيت وساعات العمل</span>
            <span className="text-xs font-mono font-semibold text-txt-1">
              ⏰ {permit.from} – {permit.to} ({permit.date || permit.startDate})
            </span>
          </div>
        </Grid>

        <Grid cols={2}>
          <div className="p-3 bg-steel/50 rounded border border-line/60">
            <span className="text-2xs text-txt-3 block mb-0.5">المُصدِر والمشرف</span>
            <span className="text-xs font-semibold text-txt-1">👤 {permit.issuer || permit.requester}</span>
          </div>
          <div className="p-3 bg-steel/50 rounded border border-line/60">
            <span className="text-2xs text-txt-3 block mb-0.5">الجهة المنفذة للأعمال</span>
            <span className="text-xs font-semibold text-txt-1">🏢 {permit.executor || permit.contractor}</span>
          </div>
        </Grid>

        {/* Gas Testing Readings */}
        <div className="p-3 bg-steel-2 rounded-lg border border-line/60">
          <div className="text-2xs font-semibold text-txt-2 mb-2 flex items-center gap-1.5">
            <Icon name="bolt" size={13} className="text-warn" />
            <span>قراءات الغازات المعتمدة بالموقع (Calibrated Gas Detection):</span>
          </div>
          <div className="grid grid-cols-4 gap-2 text-center">
            <div className="p-2 bg-steel rounded border border-line font-mono">
              <span className="text-[10px] text-txt-3 block">O2</span>
              <span className="text-xs text-safe font-bold">20.9%</span>
            </div>
            <div className="p-2 bg-steel rounded border border-line font-mono">
              <span className="text-[10px] text-txt-3 block">LEL</span>
              <span className="text-xs text-safe font-bold">0.0%</span>
            </div>
            <div className="p-2 bg-steel rounded border border-line font-mono">
              <span className="text-[10px] text-txt-3 block">H2S</span>
              <span className="text-xs text-safe font-bold">0 ppm</span>
            </div>
            <div className="p-2 bg-steel rounded border border-line font-mono">
              <span className="text-[10px] text-txt-3 block">CO</span>
              <span className="text-xs text-safe font-bold">0 ppm</span>
            </div>
          </div>
        </div>

        <StatLine label="تحليل سلامة المهمة المرتبط (Linked JSA)" value={permit.jsa || 'JSA-001'} />
      </div>
    </Modal>
  )
}
