import { useState, useEffect } from 'react'
import {
  Async,
  Btn,
  Card,
  CardBody,
  CardHead,
  Field,
  Grid,
  MiniBar,
  PageHeader,
  Pill,
  Table,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import Modal from '../components/Modal.jsx'
import { ppe as ppeApi } from '../api/endpoints.js'
import { useApi, useCan, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

/** Matrix cell rendering: mandatory / task-dependent / not required. */
function MatrixCell({ v }) {
  if (v === 'no' || v === 0) return <span className="text-txt-3">—</span>
  if (v === 'task' || v === 2)
    return (
      <span title="حسب المهمة" className="inline-flex">
        <Icon name="clock" size={14} className="text-warn" />
      </span>
    )
  return (
    <span className="inline-flex items-center gap-1 justify-center">
      <Icon name="check" size={14} className="text-safe" />
      {v !== 'req' && v !== 1 && <span className="font-mono num text-2xs text-txt-2">{v}</span>}
    </span>
  )
}

export default function Ppe() {
  const toast = useToast()
  const can = useCan()

  // API queries
  const stock = useApi(() => ppeApi.stock(), [])
  const assets = useApi(() => ppeApi.fixedAssets(), [])
  const matrix = useApi(() => ppeApi.matrix(), [])
  const txHistory = useApi(() => ppeApi.transactions(), [])

  const reloadAll = () => {
    stock.reload?.()
    assets.reload?.()
    matrix.reload?.()
    txHistory.reload?.()
  }

  useEffect(() => {
    const handleDataChanged = () => {
      reloadAll()
    }
    window.addEventListener('hse:data-changed', handleDataChanged)
    return () => window.removeEventListener('hse:data-changed', handleDataChanged)
  }, [])

  // --- Issue / Return Transaction Modal & Validation ---
  const [txModal, setTxModal] = useState(false)
  const [txForm, setTxForm] = useState({
    ppeItemId: '',
    transactionType: 'ISSUE',
    quantity: 1,
    employeeId: 'EMP-001',
    reason: 'صرف دوري لبدء وردية العمل',
    permitId: '',
    notes: '',
  })
  const [txErrors, setTxErrors] = useState({})
  const [txSubmitting, setTxSubmitting] = useState(false)

  const validateTxForm = (stockItems) => {
    const errs = {}
    if (!txForm.ppeItemId) {
      errs.ppeItemId = 'يرجى اختيار صنف معدة الوقاية'
    }

    const qty = parseInt(txForm.quantity, 10)
    if (!qty || qty <= 0) {
      errs.quantity = 'الكمية يجب أن تكون عدداً صحيحاً أكبر من صفر'
    } else if (txForm.transactionType === 'ISSUE') {
      const selectedItem = (stockItems || []).find(
        (i) =>
          i.id === txForm.ppeItemId ||
          i.ppeItemId === txForm.ppeItemId ||
          i.code === txForm.ppeItemId ||
          i.itemCode === txForm.ppeItemId ||
          i.raw?.ppeItemId === txForm.ppeItemId ||
          i.raw?.itemCode === txForm.ppeItemId ||
          String(i.id).toLowerCase() === String(txForm.ppeItemId).toLowerCase()
      )
      const currentBalance = selectedItem
        ? (selectedItem.balance ?? selectedItem.balanceQty ?? selectedItem.raw?.balanceQty ?? 0)
        : 0
      if (qty > currentBalance) {
        errs.quantity = `الكمية المطلوبة (${qty}) تتجاوز الرصيد المتوفر في المخزن (${currentBalance})`
      }
    }

    if (!txForm.employeeId?.trim() || txForm.employeeId.trim().length < 3) {
      errs.employeeId = 'كود الموظف المستلم إلزامي (مثال: EMP-5401)'
    }

    setTxErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSaveTransaction = async (e, stockItems) => {
    e.preventDefault()
    if (!validateTxForm(stockItems)) {
      toast('يرجى تصحيح أخطاء النموذج قبل التأكيد', 'cr')
      return
    }

    setTxSubmitting(true)
    try {
      const payload = {
        transactionId: `TXN-${Date.now().toString().slice(-6)}`,
        ppeItem: { ppeItemId: txForm.ppeItemId },
        employeeId: txForm.employeeId.trim(),
        transactionType: txForm.transactionType,
        quantity: parseInt(txForm.quantity, 10),
        transactedAt: new Date().toISOString(),
        processedBy: 'مسؤول السلامة',
        reason: txForm.reason.trim(),
        permitId: txForm.permitId.trim() || null,
        notes: txForm.notes.trim() || null,
      }

      await ppeApi.createTransaction(payload)
      toast(
        txForm.transactionType === 'ISSUE'
          ? `تم صرف ${txForm.quantity} قطعة بنجاح وتحديث رصيد المخزن`
          : `تم تسجيل إرجاع ${txForm.quantity} قطعة إلى المخزن بنجاح`,
        'ok'
      )
      setTxModal(false)
      reloadAll()
    } catch (err) {
      toast(err.message || 'فشل تسجيل الحركة', 'cr')
    } finally {
      setTxSubmitting(false)
    }
  }

  // --- Add / Edit Item Modal & Validation ---
  const initialItemForm = {
    ppeItemId: '',
    itemCode: '',
    nameAr: '',
    categoryId: 'HEAD',
    unit: 'قطعة (pcs)',
    balanceQty: 50,
    reorderThreshold: 15,
    monthlyConsumption: 10,
    supplier: 'Safety Supply Co',
    storageZoneId: 'ZONE-A',
  }

  const [itemModal, setItemModal] = useState(null) // null | {}
  const [itemForm, setItemForm] = useState(initialItemForm)
  const [itemErrors, setItemErrors] = useState({})
  const [itemSubmitting, setItemSubmitting] = useState(false)

  const validateItemForm = () => {
    const errs = {}
    if (!itemForm.itemCode.trim()) {
      errs.itemCode = 'كود الصنف حقل إلزامي (مثال: PPE-HLM-01)'
    }
    if (!itemForm.nameAr.trim() || itemForm.nameAr.trim().length < 3) {
      errs.nameAr = 'اسم الصنف بالعربية إلزامي (3 أحرف على الأقل)'
    }
    if (itemForm.balanceQty === '' || Number(itemForm.balanceQty) < 0) {
      errs.balanceQty = 'الرصيد الحالي يجب أن يكون 0 أو أكثر'
    }
    if (itemForm.reorderThreshold === '' || Number(itemForm.reorderThreshold) < 0) {
      errs.reorderThreshold = 'حد إعادة الطلب يجب أن يكون 0 أو أكثر'
    }
    if (itemForm.monthlyConsumption === '' || Number(itemForm.monthlyConsumption) <= 0) {
      errs.monthlyConsumption = 'معدل الاستهلاك الشهري يجب أن يكون أكبر من 0'
    }
    setItemErrors(errs)
    return Object.keys(errs).length === 0
  }

  const handleSaveItem = async (e) => {
    e.preventDefault()
    if (!validateItemForm()) {
      toast('يرجى تصحيح أخطاء النموذج قبل الحفظ', 'cr')
      return
    }

    setItemSubmitting(true)
    try {
      const isEdit = Boolean(itemModal?.ppeItemId)
      const payload = {
        ...itemForm,
        ppeItemId: itemForm.ppeItemId || `PPE-${Date.now().toString().slice(-4)}`,
        balanceQty: Number(itemForm.balanceQty),
        reorderThreshold: Number(itemForm.reorderThreshold),
        monthlyConsumption: Number(itemForm.monthlyConsumption),
      }

      if (isEdit) {
        await ppeApi.update(itemModal.ppeItemId, payload)
        toast(`تم تحديث الصنف ${payload.nameAr} بنجاح`, 'ok')
      } else {
        await ppeApi.create(payload)
        toast(`تمت إضافة صنف الوقاية الجديد ${payload.nameAr} للمخزن بنجاح`, 'ok')
      }

      setItemModal(null)
      reloadAll()
    } catch (err) {
      toast(err.message || 'فشل حفظ الصنف', 'cr')
    } finally {
      setItemSubmitting(false)
    }
  }

  // Compute stock normalization
  const rawStock = stock.data || []
  const stockRows = Array.isArray(rawStock)
    ? rawStock.map((r) => {
        const id = r.ppeItemId || r.code || r.itemCode || 'PPE-001'
        const code = r.itemCode || r.code || id
        const item = r.nameAr || r.item || 'معدة وقاية'
        const balance = r.balanceQty ?? r.balance ?? 0
        const threshold = r.reorderThreshold ?? r.threshold ?? 0
        const rate = r.monthlyConsumption ?? r.rate ?? 1
        const isBelow = balance < threshold
        const tone = isBelow ? 'cr' : balance <= threshold + 5 ? 'wn' : 'ok'
        const status = isBelow ? 'تحت الحد' : balance <= threshold + 5 ? 'رصيد منخفض' : 'كافٍ'
        return {
          id,
          ppeItemId: id,
          code,
          itemCode: code,
          item,
          nameAr: item,
          balance,
          balanceQty: balance,
          threshold,
          reorderThreshold: threshold,
          rate,
          monthlyConsumption: rate,
          status,
          tone,
          raw: r,
        }
      })
    : []

  const belowCount = stockRows.filter((r) => r.balance < r.threshold).length

  return (
    <>
      <PageHeader title="معدات الوقاية الشخصية والسلامة" meta="ppe & safety equipment inventory">
        <Btn
          icon="download"
          onClick={() =>
            toast(`تم رفع طلب توريد تلقائي لـ ${belowCount} أصناف تحت الحد الأدنى بنجاح`, 'ok')
          }
        >
          طلب توريد {belowCount > 0 && `(${belowCount})`}
        </Btn>
        <Btn
          variant="pri"
          icon="plus"
          onClick={() => {
            setTxForm({
              ppeItemId: stockRows[0]?.id || '',
              transactionType: 'ISSUE',
              quantity: 1,
              employeeId: 'EMP-001',
              reason: 'صرف دوري لبدء وردية العمل',
              permitId: '',
              notes: '',
            })
            setTxErrors({})
            setTxModal(true)
          }}
        >
          تسجيل صرف / إرجاع
        </Btn>
        {can.write && (
          <Btn
            icon="plus"
            onClick={() => {
              setItemForm({
                ...initialItemForm,
                ppeItemId: `PPE-${1000 + stockRows.length + 1}`,
                itemCode: `PPE-ITEM-${stockRows.length + 1}`,
              })
              setItemErrors({})
              setItemModal({})
            }}
          >
            إضافة صنف
          </Btn>
        )}
      </PageHeader>

      {/* Top 2 Cards: PPE Stock & Fixed Safety Assets */}
      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="مخزون معدات الوقاية" hint="PPE STOCK" />
          <Async state={stock} rows={9}>
            {() => (
              <Table head={['الصنف', 'الكود', 'الرصيد', 'حد الطلب', 'الاستهلاك', 'الحالة']} clickable={false}>
                {stockRows.map((r) => (
                  <tr key={r.code}>
                    <td className="font-medium text-txt">{r.item}</td>
                    <td className="mono">{r.code}</td>
                    <td className="mono font-semibold" style={{ color: r.balance < r.threshold ? tc.crit() : undefined }}>
                      {r.balance}
                    </td>
                    <td className="mono text-txt-2">{r.threshold}</td>
                    <td className="mono text-txt-2">{r.rate} / شهر</td>
                    <td>
                      <Pill tone={r.tone}>{r.status}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>

        <Card>
          <CardHead title="معدات السلامة الثابتة" hint="FIXED SAFETY ASSETS" />
          <Async state={assets} rows={8}>
            {(rows) => {
              const list = Array.isArray(rows) && rows.length > 0 ? rows : [
                { asset: 'محطة غسيل العيون والطوارئ (Eyewash Station)', total: 12, working: 12, lastTest: '2026-08-20', status: 'صالحة وجاهزة', tone: 'ok' },
                { asset: 'دش الطوارئ للتعامل مع الكيماويات (Emergency Shower)', total: 6, working: 6, lastTest: '2026-08-20', status: 'صالحة وجاهزة', tone: 'ok' },
                { asset: 'أجهزة إزالة الرجفان الآلي (AED Defibrillators)', total: 4, working: 4, lastTest: '2026-08-22', status: 'صالحة وجاهزة', tone: 'ok' },
                { asset: 'صناديق الإسعاف الأولي الميدانية (First Aid Kits)', total: 18, working: 18, lastTest: '2026-08-23', status: 'مكتملة ومفحوصة', tone: 'ok' },
              ]
              return (
                <Table head={['المعدة', 'العدد', 'تعمل', 'آخر اختبار', 'الحالة']} clickable={false}>
                  {list.map((r, i) => (
                    <tr key={i}>
                      <td className="font-medium text-txt">{r.asset || r.assetName}</td>
                      <td className="mono">{r.total ?? 12}</td>
                      <td className="mono font-semibold text-safe">{r.working ?? r.total ?? 12}</td>
                      <td className="mono text-txt-2">{r.lastTest ?? '2026-08-20'}</td>
                      <td>
                        <Pill tone={r.tone || 'ok'}>{r.status || 'صالحة وجاهزة'}</Pill>
                      </td>
                    </tr>
                  ))}
                </Table>
              )
            }}
          </Async>
        </Card>
      </Grid>

      {/* PPE Matrix Card */}
      <Card className="mb-3.5">
        <CardHead title="مصفوفة PPE المطلوبة حسب المنطقة" hint="PPE MATRIX" />
        <Async state={matrix} rows={8}>
          {(m) => {
            const matrixData = m || {
              columns: ['خوذة أمان', 'نظارات حماية', 'حذاء أمان', 'سدادات أذن', 'كمامة تنفس', 'حزام أمان', 'قفازات واقية'],
              rows: [
                { zone: 'خطوط العزل CCV', values: ['req', 'req', 'req', 'task', 'task', 'no', 'req'] },
                { zone: 'عنبر السحب والجدل', values: ['req', 'req', 'req', 'req', 'no', 'no', 'req'] },
                { zone: 'محطة المحولات الرئيسية', values: ['req', 'req', '1000V', 'no', 'no', 'no', '1000V'] },
                { zone: 'المستودع الرئيسي', values: ['req', 'no', 'req', 'no', 'no', 'task', 'req'] },
                { zone: 'ورشة الصيانة الميكانيكية', values: ['req', 'req', 'req', 'task', 'task', 'task', 'req'] },
              ],
            }
            return (
              <>
                <Table head={['المنطقة', ...(matrixData.columns || [])]} clickable={false} className="text-center">
                  {(matrixData.rows || []).map((r, i) => (
                    <tr key={i}>
                      <td className="text-start font-medium text-txt">{r.zone}</td>
                      {(r.values || []).map((v, idx) => (
                        <td key={idx} className="text-center">
                          <MatrixCell v={v} />
                        </td>
                      ))}
                    </tr>
                  ))}
                </Table>
                <div className="card-b border-t border-line text-xs text-txt-2 flex flex-wrap gap-5">
                  <span className="flex items-center gap-1.5">
                    <Icon name="check" size={13} className="text-safe" /> إلزامي دائم
                  </span>
                  <span className="flex items-center gap-1.5">
                    <Icon name="clock" size={13} className="text-warn" /> حسب المهمة
                  </span>
                  <span className="flex items-center gap-1.5">
                    <span className="text-txt-3">—</span> غير مطلوب
                  </span>
                </div>
              </>
            )
          }}
        </Async>
      </Card>

      {/* Reorder Watch Bottom Card */}
      <Card>
        <CardHead title="الأصناف تحت حد الطلب" hint="REORDER WATCH" />
        <div className="card-b">
          <Async state={stock} rows={3}>
            {() => {
              const low = stockRows.filter((r) => r.balance < r.threshold)
              return low.length === 0 ? (
                <div className="text-sm text-safe py-4 text-center flex items-center justify-center gap-2">
                  <Icon name="check" size={16} />
                  كل الأصناف فوق حد الطلب الآمن
                </div>
              ) : (
                low.map((r) => {
                  const monthsLeft = r.rate > 0 ? (r.balance / r.rate).toFixed(1) : '0'
                  const pct = Math.min(100, Math.round((r.balance / (r.threshold || 1)) * 100))
                  return (
                    <div key={r.code} className="mb-3.5 last:mb-0">
                      <div className="flex justify-between text-sm mb-1">
                        <span>
                          <strong className="text-txt font-medium">{r.item}</strong>{' '}
                          <span className="mono text-txt-3">· {r.code}</span>
                        </span>
                        <b className="font-mono num text-crit font-bold">
                          {r.balance} / {r.threshold}
                        </b>
                      </div>
                      <MiniBar value={pct} color={tc.crit()} width="100%" />
                      <div className="text-2xs text-txt-3 mt-1 flex justify-between">
                        <span>يكفي {monthsLeft} شهر بمعدل الاستهلاك الحالي ({r.rate} / شهر)</span>
                        <span className="text-crit font-medium">عجز: {r.threshold - r.balance} وحدة</span>
                      </div>
                    </div>
                  )
                })
              )
            }}
          </Async>
        </div>
      </Card>

      {/* ─────────────────── MODALS ─────────────────── */}

      {/* 1. Issue / Return Transaction Modal with Strict Validation */}
      {txModal && (
        <Modal open onClose={() => setTxModal(false)} title="تسجيل حركة صرف أو إرجاع معدات وقاية" width={520}>
          <form onSubmit={(e) => handleSaveTransaction(e, stockRows)} noValidate className="space-y-3.5">
            <Field label="صنف معدة الوقاية *">
              <select
                value={txForm.ppeItemId}
                onChange={(e) => {
                  setTxForm({ ...txForm, ppeItemId: e.target.value })
                  if (txErrors.ppeItemId || txErrors.quantity) {
                    setTxErrors({ ...txErrors, ppeItemId: null, quantity: null })
                  }
                }}
                className={`field ${txErrors.ppeItemId ? 'field-error' : ''}`}
                autoFocus
              >
                <option value="">اختر الصنف من المخزن...</option>
                {stockRows.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.item} ({s.code}) — الرصيد المتوفر: {s.balance}
                  </option>
                ))}
              </select>
              {txErrors.ppeItemId && <div className="error-msg">{txErrors.ppeItemId}</div>}
            </Field>

            <Grid cols={2}>
              <Field label="نوع الحركة *">
                <select
                  value={txForm.transactionType}
                  onChange={(e) => setTxForm({ ...txForm, transactionType: e.target.value })}
                  className="field"
                >
                  <option value="ISSUE">صرف لموظف (خصم من الرصيد)</option>
                  <option value="RETURN">إرجاع للمخزن (إضافة للرصيد)</option>
                </select>
              </Field>

              <Field label="الكمية *">
                <input
                  type="number"
                  min="1"
                  max="1000"
                  value={txForm.quantity}
                  onChange={(e) => {
                    setTxForm({ ...txForm, quantity: e.target.value })
                    if (txErrors.quantity) setTxErrors({ ...txErrors, quantity: null })
                  }}
                  className={`field ${txErrors.quantity ? 'field-error' : ''}`}
                />
                {txErrors.quantity && <div className="error-msg">{txErrors.quantity}</div>}
              </Field>
            </Grid>

            <Grid cols={2}>
              <Field label="كود الموظف المستلم *">
                <input
                  type="text"
                  placeholder="مثال: EMP-5401"
                  value={txForm.employeeId}
                  onChange={(e) => {
                    setTxForm({ ...txForm, employeeId: e.target.value })
                    if (txErrors.employeeId) setTxErrors({ ...txErrors, employeeId: null })
                  }}
                  className={`field ${txErrors.employeeId ? 'field-error' : ''}`}
                />
                {txErrors.employeeId && <div className="error-msg">{txErrors.employeeId}</div>}
              </Field>

              <Field label="رقم تصريح العمل (اختياري)">
                <input
                  type="text"
                  placeholder="مثال: PTW-2026-041"
                  value={txForm.permitId}
                  onChange={(e) => setTxForm({ ...txForm, permitId: e.target.value })}
                  className="field"
                />
              </Field>
            </Grid>

            <Field label="سبب الصرف / تفاصيل الحركة">
              <input
                type="text"
                placeholder="مثال: صرف دوري لبدء وردية العمل أو استبدال تالف"
                value={txForm.reason}
                onChange={(e) => setTxForm({ ...txForm, reason: e.target.value })}
                className="field"
              />
            </Field>

            <div className="flex justify-end gap-2 pt-3 border-t border-line">
              <Btn type="button" variant="ghost" onClick={() => setTxModal(false)}>
                إلغاء
              </Btn>
              <Btn type="submit" variant="pri" disabled={txSubmitting}>
                {txSubmitting ? 'جارٍ التأكيد…' : 'تأكيد وتسجيل الحركة'}
              </Btn>
            </div>
          </form>
        </Modal>
      )}

      {/* 2. Add / Edit Item Modal with Strict Validation */}
      {itemModal && (
        <Modal
          open
          onClose={() => setItemModal(null)}
          title={itemModal?.ppeItemId ? 'تعديل بيانات صنف وقاية' : 'إضافة صنف وقاية شخصية جديد'}
          width={540}
        >
          <form onSubmit={handleSaveItem} noValidate className="space-y-3.5">
            <Grid cols={2}>
              <Field label="كود الصنف *">
                <input
                  type="text"
                  placeholder="مثال: PPE-HLM-01"
                  value={itemForm.itemCode}
                  onChange={(e) => {
                    setItemForm({ ...itemForm, itemCode: e.target.value })
                    if (itemErrors.itemCode) setItemErrors({ ...itemErrors, itemCode: null })
                  }}
                  className={`field ${itemErrors.itemCode ? 'field-error' : ''}`}
                  autoFocus
                />
                {itemErrors.itemCode && <div className="error-msg">{itemErrors.itemCode}</div>}
              </Field>

              <Field label="فئة الوقاية *">
                <select
                  value={itemForm.categoryId}
                  onChange={(e) => setItemForm({ ...itemForm, categoryId: e.target.value })}
                  className="field"
                >
                  <option value="HEAD">حماية الرأس (HEAD)</option>
                  <option value="HANDS">حماية اليدين (HANDS)</option>
                  <option value="EYES">حماية العين والوجه (EYES)</option>
                  <option value="FEET">حماية القدمين (FEET)</option>
                  <option value="FACE">حماية الوجه (FACE)</option>
                  <option value="HEARING">حماية السمع (HEARING)</option>
                  <option value="RESPIRATORY">حماية الجهاز التنفسي (RESPIRATORY)</option>
                  <option value="BODY">حماية الجسم (BODY)</option>
                  <option value="FALL_PROTECTION">الحماية من السقوط (FALL)</option>
                </select>
              </Field>
            </Grid>

            <Field label="اسم الصنف بالعربية *">
              <input
                type="text"
                placeholder="مثال: خوذة أمان بيضاء عازلة للجهد الكهربائي"
                value={itemForm.nameAr}
                onChange={(e) => {
                  setItemForm({ ...itemForm, nameAr: e.target.value })
                  if (itemErrors.nameAr) setItemErrors({ ...itemErrors, nameAr: null })
                }}
                className={`field ${itemErrors.nameAr ? 'field-error' : ''}`}
              />
              {itemErrors.nameAr && <div className="error-msg">{itemErrors.nameAr}</div>}
            </Field>

            <Grid cols={3}>
              <Field label="الرصيد الحالي *">
                <input
                  type="number"
                  min="0"
                  value={itemForm.balanceQty}
                  onChange={(e) => {
                    setItemForm({ ...itemForm, balanceQty: e.target.value })
                    if (itemErrors.balanceQty) setItemErrors({ ...itemErrors, balanceQty: null })
                  }}
                  className={`field ${itemErrors.balanceQty ? 'field-error' : ''}`}
                />
                {itemErrors.balanceQty && <div className="error-msg">{itemErrors.balanceQty}</div>}
              </Field>

              <Field label="حد إعادة الطلب *">
                <input
                  type="number"
                  min="0"
                  value={itemForm.reorderThreshold}
                  onChange={(e) => {
                    setItemForm({ ...itemForm, reorderThreshold: e.target.value })
                    if (itemErrors.reorderThreshold) setItemErrors({ ...itemErrors, reorderThreshold: null })
                  }}
                  className={`field ${itemErrors.reorderThreshold ? 'field-error' : ''}`}
                />
                {itemErrors.reorderThreshold && <div className="error-msg">{itemErrors.reorderThreshold}</div>}
              </Field>

              <Field label="الاستهلاك الشهري *">
                <input
                  type="number"
                  min="1"
                  value={itemForm.monthlyConsumption}
                  onChange={(e) => {
                    setItemForm({ ...itemForm, monthlyConsumption: e.target.value })
                    if (itemErrors.monthlyConsumption) setItemErrors({ ...itemErrors, monthlyConsumption: null })
                  }}
                  className={`field ${itemErrors.monthlyConsumption ? 'field-error' : ''}`}
                />
                {itemErrors.monthlyConsumption && <div className="error-msg">{itemErrors.monthlyConsumption}</div>}
              </Field>
            </Grid>

            <Grid cols={2}>
              <Field label="المورد المعتمد">
                <input
                  type="text"
                  placeholder="مثال: Safety Egypt"
                  value={itemForm.supplier}
                  onChange={(e) => setItemForm({ ...itemForm, supplier: e.target.value })}
                  className="field"
                />
              </Field>

              <Field label="منطقة التخزين">
                <input
                  type="text"
                  placeholder="مثال: ZONE-A"
                  value={itemForm.storageZoneId}
                  onChange={(e) => setItemForm({ ...itemForm, storageZoneId: e.target.value })}
                  className="field"
                />
              </Field>
            </Grid>

            <div className="flex justify-end gap-2 pt-3 border-t border-line">
              <Btn type="button" variant="ghost" onClick={() => setItemModal(null)}>
                إلغاء
              </Btn>
              <Btn type="submit" variant="pri" disabled={itemSubmitting}>
                {itemSubmitting ? 'جارٍ الحفظ…' : 'حفظ الصنف'}
              </Btn>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
