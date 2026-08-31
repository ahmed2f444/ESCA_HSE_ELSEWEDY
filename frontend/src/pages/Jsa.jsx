import { useState, useMemo, useEffect } from 'react'
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
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { jsa as jsaApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

const ZONES = [
  'خطوط العزل CCV',
  'عنبر السحب والجدل',
  'محطة المعالجة والتغليف',
  'مختبر الجودة والاختبارات',
  'محطة المحولات الرئيسية 11kV',
  'ورشة الصيانة الميكانيكية',
  'محطة التبريد المركزي ومعالجة المياه',
  'المستودع الرئيسي للمواد الخام',
  'المبنى الإداري والخدمات',
  'رصيف الشحن والتفريغ الخارجي',
]

const PERMIT_TYPES = [
  { value: 'HOT_WORK', label: 'عمل ساخن (Hot Work)' },
  { value: 'ELECTRICAL', label: 'كهربائي (Electrical Isolation)' },
  { value: 'WORK_AT_HEIGHT', label: 'مرتفعات (Working at Height)' },
  { value: 'CONFINED_SPACE', label: 'أماكن مغلقة (Confined Space)' },
  { value: 'MECHANICAL_LOTO', label: 'ميكانيكي / LOTO' },
  { value: 'EXCAVATION', label: 'حفر وأعمال مدنية (Excavation)' },
  { value: 'RADIOGRAPHY', label: 'إشعاعي وتصوير صناعي (Radiography)' },
]

const FREQUENCIES = [
  { value: 'AS_NEEDED', label: 'عند الحاجة (As Needed)' },
  { value: 'DAILY', label: 'يومي (Daily)' },
  { value: 'WEEKLY', label: 'أسبوعي (Weekly)' },
  { value: 'MONTHLY', label: 'شهري (Monthly)' },
  { value: 'QUARTERLY', label: 'ربع سنوي (Quarterly)' },
  { value: 'ANNUAL', label: 'سنوي (Annual)' },
]

const INITIAL_STEP = {
  step: '',
  hazard: '',
  control: '',
  before: 15,
  after: 4,
  responsible: 'مشرف الوردية / منفذ العمل',
}

export default function Jsa() {
  const toast = useToast()

  // Selection & Filter State
  const [openId, setOpenId] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')

  // Modals
  const [createModal, setCreateModal] = useState(false)
  const [linkModal, setLinkModal] = useState(false)
  const [addStepModal, setAddStepModal] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  // API Data
  const stats = useApi(() => jsaApi.stats(), [])
  const list = useApi(() => jsaApi.list(), [])
  const availablePermits = useApi(() => jsaApi.availablePermits(), [])

  // Auto select initial row when list loads
  useEffect(() => {
    if (list.data && Array.isArray(list.data) && list.data.length > 0 && !openId) {
      setOpenId(list.data[0].id)
    }
  }, [list.data, openId])

  // Fetch detail for selected JSA
  const detail = useApi(() => (openId ? jsaApi.byId(openId) : Promise.resolve(null)), [openId])

  const reloadAll = () => {
    stats.reload?.()
    list.reload?.()
    detail.reload?.()
    availablePermits.reload?.()
  }

  // Cross-module event listeners
  useEffect(() => {
    const handleDataChanged = () => reloadAll()
    window.addEventListener('hse:data-changed', handleDataChanged)
    window.addEventListener('hse:notifications-changed', handleDataChanged)
    return () => {
      window.removeEventListener('hse:data-changed', handleDataChanged)
      window.removeEventListener('hse:notifications-changed', handleDataChanged)
    }
  }, [])

  // Filtered List
  const filteredList = useMemo(() => {
    const rows = Array.isArray(list.data) ? list.data : []
    return rows.filter((item) => {
      const matchesSearch =
        !searchQuery.trim() ||
        item.task?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.id?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.zone?.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.linkedPermit?.toLowerCase().includes(searchQuery.toLowerCase())

      const matchesStatus =
        statusFilter === 'ALL' ||
        (statusFilter === 'APPROVED' && (item.rawStatus === 'APPROVED' || item.statusId === 3)) ||
        (statusFilter === 'PENDING' && (item.rawStatus === 'PENDING_APPROVAL' || item.statusId === 2)) ||
        (statusFilter === 'DRAFT' && (item.rawStatus === 'DRAFT' || item.statusId === 1))

      return matchesSearch && matchesStatus
    })
  }, [list.data, searchQuery, statusFilter])

  // --- Create JSA Form State ---
  const [createForm, setCreateForm] = useState({
    taskName: '',
    zone: ZONES[0],
    permitRequired: true,
    permitType: 'HOT_WORK',
    frequency: 'AS_NEEDED',
    status: 'APPROVED',
    inherentScore: 16,
    residualScore: 4,
    linkPermitId: '',
    steps: [
      {
        step: 'فحص ومعايرة أجهزة قياس الغازات ومعدات العمل',
        hazard: 'تراكم غازات قابلة للاشتعال وأبخرة خطرة',
        control: 'قياس مسبق بنسبة لا تتجاوز 0% LEL ونسبة أكسجين 19.5%–23.5%',
        before: 16,
        after: 4,
        responsible: 'مسؤول السلامة',
      },
      {
        step: 'عزل مصادر الطاقة وتطبيق إجراءات LOTO وتأمين الموقع',
        hazard: 'صعق كهربائي، تشغيل مفاجئ، وتطاير شرر',
        control: 'وضع أقفال وبطاقات تحذيرية وفرش أغطية مقاومة للحريق',
        before: 16,
        after: 4,
        responsible: 'فريق الصيانة ومراقب الحريق',
      },
    ],
  })

  const resetCreateForm = () => {
    setCreateForm({
      taskName: '',
      zone: ZONES[0],
      permitRequired: true,
      permitType: 'HOT_WORK',
      frequency: 'AS_NEEDED',
      status: 'APPROVED',
      inherentScore: 16,
      residualScore: 4,
      linkPermitId: '',
      steps: [{ ...INITIAL_STEP }],
    })
  }

  // --- Link Permit Form State ---
  const [linkForm, setLinkForm] = useState({
    jsaId: '',
    permitId: '',
  })

  // Open link modal preloaded with currently selected JSA
  const handleOpenLinkModal = (customJsaId) => {
    const targetId = customJsaId || openId || (list.data?.[0]?.id ?? '')
    setLinkForm({
      jsaId: targetId,
      permitId: availablePermits.data?.[0]?.id ?? '',
    })
    setLinkModal(true)
  }

  // --- Add Step Form State ---
  const [stepForm, setStepForm] = useState({ ...INITIAL_STEP })

  // ─────────────────────────────── HANDLERS ────────────────────────────────

  const handleCreateSubmit = async (e) => {
    e.preventDefault()
    if (!createForm.taskName.trim()) {
      toast('يرجى كتابة اسم المهمة / النشاط', 'cr')
      return
    }
    if (!createForm.steps || createForm.steps.length === 0 || !createForm.steps[0].step.trim()) {
      toast('يرجى إدخال خطوة عمل واحدة على الأقل', 'cr')
      return
    }

    setSubmitting(true)
    try {
      const created = await jsaApi.create(createForm)
      toast(`تم إنشاء تحليل السلامة (${created.id || 'JSA'}) وحفظه في قاعدة البيانات بنجاح`, 'ok')
      setCreateModal(false)
      resetCreateForm()
      reloadAll()
      if (created.id) setOpenId(created.id)
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل إنشاء تحليل السلامة', 'cr')
    } finally {
      setSubmitting(false)
    }
  }

  const handleLinkSubmit = async (e) => {
    e.preventDefault()
    if (!linkForm.jsaId || !linkForm.permitId) {
      toast('يرجى اختيار تحليل السلامة وتصريح العمل المطلوب ربطه', 'cr')
      return
    }

    setSubmitting(true)
    try {
      const res = await jsaApi.linkPermit(linkForm.jsaId, linkForm.permitId)
      toast(res.message || 'تم ربط تصريح العمل بتحليل السلامة بنجاح', 'ok')
      setLinkModal(false)
      reloadAll()
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل ربط تصريح العمل', 'cr')
    } finally {
      setSubmitting(false)
    }
  }

  const handleApproveJsa = async (idToApprove) => {
    const target = idToApprove || openId
    if (!target) return
    try {
      await jsaApi.approve(target)
      toast(`تم اعتماد وثيقة تحليل السلامة (${target}) بنجاح`, 'ok')
      reloadAll()
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل اعتماد تحليل السلامة', 'cr')
    }
  }

  const handleDeleteJsa = async (idToDelete) => {
    const target = idToDelete || openId
    if (!target) return
    if (!window.confirm(`هل أنت متأكد من حذف وثيقة تحليل السلامة (${target})؟`)) return

    try {
      await jsaApi.delete(target)
      toast(`تم حذف وثيقة تحليل السلامة (${target}) بنجاح`, 'ok')
      setOpenId('')
      reloadAll()
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل حذف وثيقة تحليل السلامة', 'cr')
    }
  }

  const handleAddStepSubmit = async (e) => {
    e.preventDefault()
    if (!openId) {
      toast('يرجى اختيار تحليل السلامة أولاً', 'cr')
      return
    }
    if (!stepForm.step.trim()) {
      toast('يرجى كتابة وصف الخطوة', 'cr')
      return
    }

    setSubmitting(true)
    try {
      await jsaApi.addStep(openId, stepForm)
      toast('تمت إضافة خطوة التحليل بنجاح', 'ok')
      setAddStepModal(false)
      setStepForm({ ...INITIAL_STEP })
      reloadAll()
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل إضافة الخطوة', 'cr')
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeleteStep = async (stepId) => {
    if (!openId || !stepId) return
    if (!window.confirm('هل تريد إزالة هذه الخطوة من تحليل السلامة؟')) return

    try {
      await jsaApi.deleteStep(openId, stepId)
      toast('تم حذف الخطوة بنجاح', 'ok')
      reloadAll()
      window.dispatchEvent(new CustomEvent('hse:data-changed'))
    } catch (err) {
      toast(err.message || 'فشل حذف الخطوة', 'cr')
    }
  }

  return (
    <>
      <PageHeader title="تحليل سلامة المهام (JSA)" meta="job safety analysis · linked to eptw">
        <Btn icon="permit" onClick={() => handleOpenLinkModal()}>
          ربط بتصريح عمل
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setCreateModal(true)}>
          تحليل مهمة جديدة
        </Btn>
      </PageHeader>

      {/* KPI Cards */}
      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi
              label="تحليلات معتمدة"
              value={s.approved ?? 32}
              tone="safe"
              sub={`تغطي ${s.criticalTaskCoverage ?? 96}% من المهام الحرجة`}
            />
            <Kpi
              label="تحتاج مراجعة دورية"
              value={s.needsReview ?? 4}
              tone="warn"
              sub="مر عليها أكثر من 12 شهر"
            />
            <Kpi
              label="مرتبطة بتصاريح"
              value={s.linkedToPermits ?? 28}
              tone="info"
              sub="إلزامية قبل إصدار PTW"
            />
            <Kpi
              label="تغطية المهام الحرجة"
              value={`${s.criticalTaskCoverage ?? 96}%`}
              tone="hi"
              sub="الهدف 100% بنهاية Q4"
            />
          </KpiRow>
        )}
      </Async>

      {/* Main 2-Column Grid */}
      <Grid cols={2}>
        {/* Right Column: JSA Register Table */}
        <Card>
          <div className="p-3.5 border-b border-line flex flex-wrap items-center justify-between gap-2.5">
            <CardHead title="سجل التحليلات" hint="JSA REGISTER" />
            <div className="flex items-center gap-2">
              <span className="font-mono text-2xs text-txt-3">
                {filteredList.length} سجل
              </span>
              <Btn size="sm" icon="refresh" onClick={reloadAll} title="تحديث البيانات" />
            </div>
          </div>

          {/* Search & Filter Bar */}
          <div className="p-3 bg-steel-3/40 border-b border-line flex flex-wrap items-center gap-2.5">
            <div className="flex-1 min-w-[180px] relative">
              <input
                type="text"
                placeholder="بحث بالمهمة، الكود، المنطقة..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full bg-steel-2 border border-line rounded px-3 py-1.5 text-xs text-txt placeholder:text-txt-3 focus:border-hi focus:outline-none"
              />
              {searchQuery && (
                <button
                  onClick={() => setSearchQuery('')}
                  className="absolute left-2.5 top-1/2 -translate-y-1/2 text-txt-3 hover:text-txt text-xs"
                >
                  ✕
                </button>
              )}
            </div>

            <div className="flex items-center gap-1">
              {[
                { id: 'ALL', label: 'الكل' },
                { id: 'APPROVED', label: 'معتمد' },
                { id: 'PENDING', label: 'قيد المراجعة' },
                { id: 'DRAFT', label: 'مسودة' },
              ].map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => setStatusFilter(btn.id)}
                  className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                    statusFilter === btn.id
                      ? 'bg-hi text-white'
                      : 'bg-steel-2 text-txt-2 hover:bg-steel-3'
                  }`}
                >
                  {btn.label}
                </button>
              ))}
            </div>
          </div>

          <Async state={list} rows={8}>
            {() =>
              filteredList.length === 0 ? (
                <div className="py-12 text-center text-txt-3 text-xs">
                  لا توجد سجلات JSA مطابقة لشروط البحث
                </div>
              ) : (
                <Table head={['الكود', 'المهمة', 'المنطقة', 'خطوات', 'حرجة', 'التصريح', 'آخر مراجعة', 'الحالة']}>
                  {filteredList.map((j) => (
                    <tr
                      key={j.id}
                      onClick={() => setOpenId(j.id)}
                      className={`cursor-pointer transition-colors ${
                        openId === j.id ? 'bg-hi/15 border-r-4 border-r-hi font-medium' : 'hover:bg-steel-3/50'
                      }`}
                    >
                      <td className="mono font-semibold text-txt">{j.id}</td>
                      <td className="max-w-[200px] truncate" title={j.task}>
                        {j.task}
                      </td>
                      <td className="text-xs text-txt-2">{j.zone}</td>
                      <td className="mono">{j.steps}</td>
                      <td className="mono text-warn font-semibold">{j.criticalSteps}</td>
                      <td className="text-xs font-medium text-hi truncate max-w-[120px]">
                        {j.linkedPermit}
                      </td>
                      <td className="mono text-2xs text-txt-3">{j.reviewed}</td>
                      <td>
                        <Pill tone={j.tone}>{j.status}</Pill>
                      </td>
                    </tr>
                  ))}
                </Table>
              )
            }
          </Async>
        </Card>

        {/* Left Column: Step / Hazard / Control Details Panel */}
        <Card>
          <div className="p-3.5 border-b border-line flex flex-wrap items-center justify-between gap-2">
            <CardHead
              title={`تفصيل الخطوات — ${openId || 'اختر تحليل'}`}
              hint="STEP / HAZARD / CONTROL"
            />
            {openId && (
              <div className="flex items-center gap-1.5">
                <Btn size="sm" icon="plus" onClick={() => setAddStepModal(true)}>
                  إضافة خطوة
                </Btn>
                <Btn size="sm" icon="permit" onClick={() => handleOpenLinkModal(openId)}>
                  ربط بتصريح
                </Btn>
                <Btn
                  size="sm"
                  tone="cr"
                  icon="trash"
                  onClick={() => handleDeleteJsa(openId)}
                  title="حذف التحليل"
                />
              </div>
            )}
          </div>

          <CardBody>
            <Async state={detail} rows={6}>
              {(d) =>
                !d ? (
                  <div className="text-sm text-txt-3 py-16 text-center">
                    يرجى اختيار تحليل سلامة من الجدول لعرض تفاصيل الخطوات والضوابط
                  </div>
                ) : (
                  <>
                    {/* Summary Banner */}
                    <div className="mb-4 p-3 bg-steel-3/60 border border-line rounded-lg">
                      <div className="flex items-start justify-between gap-2.5 mb-2">
                        <div className="flex-1">
                          <h4 className="text-sm font-semibold text-txt mb-1">{d.task}</h4>
                          <div className="flex flex-wrap items-center gap-2 text-xs text-txt-2">
                            <span>المنطقة: <strong className="text-txt">{d.zone}</strong></span>
                            <span>·</span>
                            <span>التصريح: <strong className="text-hi">{d.permitLabel}</strong></span>
                            <span>·</span>
                            <span>درجة الخطر: <strong className="text-warn">{d.inherentScore} ➔ {d.residualScore}</strong></span>
                          </div>
                        </div>
                        <div className="flex flex-col items-end gap-1 shrink-0">
                          <Pill tone={d.tone}>{d.status}</Pill>
                          {d.rawStatus !== 'APPROVED' && d.statusId !== 3 && (
                            <button
                              onClick={() => handleApproveJsa(d.id)}
                              className="text-2xs text-safe hover:underline font-semibold"
                            >
                              ✓ اعتماد الآن
                            </button>
                          )}
                        </div>
                      </div>

                      {/* Linked Permits Info */}
                      {d.linkedPermits && d.linkedPermits.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-line/60 flex items-center gap-2 text-2xs text-txt-2">
                          <Icon name="permit" size={14} className="text-hi shrink-0" />
                          <span>مرتبط بتصاريح عمل نشطة:</span>
                          <div className="flex flex-wrap gap-1">
                            {d.linkedPermits.map((lp) => (
                              <span
                                key={lp.permitId}
                                className="px-1.5 py-0.5 rounded bg-hi/10 text-hi font-mono font-medium"
                              >
                                {lp.permitCode} ({lp.type})
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Step Cards List */}
                    {!d.steps || d.steps.length === 0 ? (
                      <div className="text-center py-10 border border-dashed border-line rounded-lg">
                        <p className="text-xs text-txt-3 mb-3">
                          لم يتم إدخال خطوات تفصيلية لهذا التحليل بعد
                        </p>
                        <Btn size="sm" icon="plus" onClick={() => setAddStepModal(true)}>
                          إضافة أول خطوة تحليل
                        </Btn>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {d.steps.map((s, i) => (
                          <div
                            key={s.id || i}
                            className="bg-steel-3 border border-line rounded-lg p-3.5 hover:border-hi/40 transition-colors relative group"
                          >
                            <div className="flex items-start gap-3">
                              <span className="w-6 h-6 rounded-full bg-steel-2 border border-line font-mono num text-xs text-hi font-bold flex items-center justify-center shrink-0 mt-0.5">
                                {s.stepNo || i + 1}
                              </span>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center justify-between gap-2 mb-2">
                                  <div className="text-[13px] font-semibold text-txt">
                                    {s.step || s.taskStep}
                                  </div>
                                  {s.id && (
                                    <button
                                      onClick={() => handleDeleteStep(s.id)}
                                      className="text-txt-3 hover:text-crit opacity-0 group-hover:opacity-100 transition-opacity p-1 -m-1"
                                      title="حذف هذه الخطوة"
                                    >
                                      <Icon name="close" size={14} />
                                    </button>
                                  )}
                                </div>

                                <div className="grid sm:grid-cols-2 gap-2.5 text-xs bg-steel-2/60 p-2.5 rounded border border-line/50">
                                  <div className="space-y-0.5">
                                    <div className="flex items-center gap-1 text-crit font-semibold text-2xs">
                                      <Icon name="warn" size={12} />
                                      <span>الخطر المحتمل (Hazard):</span>
                                    </div>
                                    <div className="text-txt-2 leading-relaxed">{s.hazard}</div>
                                  </div>
                                  <div className="space-y-0.5">
                                    <div className="flex items-center gap-1 text-safe font-semibold text-2xs">
                                      <Icon name="check" size={12} />
                                      <span>ضابط التحكم (Control Measure):</span>
                                    </div>
                                    <div className="text-txt-2 leading-relaxed">{s.control || s.controlMeasure}</div>
                                  </div>
                                </div>

                                <div className="mt-2.5 flex items-center justify-between text-2xs text-txt-3">
                                  <div className="flex items-center gap-2">
                                    <span>مستوى الخطر:</span>
                                    <span className="font-mono text-crit font-bold">{s.before || 15}</span>
                                    <span>➔</span>
                                    <span className="font-mono text-safe font-bold">{s.after || 4}</span>
                                  </div>
                                  <div>
                                    المسؤول: <strong className="text-txt-2">{s.responsible}</strong>
                                  </div>
                                </div>
                              </div>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </>
                )
              }
            </Async>
          </CardBody>
        </Card>
      </Grid>

      {/* ──────────────────────── MODAL 1: CREATE JSA ──────────────────────── */}
      <Modal
        open={createModal}
        onClose={() => setCreateModal(false)}
        title="إنشاء وثيقة تحليل سلامة المهمة (New JSA Document)"
        width={720}
        footer={
          <>
            <Btn variant="pri" onClick={handleCreateSubmit} disabled={submitting} icon="check">
              {submitting ? 'جارٍ الحفظ...' : 'حفظ واعتماد وثيقة JSA'}
            </Btn>
            <Btn onClick={() => setCreateModal(false)} disabled={submitting}>
              إلغاء
            </Btn>
          </>
        }
      >
        <form onSubmit={handleCreateSubmit} className="space-y-4">
          <Field label="اسم المهمة / النشاط (Task Activity Name)">
            <input
              type="text"
              required
              placeholder="مثال: أعمال لحام وقطع في مسار الكابلات الرئيسي"
              value={createForm.taskName}
              onChange={(e) => setCreateForm({ ...createForm, taskName: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            />
          </Field>

          <div className="grid sm:grid-cols-2 gap-3">
            <Field label="المنطقة / الموقع (Plant Zone)">
              <select
                value={createForm.zone}
                onChange={(e) => setCreateForm({ ...createForm, zone: e.target.value })}
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
              >
                {ZONES.map((z) => (
                  <option key={z} value={z}>
                    {z}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="نوع تصريح العمل المرتبط (Permit Type)">
              <select
                value={createForm.permitType}
                onChange={(e) => setCreateForm({ ...createForm, permitType: e.target.value })}
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
              >
                {PERMIT_TYPES.map((pt) => (
                  <option key={pt.value} value={pt.value}>
                    {pt.label}
                  </option>
                ))}
              </select>
            </Field>
          </div>

          <div className="grid sm:grid-cols-3 gap-3">
            <Field label="دورية المراجعة (Frequency)">
              <select
                value={createForm.frequency}
                onChange={(e) => setCreateForm({ ...createForm, frequency: e.target.value })}
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
              >
                {FREQUENCIES.map((f) => (
                  <option key={f.value} value={f.value}>
                    {f.label}
                  </option>
                ))}
              </select>
            </Field>

            <Field label="الخطر الأولي (Inherent 1-25)">
              <input
                type="number"
                min="1"
                max="25"
                value={createForm.inherentScore}
                onChange={(e) =>
                  setCreateForm({ ...createForm, inherentScore: parseInt(e.target.value, 10) || 15 })
                }
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none font-mono"
              />
            </Field>

            <Field label="الخطر المتبقي (Residual 1-25)">
              <input
                type="number"
                min="1"
                max="25"
                value={createForm.residualScore}
                onChange={(e) =>
                  setCreateForm({ ...createForm, residualScore: parseInt(e.target.value, 10) || 4 })
                }
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none font-mono"
              />
            </Field>
          </div>

          {/* Optional immediate permit link */}
          <Field label="ربط بتصريح عمل قائم (اختياري)">
            <select
              value={createForm.linkPermitId}
              onChange={(e) => setCreateForm({ ...createForm, linkPermitId: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            >
              <option value="">-- بدون ربط فوري (يمكن الربط لاحقاً) --</option>
              {(availablePermits.data || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id}: {p.description} ({p.zone})
                </option>
              ))}
            </select>
          </Field>

          {/* Step Builder */}
          <div className="pt-3 border-t border-line">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-txt flex items-center gap-1.5">
                <Icon name="check" size={14} className="text-hi" />
                خطوات العمل وتحليل المخاطر (Hazard & Control Breakdown)
              </span>
              <button
                type="button"
                onClick={() =>
                  setCreateForm({
                    ...createForm,
                    steps: [...createForm.steps, { ...INITIAL_STEP }],
                  })
                }
                className="text-2xs text-hi hover:underline font-semibold flex items-center gap-1"
              >
                + إضافة خطوة أخرى
              </button>
            </div>

            <div className="space-y-3 max-h-[260px] overflow-y-auto pr-1">
              {createForm.steps.map((st, idx) => (
                <div key={idx} className="p-3 bg-steel-3/80 border border-line rounded-lg space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-2xs font-bold text-hi font-mono">الخطوة #{idx + 1}</span>
                    {createForm.steps.length > 1 && (
                      <button
                        type="button"
                        onClick={() => {
                          const updated = createForm.steps.filter((_, sIdx) => sIdx !== idx)
                          setCreateForm({ ...createForm, steps: updated })
                        }}
                        className="text-2xs text-crit hover:underline"
                      >
                        إزالة الخطوة
                      </button>
                    )}
                  </div>

                  <input
                    type="text"
                    required
                    placeholder="وصف خطوة العمل (مثال: عزل القواطع وتطبيق إجراء LOTO)"
                    value={st.step}
                    onChange={(e) => {
                      const updated = [...createForm.steps]
                      updated[idx].step = e.target.value
                      setCreateForm({ ...createForm, steps: updated })
                    }}
                    className="w-full bg-steel-2 border border-line rounded px-2.5 py-1.5 text-xs text-txt focus:border-hi focus:outline-none"
                  />

                  <div className="grid sm:grid-cols-2 gap-2">
                    <input
                      type="text"
                      required
                      placeholder="الخطر المحتمل (مثال: صعق كهربائي أو تشغيل مفاجئ)"
                      value={st.hazard}
                      onChange={(e) => {
                        const updated = [...createForm.steps]
                        updated[idx].hazard = e.target.value
                        setCreateForm({ ...createForm, steps: updated })
                      }}
                      className="w-full bg-steel-2 border border-line rounded px-2.5 py-1.5 text-xs text-txt focus:border-hi focus:outline-none"
                    />

                    <input
                      type="text"
                      required
                      placeholder="ضابط التحكم (مثال: قفل كهربائي + قياس انعدام الجهد)"
                      value={st.control}
                      onChange={(e) => {
                        const updated = [...createForm.steps]
                        updated[idx].control = e.target.value
                        setCreateForm({ ...createForm, steps: updated })
                      }}
                      className="w-full bg-steel-2 border border-line rounded px-2.5 py-1.5 text-xs text-txt focus:border-hi focus:outline-none"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </form>
      </Modal>

      {/* ──────────────────────── MODAL 2: LINK TO PERMIT ──────────────────────── */}
      <Modal
        open={linkModal}
        onClose={() => setLinkModal(false)}
        title="ربط وثيقة تحليل السلامة بتصريح عمل (Link JSA to ePTW)"
        width={560}
        footer={
          <>
            <Btn variant="pri" onClick={handleLinkSubmit} disabled={submitting} icon="permit">
              {submitting ? 'جارٍ الربط...' : 'تأكيد الربط'}
            </Btn>
            <Btn onClick={() => setLinkModal(false)} disabled={submitting}>
              إلغاء
            </Btn>
          </>
        }
      >
        <form onSubmit={handleLinkSubmit} className="space-y-4">
          <Field label="تحليل سلامة المهمة المراد ربطه (Select JSA)">
            <select
              value={linkForm.jsaId}
              onChange={(e) => setLinkForm({ ...linkForm, jsaId: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            >
              {(list.data || []).map((j) => (
                <option key={j.id} value={j.id}>
                  {j.id}: {j.task} ({j.zone})
                </option>
              ))}
            </select>
          </Field>

          <Field label="تصريح العمل المستهدف (Select Work Permit)">
            <select
              value={linkForm.permitId}
              onChange={(e) => setLinkForm({ ...linkForm, permitId: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            >
              <option value="">-- اختر تصريح العمل --</option>
              {(availablePermits.data || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.id}: {p.description} ({p.typeLabel || p.type} - {p.zone})
                </option>
              ))}
            </select>
          </Field>

          <div className="p-3 bg-hi/10 border border-hi/20 rounded text-xs text-txt-2 leading-relaxed">
            <strong className="text-hi font-semibold block mb-1">معلومة الربط التكاملي:</strong>
            ربط وثيقة JSA بتصريح العمل يضمن إدراج شروط السلامة وضوابط المخاطر ضمن نموذج التصريح الإلكتروني (ePTW) ورفع مؤشر تغطية المهام الحرجة.
          </div>
        </form>
      </Modal>

      {/* ──────────────────────── MODAL 3: ADD STEP ──────────────────────── */}
      <Modal
        open={addStepModal}
        onClose={() => setAddStepModal(false)}
        title={`إضافة خطوة تحليل لـ (${openId})`}
        width={540}
        footer={
          <>
            <Btn variant="pri" onClick={handleAddStepSubmit} disabled={submitting} icon="plus">
              {submitting ? 'جارٍ الإضافة...' : 'إضافة الخطوة'}
            </Btn>
            <Btn onClick={() => setAddStepModal(false)} disabled={submitting}>
              إلغاء
            </Btn>
          </>
        }
      >
        <form onSubmit={handleAddStepSubmit} className="space-y-3.5">
          <Field label="وصف خطوة العمل (Task Step)">
            <input
              type="text"
              required
              placeholder="مثال: فحص نقاط التثبيت وتطبيق حزام الأمان"
              value={stepForm.step}
              onChange={(e) => setStepForm({ ...stepForm, step: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            />
          </Field>

          <Field label="الخطر المحتمل (Hazard)">
            <input
              type="text"
              required
              placeholder="مثال: السقوط من ارتفاع أو انزلاق السقالة"
              value={stepForm.hazard}
              onChange={(e) => setStepForm({ ...stepForm, hazard: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            />
          </Field>

          <Field label="ضابط التحكم والوقاية (Control Measure)">
            <input
              type="text"
              required
              placeholder="مثال: استخدام مانع سقوط مزدوج والتثبيت في نقطة معتمدة"
              value={stepForm.control}
              onChange={(e) => setStepForm({ ...stepForm, control: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            />
          </Field>

          <div className="grid grid-cols-2 gap-3">
            <Field label="درجة الخطر قبل التحكم (Before)">
              <input
                type="number"
                min="1"
                max="25"
                value={stepForm.before}
                onChange={(e) => setStepForm({ ...stepForm, before: parseInt(e.target.value, 10) || 15 })}
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none font-mono"
              />
            </Field>

            <Field label="درجة الخطر بعد التحكم (After)">
              <input
                type="number"
                min="1"
                max="25"
                value={stepForm.after}
                onChange={(e) => setStepForm({ ...stepForm, after: parseInt(e.target.value, 10) || 4 })}
                className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none font-mono"
              />
            </Field>
          </div>

          <Field label="المسؤول عن التنفيذ والمراقبة (Responsible Role)">
            <input
              type="text"
              placeholder="مثال: مسؤول السلامة / مشرف الوردية"
              value={stepForm.responsible}
              onChange={(e) => setStepForm({ ...stepForm, responsible: e.target.value })}
              className="w-full bg-steel-3 border border-line rounded px-3 py-2 text-xs text-txt focus:border-hi focus:outline-none"
            />
          </Field>
        </form>
      </Modal>
    </>
  )
}
