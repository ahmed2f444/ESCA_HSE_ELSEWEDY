import { useState, useMemo } from 'react'
import Modal from '../../components/Modal.jsx'
import { Btn, Field } from '../../components/ui.jsx'
import { risk as riskApi } from '../../api/endpoints.js'
import { useToast } from '../../hooks.jsx'
import Icon from '../../components/Icon.jsx'

const ZONES = [
  'خطوط السحب والجدل',
  'ورشة الصيانة الميكانيكية',
  'المستودع الرئيسي والخامات',
  'محطة المحولات الرئيسية 11kV',
  'محطة التبريد المركزي',
  'خطوط العزل CCV',
  'رصيف الشحن والتفريغ',
  'معمل الجودة والاختبارات',
  'مبنى الخدمات الإدارية'
]

const OWNERS = [
  'م. أحمد عثمان — مهندس سلامة',
  'م. سامح فوزي — مهندس صيانة',
  'م. طارق كمال — مشرف موقع',
  'م. كريم حسني — مدير سلامة',
  'م. مصطفى محمد — رئيس قسم HSE'
]

const PROBABILITY_OPTIONS = [
  { value: 1, label: '1 - نادر (Rare)' },
  { value: 2, label: '2 - ضعيف (Unlikely)' },
  { value: 3, label: '3 - ممكن (Possible)' },
  { value: 4, label: '4 - مرجح (Likely)' },
  { value: 5, label: '5 - شبه مؤكد (Almost Certain)' }
]

const SEVERITY_OPTIONS = [
  { value: 1, label: '1 - ضئيل (Insignificant)' },
  { value: 2, label: '2 - بسيط (Minor)' },
  { value: 3, label: '3 - متوسط (Moderate)' },
  { value: 4, label: '4 - كبير (Major)' },
  { value: 5, label: '5 - كارثي (Catastrophic)' }
]

const getRiskMeta = (score) => {
  if (score >= 20) return { label: 'حرج', color: '#8E1F17', bg: 'rgba(142, 31, 23, 0.2)', border: 'rgba(142, 31, 23, 0.5)' }
  if (score >= 15) return { label: 'عالي', color: '#E0483C', bg: 'rgba(224, 72, 60, 0.2)', border: 'rgba(224, 72, 60, 0.5)' }
  if (score >= 10) return { label: 'متوسط', color: '#F09030', bg: 'rgba(240, 144, 48, 0.2)', border: 'rgba(240, 144, 48, 0.5)' }
  if (score >= 5) return { label: 'منخفض', color: '#C6C43A', bg: 'rgba(198, 196, 58, 0.2)', border: 'rgba(198, 196, 58, 0.5)' }
  return { label: 'مقبول', color: '#38B87C', bg: 'rgba(56, 184, 124, 0.2)', border: 'rgba(56, 184, 124, 0.5)' }
}

const initialForm = {
  hazard: '',
  activity: '',
  zone: ZONES[0],
  customZone: '',
  owner: OWNERS[0],
  customOwner: '',
  probability: 3,
  severity: 3,
  controls: '',
  residual_likelihood: 1,
  residual_severity: 2
}

export default function RiskForm({ open, onClose, onSuccess }) {
  const toast = useToast()
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState(initialForm)
  const [errors, setErrors] = useState({})
  const [touched, setTouched] = useState({})

  const inherentScore = useMemo(() => Number(form.probability) * Number(form.severity), [form.probability, form.severity])
  const inherentMeta = useMemo(() => getRiskMeta(inherentScore), [inherentScore])

  const residualScore = useMemo(() => Number(form.residual_likelihood) * Number(form.residual_severity), [form.residual_likelihood, form.residual_severity])
  const residualMeta = useMemo(() => getRiskMeta(residualScore), [residualScore])

  const handleChange = (e) => {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const handleBlur = (name) => {
    setTouched(prev => ({ ...prev, [name]: true }))
    validateField(name, form[name])
  }

  const validateField = (name, value) => {
    let err = ''
    if (name === 'hazard' && (!value || !value.trim())) {
      err = 'وصف الخطر إلزامي'
    } else if (name === 'activity' && (!value || !value.trim())) {
      err = 'النشاط المرتبط إلزامي'
    } else if (name === 'controls' && (!value || !value.trim())) {
      err = 'ضوابط وإجراءات التحكم إلزامية'
    }
    setErrors(prev => ({ ...prev, [name]: err }))
    return !err
  }

  const validateAll = () => {
    const errs = {}
    if (!form.hazard?.trim()) errs.hazard = 'يرجى إدخال وصف تفصيلي للخطر'
    if (!form.activity?.trim()) errs.activity = 'يرجى تحديد النشاط التشغيلي المرتبط'
    if (!form.controls?.trim()) errs.controls = 'يرجى تحديد إجراءات وضوابط التحكم المطبقة'
    if (form.zone === 'OTHER' && !form.customZone?.trim()) errs.zone = 'يرجى كتابة اسم المنطقة'
    if (form.owner === 'OTHER' && !form.customOwner?.trim()) errs.owner = 'يرجى كتابة اسم المسؤول'
    
    setErrors(errs)
    setTouched({ hazard: true, activity: true, controls: true, zone: true, owner: true })
    return Object.keys(errs).length === 0
  }

  const handleSubmit = async (e) => {
    if (e?.preventDefault) e.preventDefault()
    if (!validateAll()) {
      toast('يرجى تصحيح الأخطاء واستكمال الحقول الإلزامية', 'cr')
      return
    }

    setLoading(true)
    try {
      const finalZone = form.zone === 'OTHER' ? form.customZone.trim() : form.zone
      const finalOwner = form.owner === 'OTHER' ? form.customOwner.trim() : form.owner

      const payload = {
        hazard: form.hazard.trim(),
        activity: form.activity.trim(),
        zone: finalZone,
        owner: finalOwner,
        probability: Number(form.probability),
        severity: Number(form.severity),
        controls: form.controls.trim(),
        residual_likelihood: Number(form.residual_likelihood),
        residual_severity: Number(form.residual_severity),
        residual: residualScore
      }

      await riskApi.create(payload)
      toast('تم تسجيل تقييم المخاطر (HIRA) بنجاح في قاعدة البيانات', 'ok')
      setForm(initialForm)
      setErrors({})
      setTouched({})
      onSuccess?.()
      onClose()
    } catch (err) {
      console.error('Risk creation error:', err)
      toast(err.message || 'تعذر حفظ تقييم المخاطر، تحقق من اتصال الخادم', 'cr')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="تقييم مخاطر جديد — Hazard Identification & Risk Assessment (HIRA)"
      width={720}
      footer={
        <>
          <Btn variant="pri" onClick={handleSubmit} disabled={loading} className="px-5">
            <Icon name="check" size={15} />
            {loading ? 'جارٍ الحفظ والتوثيق…' : 'حفظ وتقييد الخطر'}
          </Btn>
          <Btn onClick={onClose} disabled={loading}>
            إلغاء
          </Btn>
        </>
      }
    >
      <form onSubmit={handleSubmit} noValidate>
        {/* Step Header */}
        <div className="mb-5 pb-3 border-b border-line flex items-center justify-between">
          <div>
            <div className="text-xs font-semibold text-txt">نموذج تقييم وتحليل المخاطر الشامل</div>
            <div className="text-[11px] text-txt-3">سجل المخاطر التشغيلية والبيئية وفق معايير ISO 45001</div>
          </div>
          <span className="pill p-in text-xs font-mono">HIRA-FORM</span>
        </div>

        {/* Hazard & Activity */}
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <Field label="الخطر المحدد (Hazard Identification) *" className="mb-0">
            <input
              type="text"
              name="hazard"
              value={form.hazard}
              onChange={handleChange}
              onBlur={() => handleBlur('hazard')}
              placeholder="مثال: تطاير أجزاء معدنية ساخنة، تسرب زيت هيدروليك..."
              className={`field ${touched.hazard && errors.hazard ? 'field-error' : ''}`}
            />
            {touched.hazard && errors.hazard && (
              <div className="error-msg text-crit text-xs mt-1 flex items-center gap-1">
                <Icon name="incident" size={12} /> {errors.hazard}
              </div>
            )}
          </Field>

          <Field label="النشاط أو المهمة التشغيلية (Activity) *" className="mb-0">
            <input
              type="text"
              name="activity"
              value={form.activity}
              onChange={handleChange}
              onBlur={() => handleBlur('activity')}
              placeholder="مثال: أعمال لحام القوس الكهربائي، تنظيف الخزانات..."
              className={`field ${touched.activity && errors.activity ? 'field-error' : ''}`}
            />
            {touched.activity && errors.activity && (
              <div className="error-msg text-crit text-xs mt-1 flex items-center gap-1">
                <Icon name="incident" size={12} /> {errors.activity}
              </div>
            )}
          </Field>
        </div>

        {/* Zone & Owner */}
        <div className="grid sm:grid-cols-2 gap-4 mb-4">
          <Field label="موقع العمل / المنطقة (Plant Zone) *" className="mb-0">
            <select
              name="zone"
              value={form.zone}
              onChange={handleChange}
              className="field"
            >
              {ZONES.map(z => <option key={z} value={z}>{z}</option>)}
              <option value="OTHER">منطقة أخرى (إدخال يدوي)...</option>
            </select>
            {form.zone === 'OTHER' && (
              <input
                type="text"
                name="customZone"
                value={form.customZone}
                onChange={handleChange}
                placeholder="أدخل اسم المنطقة..."
                className="field mt-2"
              />
            )}
          </Field>

          <Field label="المسؤول المتابع (Risk Owner) *" className="mb-0">
            <select
              name="owner"
              value={form.owner}
              onChange={handleChange}
              className="field"
            >
              {OWNERS.map(o => <option key={o} value={o}>{o}</option>)}
              <option value="OTHER">مسؤول آخر (إدخال يدوي)...</option>
            </select>
            {form.owner === 'OTHER' && (
              <input
                type="text"
                name="customOwner"
                value={form.customOwner}
                onChange={handleChange}
                placeholder="اسم المسؤول وصفته..."
                className="field mt-2"
              />
            )}
          </Field>
        </div>

        {/* Inherent Risk Calculation Section */}
        <div className="p-3.5 bg-steel-3/50 border border-line rounded-lg mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-txt flex items-center gap-1.5">
              <Icon name="chart" size={14} className="text-hi" />
              التقييم الأولي للخطر (Inherent Risk Rating)
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-txt-3">الدرجة المحسوبة:</span>
              <span
                className="px-2.5 py-0.5 rounded text-xs font-bold font-mono"
                style={{
                  color: inherentMeta.color,
                  backgroundColor: inherentMeta.bg,
                  border: `1px solid ${inherentMeta.border}`
                }}
              >
                {inherentScore} — {inherentMeta.label}
              </span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="الاحتمالية الأولية (Likelihood)" className="mb-0">
              <select
                name="probability"
                value={form.probability}
                onChange={handleChange}
                className="field font-mono"
              >
                {PROBABILITY_OPTIONS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </Field>

            <Field label="الشدة الأولية (Severity)" className="mb-0">
              <select
                name="severity"
                value={form.severity}
                onChange={handleChange}
                className="field font-mono"
              >
                {SEVERITY_OPTIONS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </Field>
          </div>
        </div>

        {/* Controls */}
        <div className="mb-4">
          <Field label="إجراءات وضوابط التحكم المطبقة (Hierarchy of Controls) *" className="mb-0">
            <textarea
              name="controls"
              rows={3}
              value={form.controls}
              onChange={handleChange}
              onBlur={() => handleBlur('controls')}
              placeholder="مثال: تطبيق عزل الطاقة LOTO، إلزام بارتداء مهمات الوقاية الكاملة (PPE)، توفير ستائر عزل وتهوية ميكانيكية..."
              className={`field ${touched.controls && errors.controls ? 'field-error' : ''}`}
            />
            {touched.controls && errors.controls && (
              <div className="error-msg text-crit text-xs mt-1 flex items-center gap-1">
                <Icon name="incident" size={12} /> {errors.controls}
              </div>
            )}
          </Field>
        </div>

        {/* Residual Risk Calculation */}
        <div className="p-3.5 bg-steel-3/30 border border-line rounded-lg">
          <div className="flex items-center justify-between mb-3">
            <span className="text-xs font-semibold text-txt flex items-center gap-1.5">
              <Icon name="check" size={14} className="text-safe" />
              الخطر المتبقي بعد تطبيق الضوابط (Residual Risk Rating)
            </span>
            <div className="flex items-center gap-2">
              <span className="text-xs text-txt-3">الدرجة المتبقية:</span>
              <span
                className="px-2.5 py-0.5 rounded text-xs font-bold font-mono"
                style={{
                  color: residualMeta.color,
                  backgroundColor: residualMeta.bg,
                  border: `1px solid ${residualMeta.border}`
                }}
              >
                {residualScore} — {residualMeta.label}
              </span>
            </div>
          </div>

          <div className="grid sm:grid-cols-2 gap-4">
            <Field label="الاحتمالية بعد التحكم (Residual Likelihood)" className="mb-0">
              <select
                name="residual_likelihood"
                value={form.residual_likelihood}
                onChange={handleChange}
                className="field font-mono"
              >
                {PROBABILITY_OPTIONS.map(p => (
                  <option key={p.value} value={p.value}>{p.label}</option>
                ))}
              </select>
            </Field>

            <Field label="الشدة بعد التحكم (Residual Severity)" className="mb-0">
              <select
                name="residual_severity"
                value={form.residual_severity}
                onChange={handleChange}
                className="field font-mono"
              >
                {SEVERITY_OPTIONS.map(s => (
                  <option key={s.value} value={s.value}>{s.label}</option>
                ))}
              </select>
            </Field>
          </div>
        </div>
      </form>
    </Modal>
  )
}
