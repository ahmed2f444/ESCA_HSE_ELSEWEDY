import { useState } from 'react'
import { Async, Btn, Card, CardBody, CardHead, PageHeader, Pill, StatLine } from '../components/ui.jsx'
import Modal from '../components/Modal.jsx'
import Icon from '../components/Icon.jsx'
import { departments as deptApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

const TONE_COLOR = { ok: '#38B87C', wn: '#F09030', cr: '#E0483C' }

export default function Departments() {
  const toast = useToast()
  const [zone, setZone] = useState(null)
  const sectors = useApi(() => deptApi.list(), [])

  return (
    <>
      <PageHeader title="الأقسام والمناطق" meta="departments & zones · loaded from plant master data">
        <Btn icon="pin" onClick={() => toast('خريطة المصنع التفاعلية ضمن نطاق المرحلة القادمة', 'in')}>
          خريطة المصنع
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => toast('إضافة منطقة تتم من خدمة Departments', 'in')}>
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
                      style={{ borderInlineEndWidth: 4, borderInlineEndColor: TONE_COLOR[z.status] || '#5E7794' }}
                    >
                      <div className="text-[13.5px] font-semibold mb-0.5">{z.name}</div>
                      <div className="text-xs text-txt-3 font-mono num mb-2.5">
                        {z.code} · {z.headcount} فرد
                      </div>
                      <div className="stat-line">
                        <span>مؤشر السلامة</span>
                        <b style={{ color: TONE_COLOR[z.status] || '#93A9C4' }}>
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
    </>
  )
}
