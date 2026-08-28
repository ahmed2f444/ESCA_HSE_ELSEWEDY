import { useState } from 'react'
import Modal from '../../components/Modal.jsx'
import { Btn, Field } from '../../components/ui.jsx'
import { incidents } from '../../api/endpoints.js'

const TYPES = ['إصابة', 'شبه حادث (Near Miss)', 'وضع غير آمن', 'سلوك غير آمن', 'حريق', 'ضرر بالممتلكات', 'انسكاب / تسرب بيئي']
const SEVERITIES = ['منخفضة', 'متوسطة', 'عالية', 'حرجة']
const ZONES = [
  'خط إنتاج الأكسسوارات — A',
  'خط إنتاج الأكسسوارات — B',
  'ورشة الصيانة الميكانيكية',
  'معمل الجودة والاختبارات',
  'مخزن الخامات',
  'مخزن المنتج التام',
  'محطة الكهرباء والمرافق',
  'المبنى الإداري',
  'العيادة والكانتين',
]
const OWNERS = [
  'م. أحمد سامي — HSE Officer',
  'م. هبة فؤاد — HSE Officer',
  'م. كريم رشاد — HSE Officer',
  'رافع صابر — HSE Manager',
]

const blank = {
  type: TYPES[0],
  severity: SEVERITIES[1],
  zone: ZONES[0],
  occurredAt: '2026-08-06T10:30',
  injured: '',
  employeeNo: '',
  description: '',
  immediateAction: '',
  owner: OWNERS[0],
  dueDate: '2026-08-13',
}

/**
 * Field reporting form.
 *
 * Only four fields are actually required (type, zone, time, description) —
 * the rest can be completed during the investigation. That's deliberate: a
 * long mandatory form is the fastest way to stop people reporting near misses
 * at all, and the near-miss ratio is one of the plant's leading indicators.
 */
export default function IncidentForm({ open, onClose, onCreated }) {
  const [form, setForm] = useState(blank)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))
  const missing = !form.description.trim()

  async function submit() {
    if (missing) {
      setError('وصف ما حدث حقل إلزامي')
      return
    }
    setBusy(true)
    setError('')
    try {
      const rec = await incidents.create(form)
      setForm(blank)
      onClose?.()
      onCreated?.(rec)
    } catch (e) {
      setError(e.message)
    } finally {
      setBusy(false)
    }
  }

  return (
    <Modal
      open={open}
      onClose={onClose}
      title="تسجيل حادث / بلاغ جديد"
      footer={
        <>
          <Btn variant="dgr" onClick={submit} disabled={busy}>
            {busy ? 'جارٍ الحفظ…' : 'حفظ وإخطار'}
          </Btn>
          <Btn onClick={onClose} disabled={busy}>
            إلغاء
          </Btn>
        </>
      }
    >
      <div className="grid sm:grid-cols-2 gap-x-3">
        <Field label="نوع البلاغ">
          <select className="field" value={form.type} onChange={set('type')}>
            {TYPES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </Field>
        <Field label="درجة الخطورة">
          <select className="field" value={form.severity} onChange={set('severity')}>
            {SEVERITIES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </Field>
        <Field label="القسم / المنطقة">
          <select className="field" value={form.zone} onChange={set('zone')}>
            {ZONES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </Field>
        <Field label="التاريخ والوقت">
          <input type="datetime-local" className="field" value={form.occurredAt} onChange={set('occurredAt')} />
        </Field>
        <Field label="اسم المصاب (إن وُجد)">
          <input className="field" placeholder="اتركه فارغاً لو مفيش إصابة" value={form.injured} onChange={set('injured')} />
        </Field>
        <Field label="الرقم الوظيفي">
          <input className="field" placeholder="EMP-01184" value={form.employeeNo} onChange={set('employeeNo')} />
        </Field>
      </div>

      <Field label="وصف ما حدث">
        <textarea
          className="field min-h-[78px] resize-y"
          placeholder="ماذا حدث، أين، كيف، وما هي الظروف المحيطة…"
          value={form.description}
          onChange={set('description')}
        />
      </Field>

      <Field label="الإجراء الفوري المتخذ">
        <textarea
          className="field min-h-[56px] resize-y"
          placeholder="ما تم عمله فور وقوع الحادث…"
          value={form.immediateAction}
          onChange={set('immediateAction')}
        />
      </Field>

      <div className="grid sm:grid-cols-2 gap-x-3">
        <Field label="المسؤول عن التحقيق">
          <select className="field" value={form.owner} onChange={set('owner')}>
            {OWNERS.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
        </Field>
        <Field label="موعد إنهاء التحقيق">
          <input type="date" className="field" value={form.dueDate} onChange={set('dueDate')} />
        </Field>
      </div>

      {error && (
        <div
          className="text-xs px-3 py-2 rounded"
          style={{ background: 'rgb(var(--c-crit) / 0.1)', border: '1px solid rgb(var(--c-crit) / 0.4)', color: 'rgb(var(--c-crit))' }}
        >
          {error}
        </div>
      )}
    </Modal>
  )
}
