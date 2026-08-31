import { useState } from 'react'
import { Async, Btn, Card, CardBody, CardHead, PageHeader, Pill, StatLine } from '../components/ui.jsx'
import Modal from '../components/Modal.jsx'
import Icon from '../components/Icon.jsx'
import { departments as deptApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'
import tc, { toneColors } from '../themeColors.js'



export default function Departments() {
  const toast = useToast()
  const [zone, setZone] = useState(null)
  const [showAdd, setShowAdd] = useState(false)
  const [form, setForm] = useState({ name_ar: '', name_en: '', department_id: '', max_occupancy: 0 })
  const sectors = useApi(() => deptApi.list(), [])
  const rawDepartments = useApi(() => deptApi.rawList(), [])

  const handleAddZone = async (e) => {
    e.preventDefault()
    try {
      await deptApi.createZone({
        name_ar: form.name_ar,
        name_en: form.name_en,
        department_id: Number(form.department_id),
        max_occupancy: Number(form.max_occupancy) || 0,
        active_flag: true,
        zone_type: 'GENERAL',
        risk_class_id: 1,
      })
      toast('تمت إضافة المنطقة بنجاح', 'ok')
      setShowAdd(false)
      setForm({ name_ar: '', name_en: '', department_id: '', max_occupancy: 0 })
      sectors.reload()
    } catch (err) {
      toast(err.message || 'حدث خطأ أثناء الإضافة', 'cr')
    }
  }

  return (
    <>
      <PageHeader title="الأقسام والمناطق" meta="departments & zones · loaded from plant master data">
        <Btn icon="pin" onClick={() => toast('خريطة المصنع التفاعلية ضمن نطاق المرحلة القادمة', 'in')}>
          خريطة المصنع
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setShowAdd(true)}>
          إضافة منطقة
        </Btn>
      </PageHeader>

      <Async state={sectors} rows={8}>
        {(rows) =>
          rows.map((sec) => (
            <Card key={sec.sector} className="mb-3.5">
              <CardHead
                title={sec.sector}
                hint={`${sec.sectorEn} · ${sec.zones.length} ZONES · ${sec.headcount} فرد`}
              />
              <CardBody>
                <div className="grid gap-3.5" style={{ gridTemplateColumns: 'repeat(auto-fit,minmax(215px,1fr))' }}>
                  {sec.zones.map((z) => (
                    <button
                      key={z.code}
                      onClick={() => setZone(z)}
                      className="text-start bg-steel-3 border border-line rounded-md p-3.5 transition-all duration-150
                                 hover:-translate-y-0.5 hover:border-txt-3 hover:shadow-lg"
                      style={{ borderInlineEndWidth: 4, borderInlineEndColor: toneColors()[z.status] || tc.txt3() }}
                    >
                      <div className="text-[13.5px] font-semibold mb-0.5">{z.name}</div>
                      <div className="text-xs text-txt-3 font-mono num mb-2.5">
                        {z.code} · {z.headcount} فرد
                      </div>
                      <div className="stat-line">
                        <span>مؤشر السلامة</span>
                        <b style={{ color: toneColors()[z.status] || tc.txt2() }}>
                          {z.score == null ? '—' : `${z.score}%`}
                        </b>
                      </div>
                      <div className="stat-line">
                        <span>حوادث 2026</span>
                        <b className={z.incidents >= 5 ? 'text-crit' : ''}>{z.incidents}</b>
                      </div>
                      <div className="stat-line">
                        <span>الطفايات</span>
                        <b>{z.extinguishers}</b>
                      </div>
                      <div className="stat-line">
                        <span>آخر تفتيش</span>
                        <b>{z.lastInspection}</b>
                      </div>
                      <div className="mt-2.5">
                        <Pill tone={z.status}>{z.statusLabel}</Pill>
                      </div>
                    </button>
                  ))}
                </div>
              </CardBody>
            </Card>
          ))
        }
      </Async>

      {zone && (
        <Modal open onClose={() => setZone(null)} title={zone.name} width={520}>
          <div className="flex items-center gap-2 mb-4">
            <Pill tone={zone.status}>{zone.statusLabel}</Pill>
            <span className="font-mono num text-xs text-txt-3">{zone.code}</span>
          </div>
          <StatLine label="عدد العاملين" value={zone.headcount} />
          <StatLine
            label="مؤشر السلامة"
            value={zone.score == null ? '—' : `${zone.score}%`}
            valueClass={zone.score != null && zone.score < 70 ? 'text-crit' : ''}
          />
          <StatLine label="حوادث 2026" value={zone.incidents} />
          <StatLine label="جاهزية الطفايات" value={zone.extinguishers} />
          <StatLine label="آخر جولة تفتيش" value={zone.lastInspection} />
          <div className="mt-4 pt-3.5 border-t border-line">
            <div className="text-[12.5px] font-semibold mb-1.5 flex items-center gap-2">
              <Icon name="risk" size={14} className="text-txt-3" />
              المخاطر الرئيسية بالمنطقة
            </div>
            <p className="text-xs text-txt-2 leading-8">{zone.hazard}</p>
          </div>
        </Modal>
      )}
      {showAdd && (
        <Modal open onClose={() => setShowAdd(false)} title="إضافة منطقة جديدة" width={520}>
          <form onSubmit={handleAddZone}>
            <div className="flex flex-col gap-4">
              <div>
                <label className="text-xs text-txt-3 block mb-1">اسم المنطقة (العربية)</label>
                <input
                  required
                  className="w-full bg-steel-3 border border-line rounded-md px-3 py-2 outline-none focus:border-hi text-sm"
                  value={form.name_ar}
                  onChange={(e) => setForm({ ...form, name_ar: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-txt-3 block mb-1">اسم المنطقة (English)</label>
                <input
                  required
                  className="w-full bg-steel-3 border border-line rounded-md px-3 py-2 outline-none focus:border-hi text-sm"
                  value={form.name_en}
                  onChange={(e) => setForm({ ...form, name_en: e.target.value })}
                />
              </div>
              <div>
                <label className="text-xs text-txt-3 block mb-1">القسم / القطاع</label>
                <select
                  required
                  className="w-full bg-steel-3 border border-line rounded-md px-3 py-2 outline-none focus:border-hi text-sm"
                  value={form.department_id}
                  onChange={(e) => setForm({ ...form, department_id: e.target.value })}
                >
                  <option value="">-- اختر القسم --</option>
                  {rawDepartments.data?.map(dept => (
                    <option key={dept.department_id} value={dept.department_id}>{dept.name_ar}</option>
                  ))}
                </select>
              </div>
              <div>
                <label className="text-xs text-txt-3 block mb-1">عدد العاملين (Max Occupancy)</label>
                <input
                  type="number"
                  required
                  min="0"
                  className="w-full bg-steel-3 border border-line rounded-md px-3 py-2 outline-none focus:border-hi text-sm"
                  value={form.max_occupancy}
                  onChange={(e) => setForm({ ...form, max_occupancy: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="pt-3 border-t border-line mt-1 flex justify-end gap-2">
                <Btn variant="txt" type="button" onClick={() => setShowAdd(false)}>إلغاء</Btn>
                <Btn variant="pri" type="submit">إضافة</Btn>
              </div>
            </div>
          </form>
        </Modal>
      )}
    </>
  )
}
