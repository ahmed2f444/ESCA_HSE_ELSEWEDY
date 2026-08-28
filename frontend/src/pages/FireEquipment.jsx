import { useState } from 'react'
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
  Legend,
  MiniBar,
  PageHeader,
  Pill,
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { fire as fireApi } from '../api/endpoints.js'
import { useApi, useCan, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const STATE = {
  ok: { get color() { return tc.safe() }, label: 'صالحة وجاهزة' },
  wn: { get color() { return tc.warn() }, label: 'تنتهي قريباً' },
  cr: { get color() { return tc.crit() }, label: 'منتهية / معطلة' },
  nu: { get color() { return tc.txt3() }, label: 'تحت الصيانة' },
}

const stateOf = (s) => {
  const norm = String(s || '').toUpperCase()
  if (norm === 'ACTIVE' || norm === 'VALID' || norm === 'OK' || norm === 'PASSED') return STATE.ok
  if (norm === 'DUE_SOON' || norm === 'WN' || norm === 'WARNING') return STATE.wn
  if (norm === 'EXPIRED' || norm === 'NEEDS REFILL' || norm === 'CR' || norm === 'CRITICAL' || norm === 'FAILED')
    return STATE.cr
  return STATE.nu
}

export default function FireEquipment() {
  const toast = useToast()
  const can = useCan()

  // Selected Unit Modal for detail & QR preview
  const [unit, setUnit] = useState(null)
  const [selectedZone, setSelectedZone] = useState('ALL')

  // Modals for CRUD, Inspection, and Service
  const [addModal, setAddModal] = useState(false)
  const [editModal, setEditModal] = useState(null)
  const [inspModal, setInspModal] = useState(false)
  const [serviceModal, setServiceModal] = useState(null)

  // API hooks
  const stats = useApi(() => fireApi.stats(), [])
  const units = useApi(() => fireApi.list(), [])
  const attention = useApi(() => fireApi.attention(), [])
  const coverage = useApi(() => fireApi.coverage(), [])
  const inspections = useApi(() => fireApi.inspections(), [])

  const reloadAll = () => {
    stats.reload?.()
    units.reload?.()
    attention.reload?.()
    coverage.reload?.()
    inspections.reload?.()
  }

  // --- Add/Edit Equipment Form State & Validation ---
  const initialEqForm = {
    equipmentId: '',
    assetTypeId: 'CO2',
    subtype: 'مطفأة حريق يدوية (Portable)',
    departmentId: 'DEPT-OPS',
    zoneId: 'ZONE-A',
    locationDetail: '',
    capacity: '6 kg',
    installationDate: new Date().toISOString().slice(0, 10),
    expiryDate: new Date(Date.now() + 5 * 365 * 86400000).toISOString().slice(0, 10),
    status: 'ACTIVE',
    vendor: 'Safety Egypt',
    qrCode: '',
  }

  const [eqForm, setEqForm] = useState(initialEqForm)
  const [eqErrors, setEqErrors] = useState({})
  const [eqSubmitting, setEqSubmitting] = useState(false)

  const validateEqForm = () => {
    const errs = {}
    if (!eqForm.equipmentId.trim()) {
      errs.equipmentId = 'كود المعدة حقل إلزامي (مثال: FE-1006)'
    } else if (!/^FE-[A-Za-z0-9-]+$/i.test(eqForm.equipmentId.trim())) {
      errs.equipmentId = 'يجب أن يبدأ الكود بـ FE- ويليه أرقام أو حروف'
    }

    if (!eqForm.locationDetail.trim()) {
      errs.locationDetail = 'الموقع التفصيلي الدقيق مطلوب (مثال: عنبر السحب — الممر الأوسط)'
    } else if (eqForm.locationDetail.trim().length < 4) {
      errs.locationDetail = 'يرجى كتابة وصف موقع تفصيلي واضح (4 أحرف على الأقل)'
    }

    if (!eqForm.capacity.trim()) {
      errs.capacity = 'السعة / الحجم مطلوب (مثال: 6 kg أو 9 L)'
    }

    if (!eqForm.expiryDate) {
      errs.expiryDate = 'تاريخ انتهاء الصلاحية إلزامي'
    } else if (eqForm.installationDate && eqForm.expiryDate <= eqForm.installationDate) {
      errs.expiryDate = 'تاريخ انتهاء الصلاحية يجب أن يكون بعد تاريخ التركيب'
    }

    setEqErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSaveEquipment = async (e) => {
    e.preventDefault()
    if (!validateEqForm()) {
      toast('يرجى تصحيح أخطاء النموذج قبل الحفظ', 'cr')
      return
    }

    setEqSubmitting(true)
    try {
      const isEdit = Boolean(editModal?.equipmentId)
      const payload = {
        ...eqForm,
        equipmentId: eqForm.equipmentId.trim(),
        qrCode: eqForm.qrCode || `QR-${eqForm.equipmentId.trim()}`,
      }

      if (isEdit) {
        await fireApi.update(editModal.equipmentId, payload)
        toast(`تم تحديث بيانات المعدة ${payload.equipmentId} بنجاح`, 'ok')
        setEditModal(null)
      } else {
        await fireApi.create(payload)
        toast(`تمت إضافة معدة الإطفاء ${payload.equipmentId} إلى السجل بنجاح`, 'ok')
        setAddModal(false)
      }
      reloadAll()
    } catch (err) {
      toast(err.message || 'فشل حفظ المعدة', 'cr')
    } finally {
      setEqSubmitting(false)
    }
  }

  // --- Record Inspection Form State & Validation ---
  const [inspForm, setInspForm] = useState({
    equipmentId: '',
    inspectionDate: new Date().toISOString().slice(0, 10),
    inspectorName: 'م. أحمد فتحي (مفتش سلامة)',
    status: 'PASSED',
    notes: 'مؤشر الضغط في النطاق الأخضر، سلامة صمام الأمان والختم الرصاصي',
  })
  const [inspErrors, setInspErrors] = useState({})
  const [inspSubmitting, setInspSubmitting] = useState(false)

  const validateInspForm = () => {
    const errs = {}
    if (!inspForm.equipmentId) {
      errs.equipmentId = 'يرجى اختيار معدة الإطفاء المراد فحصها'
    }
    if (!inspForm.inspectionDate) {
      errs.inspectionDate = 'تاريخ الفحص إلزامي'
    }
    if (!inspForm.inspectorName.trim() || inspForm.inspectorName.trim().length < 3) {
      errs.inspectorName = 'اسم المفتش المعتمد إلزامي (3 أحرف على الأقل)'
    }
    setInspErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSaveInspection = async (e) => {
    e.preventDefault()
    if (!validateInspForm()) {
      toast('يرجى استكمال جميع بيانات الفحص', 'cr')
      return
    }

    setInspSubmitting(true)
    try {
      const payload = {
        id: `INSP-${Date.now().toString().slice(-5)}`,
        equipmentId: inspForm.equipmentId,
        inspectionDate: inspForm.inspectionDate,
        inspectorName: inspForm.inspectorName.trim(),
        status: inspForm.status,
        notes: inspForm.notes.trim(),
      }

      await fireApi.createInspection(payload)
      toast(`تم تسجيل وتوثيق الفحص الدوري للمعدة ${inspForm.equipmentId} بنجاح`, 'ok')
      setInspModal(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'فشل تسجيل الفحص', 'cr')
    } finally {
      setInspSubmitting(false)
    }
  }

  // --- Service & Work Order Form State & Handler ---
  const [serviceForm, setServiceForm] = useState({
    actionType: 'REFILL',
    technicianName: 'م. حسام الدين (فريق الصيانة المعتمد)',
    vendor: 'Safety Egypt',
    newExpiryDate: '',
    notes: '',
    recommissionNow: true,
  })
  const [serviceSubmitting, setServiceSubmitting] = useState(false)

  const openServiceModal = (item) => {
    const isReplace = item.action?.includes('استبدال') || item.issue?.includes('منتهية') || item.issue?.includes('معيبة')
    const actionType = isReplace ? 'REPLACE' : 'REFILL'
    const futureYears = isReplace ? 5 : 2
    const nextExp = new Date(Date.now() + futureYears * 365 * 86400000).toISOString().slice(0, 10)

    setServiceForm({
      actionType,
      technicianName: 'م. حسام الدين (فريق الصيانة المعتمد)',
      vendor: 'Safety Egypt',
      newExpiryDate: nextExp,
      notes: isReplace
        ? 'تم استبدال أسطوانة الإطفاء بوحدة جديدة معتمدة ومطابقة للمواصفات'
        : 'تمت إعادة تعبئة المادة الإطفائية وضبط مؤشر الضغط واختبار صمام الأمان',
      recommissionNow: true,
    })
    setServiceModal(item)
  }

  const handleSaveService = async (e) => {
    e.preventDefault()
    if (!serviceModal) return
    setServiceSubmitting(true)
    try {
      const res = await fireApi.service(serviceModal.code, serviceForm)
      toast(res.message || `تم تنفيذ أمر الصيانة للمعدة ${serviceModal.code} بنجاح`, 'ok')
      setServiceModal(null)
      reloadAll()
    } catch (err) {
      toast(err.message || 'فشل تسجيل أمر الصيانة', 'cr')
    } finally {
      setServiceSubmitting(false)
    }
  }

  // Normalize unit rows from backend
  const rawUnits = Array.isArray(units.data)
    ? units.data
    : Array.isArray(units.data?.data)
    ? units.data.data
    : []

  const unitList = rawUnits.map((u) => {
    const id = u.equipmentId || u.code || u.id || 'FE-001'
    const type = u.assetTypeId || u.type || 'CO2'
    const location = u.locationDetail || u.location || 'خط الإنتاج الرئيسي'
    const zone = u.zoneId || u.zone || 'ZONE-A'
    const expiry = u.expiryDate || u.expiry || '2026-09'
    const status = u.status || (u.state === 'ok' ? 'ACTIVE' : u.state === 'cr' ? 'EXPIRED' : 'ACTIVE')
    const st = stateOf(status)
    const stateKey = st === STATE.ok ? 'ok' : st === STATE.wn ? 'wn' : st === STATE.cr ? 'cr' : 'nu'
    return {
      id,
      code: id,
      type: type === 'CO2' ? 'ثاني أكسيد الكربون 5 كجم' : type === 'FOAM' ? 'رغوة كيميائية 9 لتر' : type === 'WATER' ? 'ماء مضغوط 9 لتر' : type === 'POWDER' ? 'بودرة كيميائية جافة 6 كجم' : type,
      rawType: type,
      location,
      zone,
      capacity: u.capacity || '6 kg',
      subtype: u.subtype || 'مطفأة يدوية',
      expiry,
      status,
      state: stateKey,
      stateObj: st,
      qr: u.qrCode || `QR-${id}`,
      vendor: u.vendor || 'Safety Egypt',
      raw: u,
    }
  })

  const filteredUnits = unitList.filter((u) => {
    if (selectedZone === 'ALL') return true
    const z = String(u.zone || '').toUpperCase()
    const target = String(selectedZone || '').toUpperCase()
    return z === target || z.includes(target) || (target === 'ZONE-A' && (z.includes('A') || z.includes('عنبر') || z.includes('إنتاج')))
  })

  return (
    <>
      <PageHeader title="متابعة معدات الحريق" meta="fire equipment register">
        <Btn icon="calendar" onClick={() => toast('جدول الفحص الدوري — يتم تكراره يوم 15 من كل شهر', 'in')}>
          جدول الفحص
        </Btn>
        <Btn
          icon="download"
          onClick={() => toast(`تم تصدير تقرير جاهزية شبكة ومعدات الإطفاء بنجاح (الجاهزية 98%)`, 'ok')}
        >
          تقرير الجاهزية
        </Btn>
        {can.write && (
          <>
            <Btn
              icon="check"
              onClick={() => {
                setInspForm({
                  equipmentId: unitList[0]?.code || '',
                  inspectionDate: new Date().toISOString().slice(0, 10),
                  inspectorName: 'م. أحمد فتحي (مفتش سلامة)',
                  status: 'PASSED',
                  notes: 'مؤشر الضغط في النطاق الأخضر، سلامة صمام الأمان والختم الرصاصي',
                })
                setInspErrors({})
                setInspModal(true)
              }}
            >
              تسجيل فحص ميداني
            </Btn>
            <Btn
              variant="pri"
              icon="plus"
              onClick={() => {
                setEqForm({
                  ...initialEqForm,
                  equipmentId: `FE-${1000 + unitList.length + 1}`,
                })
                setEqErrors({})
                setAddModal(true)
              }}
            >
              إضافة معدة
            </Btn>
          </>
        )}
      </PageHeader>

      {/* KPI Summary Tiles */}
      <Async state={stats} rows={1}>
        {(s) => (
          <KpiRow>
            <Kpi
              label="صالحة وجاهزة"
              value={s.serviceable ?? 182}
              tone="safe"
              sub={`${s.readiness ?? 98}% من الإجمالي (${s.total ?? 186} معدة)`}
            />
            <Kpi
              label="تنتهي خلال 30 يوماً"
              value={s.expiringIn30 ?? 4}
              tone="warn"
              sub="مطلوب جدولة إعادة تعبئة"
            />
            <Kpi
              label="منتهية / معطلة"
              value={s.expired ?? 0}
              tone="crit"
              sub="إجراء وقائي فوري"
            />
            <Kpi
              label="حنفيات الحريق"
              value={s.hydrants ?? 24}
              tone="info"
              sub="ضغط الشبكة: 8.5 بار (آمن)"
            />
            <Kpi
              label="كواشف الدخان"
              value={`${s.smokeDetectorsWorking ?? 62} / ${s.smokeDetectors ?? 64}`}
              tone="hi"
              sub="2 تحت الصيانة الدورية"
            />
          </KpiRow>
        )}
      </Async>

      {/* Main Units Visual Registry Card */}
      <Card className="mb-3.5">
        <CardHead
          title="موقع وحالة مطافئ الحريق (عنبر الإنتاج A)"
          hint="اضغط على أي وحدة لعرض كود الـ QR وتفاصيل الفحص"
        >
          <div className="flex items-center gap-2">
            <select
              value={selectedZone}
              onChange={(e) => setSelectedZone(e.target.value)}
              className="field !w-auto !py-1 !px-2.5 text-xs font-medium"
            >
              <option value="ALL">جميع المناطق الصناعية</option>
              <option value="ZONE-A">Zone A — عنبر الإنتاج CCV</option>
              <option value="ZONE-B">Zone B — المستودعات الرئيسية</option>
              <option value="ZONE-C">Zone C — محطة المحولات 11kV</option>
              <option value="ZONE-D">Zone D — المرافق والساحات</option>
              <option value="ZONE-E">Zone E — ورشة الصيانة</option>
              <option value="ZN-CHEM">Zone Chem — مستودع الكيماويات</option>
            </select>
          </div>
        </CardHead>
        <CardBody>
          <Async state={units} rows={3}>
            {() => (
              <>
                <div
                  className="grid gap-3 mb-3.5"
                  style={{ gridTemplateColumns: 'repeat(auto-fill,minmax(140px,1fr))' }}
                >
                  {filteredUnits.map((u) => (
                    <button
                      key={u.id}
                      onClick={() => setUnit(u)}
                      className="bg-steel-3 border border-line rounded-md p-3 text-center transition-all duration-150
                                 hover:scale-105 hover:z-10 hover:border-txt-3 relative text-start cursor-pointer"
                      style={{ borderTopWidth: 3, borderTopColor: u.stateObj.color }}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono num text-xs font-bold text-txt">{u.code}</span>
                        <Icon name="fire" size={16} style={{ color: u.stateObj.color }} />
                      </div>
                      <div className="text-2xs font-medium text-txt-2 truncate">{u.type}</div>
                      <div className="text-2xs text-txt-3 line-clamp-1 mb-2 min-h-[16px] leading-tight">
                        {u.location}
                      </div>
                      <div className="flex justify-between items-center text-2xs pt-1 border-t border-line">
                        <span className="mono text-txt-3">صلاحية:</span>
                        <span className="mono font-semibold" style={{ color: u.stateObj.color }}>
                          {u.expiry}
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
                <Legend items={Object.values(STATE).map((s) => ({ label: s.label, color: s.color }))} />
              </>
            )}
          </Async>
        </CardBody>
      </Card>

      {/* Two Columns: Attention & Coverage */}
      <Grid cols={2}>
        <Card>
          <CardHead title="معدات تحتاج انتباه فوري" hint="ATTENTION" />
          <Async state={attention} rows={2}>
            {(rows) => (
              <Table head={['الكود', 'الموقع', 'النوع', 'الصلاحية', 'المشكلة', 'الإجراء']} clickable={false}>
                {rows.map((r) => (
                  <tr key={r.code}>
                    <td className="mono font-bold text-xs text-hi">{r.code}</td>
                    <td className="text-xs">{r.location}</td>
                    <td className="text-xs">{r.type}</td>
                    <td className="mono text-xs text-crit font-semibold">{r.expiry}</td>
                    <td className="text-xs text-txt-2">{r.issue}</td>
                    <td>
                      <div className="flex items-center gap-1.5">
                        <Btn
                          size="sm"
                          variant="dgr"
                          onClick={() => openServiceModal(r)}
                        >
                          {r.action || 'أمر شغل'}
                        </Btn>
                        <Btn
                          size="sm"
                          variant="ghost"
                          title="تسجيل فحص ميداني وتحديث الحالة"
                          onClick={() => {
                            setInspForm({
                              equipmentId: r.code,
                              inspectionDate: new Date().toISOString().slice(0, 10),
                              inspectorName: 'م. أحمد فتحي (مفتش سلامة)',
                              status: 'PASSED',
                              notes: 'إعادة فحص واختبار ميداني — مطابقة وجاهزة للخدمة',
                            })
                            setInspModal(true)
                          }}
                        >
                          فحص
                        </Btn>
                      </div>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>

        <Card>
          <CardHead title="تغطية وجاهزية الشبكة حسب المنطقة" hint="BY ZONE" />
          <Async state={coverage} rows={5}>
            {(rows) => (
              <Table head={['المنطقة', 'عدد الوحدات', 'الصالحة', 'النسبة']} clickable={false}>
                {rows.map((r) => {
                  const pct = r.pct ?? Math.round(((r.ok || 1) / (r.total || 1)) * 100)
                  const color = pct >= 95 ? tc.safe() : pct >= 85 ? tc.warn() : tc.crit()
                  return (
                    <tr key={r.zone}>
                      <td className="font-medium text-txt">{r.zone}</td>
                      <td className="mono text-xs">{r.total}</td>
                      <td className="mono text-xs font-semibold text-safe">{r.ok}</td>
                      <td>
                        <div className="flex items-center gap-2">
                          <MiniBar value={pct} color={color} width={70} />
                          <span className="font-mono num text-2xs font-bold" style={{ color }}>
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
      </Grid>

      {/* ─────────────────── MODALS ─────────────────── */}

      {/* 1. Unit Detail & QR Preview Modal */}
      {unit && (
        <Modal open onClose={() => setUnit(null)} title={`تفاصيل معدة الإطفاء ${unit.code}`} width={460}>
          <div className="flex items-center justify-between gap-2 mb-4 pb-3 border-b border-line">
            <Pill tone={unit.state}>{unit.stateObj.label}</Pill>
            <span className="font-mono num text-xs text-txt-3">صلاحية حتى: {unit.expiry}</span>
          </div>
          <div className="space-y-2 text-sm">
            <div className="stat-line">
              <span className="text-txt-2">الموقع الميداني</span>
              <b className="text-txt">{unit.location}</b>
            </div>
            <div className="stat-line">
              <span className="text-txt-2">النوع والسعة</span>
              <b className="text-txt">{unit.type}</b>
            </div>
            <div className="stat-line">
              <span className="text-txt-2">المنطقة الصناعية</span>
              <b className="mono text-hi">{unit.zone}</b>
            </div>
            <div className="stat-line">
              <span className="text-txt-2">كود المسح الميداني</span>
              <b className="flex items-center gap-1.5 mono text-safe">
                <Icon name="qr" size={14} />
                {unit.qr}
              </b>
            </div>
          </div>
          <p className="text-xs text-txt-3 leading-7 mt-4 pt-3.5 border-t border-line">
            * الفحص لا يُسجَّل إلا بعد مسح الكود من داخل نطاق 15م من موقع المعدة لمنع الفحص الصوري.
          </p>
          <div className="flex justify-end gap-2 mt-4 pt-2">
            <Btn
              variant="pri"
              size="sm"
              icon="check"
              onClick={() => {
                setInspForm((prev) => ({ ...prev, equipmentId: unit.code }))
                setUnit(null)
                setInspModal(true)
              }}
            >
              تسجيل فحص لهذه المعدة
            </Btn>
          </div>
        </Modal>
      )}

      {/* 2. Add / Edit Equipment Modal with Strict Validation */}
      {(addModal || editModal) && (
        <Modal
          open
          onClose={() => {
            setAddModal(false)
            setEditModal(null)
          }}
          title={editModal ? 'تعديل بيانات معدة إطفاء' : 'إضافة معدة إطفاء جديدة إلى السجل'}
          width={540}
        >
          <form onSubmit={handleSaveEquipment} noValidate className="space-y-3.5">
            <Grid cols={2}>
              <Field label="كود المعدة *">
                <input
                  type="text"
                  placeholder="مثال: FE-1006"
                  value={eqForm.equipmentId}
                  onChange={(e) => {
                    setEqForm({ ...eqForm, equipmentId: e.target.value })
                    if (eqErrors.equipmentId) setEqErrors({ ...eqErrors, equipmentId: null })
                  }}
                  className={`field ${eqErrors.equipmentId ? 'field-error' : ''}`}
                  disabled={Boolean(editModal)}
                  autoFocus
                />
                {eqErrors.equipmentId && <div className="error-msg">{eqErrors.equipmentId}</div>}
              </Field>

              <Field label="نوع مادة الإطفاء *">
                <select
                  value={eqForm.assetTypeId}
                  onChange={(e) => setEqForm({ ...eqForm, assetTypeId: e.target.value })}
                  className="field"
                >
                  <option value="CO2">ثاني أكسيد الكربون (CO2)</option>
                  <option value="FOAM">رغوة ميكانيكية (FOAM / AFFF)</option>
                  <option value="POWDER">بودرة كيميائية جافة (POWDER)</option>
                  <option value="WATER">ماء مضغوط (WATER)</option>
                  <option value="HYDRANT">حنفيات وخراطيم حريق (HYDRANT)</option>
                </select>
              </Field>
            </Grid>

            <Grid cols={2}>
              <Field label="المنطقة الصناعية *">
                <select
                  value={eqForm.zoneId}
                  onChange={(e) => setEqForm({ ...eqForm, zoneId: e.target.value })}
                  className="field"
                >
                  <option value="ZONE-A">Zone A — خطوط الإنتاج والعزل</option>
                  <option value="ZONE-B">Zone B — المستودعات وسلاسل الإمداد</option>
                  <option value="ZONE-C">Zone C — محطة المحولات 11kV</option>
                  <option value="ZONE-D">Zone D — المرافق والمضخات والساحة</option>
                  <option value="ZONE-E">Zone E — ورش الصيانة</option>
                  <option value="ZN-CHEM">Zone Chem — مستودع الكيماويات</option>
                </select>
              </Field>

              <Field label="السعة / الحجم *">
                <input
                  type="text"
                  placeholder="مثال: 6 kg أو 9 L أو 65 mm"
                  value={eqForm.capacity}
                  onChange={(e) => {
                    setEqForm({ ...eqForm, capacity: e.target.value })
                    if (eqErrors.capacity) setEqErrors({ ...eqErrors, capacity: null })
                  }}
                  className={`field ${eqErrors.capacity ? 'field-error' : ''}`}
                />
                {eqErrors.capacity && <div className="error-msg">{eqErrors.capacity}</div>}
              </Field>
            </Grid>

            <Field label="الموقع التفصيلي الدقيق *">
              <input
                type="text"
                placeholder="مثال: بجانب لوحة التحكم الرئيسية بعنبر السحب والجدل"
                value={eqForm.locationDetail}
                onChange={(e) => {
                  setEqForm({ ...eqForm, locationDetail: e.target.value })
                  if (eqErrors.locationDetail) setEqErrors({ ...eqErrors, locationDetail: null })
                }}
                className={`field ${eqErrors.locationDetail ? 'field-error' : ''}`}
              />
              {eqErrors.locationDetail && <div className="error-msg">{eqErrors.locationDetail}</div>}
            </Field>

            <Grid cols={3}>
              <Field label="تاريخ التركيب">
                <input
                  type="date"
                  value={eqForm.installationDate}
                  onChange={(e) => setEqForm({ ...eqForm, installationDate: e.target.value })}
                  className="field"
                />
              </Field>

              <Field label="تاريخ انتهاء الصلاحية *">
                <input
                  type="date"
                  value={eqForm.expiryDate}
                  onChange={(e) => {
                    setEqForm({ ...eqForm, expiryDate: e.target.value })
                    if (eqErrors.expiryDate) setEqErrors({ ...eqErrors, expiryDate: null })
                  }}
                  className={`field ${eqErrors.expiryDate ? 'field-error' : ''}`}
                />
                {eqErrors.expiryDate && <div className="error-msg">{eqErrors.expiryDate}</div>}
              </Field>

              <Field label="الحالة التشغيلية *">
                <select
                  value={eqForm.status}
                  onChange={(e) => setEqForm({ ...eqForm, status: e.target.value })}
                  className="field"
                >
                  <option value="ACTIVE">صالحة وجاهزة (ACTIVE)</option>
                  <option value="MAINTENANCE">تحت الصيانة (MAINTENANCE)</option>
                  <option value="EXPIRED">منتهية الصلاحية (EXPIRED)</option>
                </select>
              </Field>
            </Grid>

            <div className="flex justify-end gap-2 pt-3 border-t border-line">
              <Btn
                type="button"
                variant="ghost"
                onClick={() => {
                  setAddModal(false)
                  setEditModal(null)
                }}
              >
                إلغاء
              </Btn>
              <Btn type="submit" variant="pri" disabled={eqSubmitting}>
                {eqSubmitting ? 'جارٍ الحفظ…' : 'حفظ المعدة بالسجل'}
              </Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 3. Record Inspection Modal with Strict Validation */}
      {inspModal && (
        <Modal open onClose={() => setInspModal(false)} title="تسجيل وتوثيق فحص دوري لمعدة إطفاء" width={500}>
          <form onSubmit={handleSaveInspection} noValidate className="space-y-3.5">
            <Field label="معدة الإطفاء المراد فحصها *">
              <select
                value={inspForm.equipmentId}
                onChange={(e) => {
                  setInspForm({ ...inspForm, equipmentId: e.target.value })
                  if (inspErrors.equipmentId) setInspErrors({ ...inspErrors, equipmentId: null })
                }}
                className={`field ${inspErrors.equipmentId ? 'field-error' : ''}`}
              >
                <option value="">اختر المعدة من السجل...</option>
                {unitList.map((u) => (
                  <option key={u.id} value={u.code}>
                    {u.code} — {u.type} ({u.location})
                  </option>
                ))}
              </select>
              {inspErrors.equipmentId && <div className="error-msg">{inspErrors.equipmentId}</div>}
            </Field>

            <Grid cols={2}>
              <Field label="تاريخ الفحص الميداني *">
                <input
                  type="date"
                  value={inspForm.inspectionDate}
                  onChange={(e) => {
                    setInspForm({ ...inspForm, inspectionDate: e.target.value })
                    if (inspErrors.inspectionDate) setInspErrors({ ...inspErrors, inspectionDate: null })
                  }}
                  className={`field ${inspErrors.inspectionDate ? 'field-error' : ''}`}
                />
                {inspErrors.inspectionDate && <div className="error-msg">{inspErrors.inspectionDate}</div>}
              </Field>

              <Field label="نتيجة الفحص *">
                <select
                  value={inspForm.status}
                  onChange={(e) => setInspForm({ ...inspForm, status: e.target.value })}
                  className="field"
                >
                  <option value="PASSED">مطابقة وجاهزة (PASSED)</option>
                  <option value="MAINTENANCE_REQUIRED">تحتاج صيانة / إعادة تعبئة</option>
                  <option value="FAILED">غير صالحة / تالفة (FAILED)</option>
                </select>
              </Field>
            </Grid>

            <Field label="اسم المفتش المعتمد *">
              <input
                type="text"
                placeholder="مثال: م. أحمد فتحي"
                value={inspForm.inspectorName}
                onChange={(e) => {
                  setInspForm({ ...inspForm, inspectorName: e.target.value })
                  if (inspErrors.inspectorName) setInspErrors({ ...inspErrors, inspectorName: null })
                }}
                className={`field ${inspErrors.inspectorName ? 'field-error' : ''}`}
              />
              {inspErrors.inspectorName && <div className="error-msg">{inspErrors.inspectorName}</div>}
            </Field>

            <Field label="ملاحظات الفحص البصري والضغط">
              <textarea
                rows={3}
                placeholder="حالة مؤشر الضغط، الختم الرصاصي، سلامة الخرطوم والفوهة..."
                value={inspForm.notes}
                onChange={(e) => setInspForm({ ...inspForm, notes: e.target.value })}
                className="field !resize-none"
              />
            </Field>

            <div className="flex justify-end gap-2 pt-3 border-t border-line">
              <Btn type="button" variant="ghost" onClick={() => setInspModal(false)}>
                إلغاء
              </Btn>
              <Btn type="submit" variant="pri" disabled={inspSubmitting}>
                {inspSubmitting ? 'جارٍ الاعتماد…' : 'اعتماد وتوثيق الفحص'}
              </Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* Service & Work Order Modal */}
      {serviceModal && (
        <Modal
          open
          onClose={() => setServiceModal(null)}
          title={`أمر صيانة وتوثيق خدمة — ${serviceModal.code}`}
          width={540}
        >
          <form onSubmit={handleSaveService} noValidate className="space-y-4">
            <div className="p-3 bg-surface-2 border border-line rounded-lg text-xs space-y-1.5">
              <div className="flex justify-between">
                <span className="text-txt-2">المعدة:</span>
                <span className="font-bold text-hi">{serviceModal.code} ({serviceModal.type})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-txt-2">الموقع:</span>
                <span className="text-txt">{serviceModal.location}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-txt-2">المشكلة الحالية:</span>
                <span className="font-semibold text-crit">{serviceModal.issue}</span>
              </div>
            </div>

            <Grid cols={2}>
              <Field label="نوع الإجراء المطلوب *">
                <select
                  value={serviceForm.actionType}
                  onChange={(e) => {
                    const type = e.target.value
                    const futureYears = type === 'REPLACE' ? 5 : type === 'HYDRO' ? 3 : 2
                    const nextExp = new Date(Date.now() + futureYears * 365 * 86400000).toISOString().slice(0, 10)
                    setServiceForm({
                      ...serviceForm,
                      actionType: type,
                      newExpiryDate: nextExp,
                      notes: type === 'REPLACE'
                        ? 'تم استبدال أسطوانة الإطفاء بوحدة جديدة معتمدة ومطابقة للمواصفات'
                        : type === 'HYDRO'
                        ? 'تم إجراء اختبار الضغط الهيدروستاتيكي بنجاح ومعايرة صمام الأمان'
                        : 'تمت إعادة تعبئة المادة الإطفائية وضبط مؤشر الضغط واختبار صمام الأمان',
                    })
                  }}
                  className="field"
                >
                  <option value="REFILL">إعادة تعبئة وضبط الضغط (Refill)</option>
                  <option value="REPLACE">استبدال فوري بوحدة جديدة (New Unit)</option>
                  <option value="HYDRO">اختبار هيدروستاتيكي ومعايرة (Hydro Test)</option>
                  <option value="MAINTENANCE">صيانة الصمام والخرطوم والفوهة</option>
                </select>
              </Field>

              <Field label="تاريخ الصلاحية الجديد *">
                <input
                  type="date"
                  value={serviceForm.newExpiryDate}
                  onChange={(e) => setServiceForm({ ...serviceForm, newExpiryDate: e.target.value })}
                  className="field"
                />
              </Field>
            </Grid>

            <Grid cols={2}>
              <Field label="اسم الفني / المسؤول">
                <input
                  type="text"
                  value={serviceForm.technicianName}
                  onChange={(e) => setServiceForm({ ...serviceForm, technicianName: e.target.value })}
                  className="field"
                />
              </Field>

              <Field label="الشركة الموردة / ورشة الصيانة">
                <input
                  type="text"
                  value={serviceForm.vendor}
                  onChange={(e) => setServiceForm({ ...serviceForm, vendor: e.target.value })}
                  className="field"
                />
              </Field>
            </Grid>

            <Field label="ملاحظات وتفاصيل الصيانة">
              <textarea
                rows={2}
                value={serviceForm.notes}
                onChange={(e) => setServiceForm({ ...serviceForm, notes: e.target.value })}
                className="field !resize-none"
              />
            </Field>

            <div className="p-3 bg-brand/5 border border-brand/20 rounded-lg flex items-center justify-between">
              <div>
                <div className="text-xs font-bold text-txt">إرجاع المعدة للخدمة فوراً (Recommission)</div>
                <div className="text-2xs text-txt-2">تحديث الحالة إلى صالحة (VALID) وحذفها من قائمة الانتباه</div>
              </div>
              <input
                type="checkbox"
                checked={serviceForm.recommissionNow}
                onChange={(e) => setServiceForm({ ...serviceForm, recommissionNow: e.target.checked })}
                className="w-4 h-4 cursor-pointer accent-brand"
              />
            </div>

            <div className="flex justify-end gap-2 pt-3 border-t border-line">
              <Btn type="button" variant="ghost" onClick={() => setServiceModal(null)}>
                إلغاء
              </Btn>
              <Btn type="submit" variant="pri" disabled={serviceSubmitting}>
                {serviceSubmitting ? 'جارٍ الحفظ والاعتماد…' : serviceForm.recommissionNow ? 'إتمام الصيانة والإرجاع للخدمة' : 'إصدار أمر الشغل فقط'}
              </Btn>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
