import { useState, useMemo } from 'react'
import { Async, Btn, Card, CardBody, CardHead, Grid, Kpi, KpiRow, PageHeader, Pill, Table } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { hazmat as hazmatApi, departments as deptApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const CELL = {
  '✓': { get color() { return tc.safe() }, label: 'تخزين مشترك مسموح', bg: 'rgba(34, 197, 94, 0.12)' },
  '!': { get color() { return tc.warn() }, label: 'فصل إلزامي بمسافة أمان', bg: 'rgba(234, 179, 8, 0.12)' },
  X: { get color() { return tc.crit() }, label: 'محظور التخزين معاً منعاً باتاً', bg: 'rgba(239, 68, 68, 0.12)' },
}

const GHS_OPTIONS = [
  { value: 'FLAMMABLE', label: 'GHS02 سريع الاشتعال', tone: 'crit', icon: 'flame' },
  { value: 'CORROSIVE', label: 'GHS05 مادة أكالة', tone: 'warn', icon: 'alert-circle' },
  { value: 'TOXIC', label: 'GHS06 سمية حادة', tone: 'crit', icon: 'alert-circle' },
  { value: 'IRRITANT', label: 'GHS07 مخرش / تنبيه', tone: 'wn', icon: 'alert-circle' },
  { value: 'HEALTH_HAZARD', label: 'GHS08 خطر صحي', tone: 'warn', icon: 'health' },
  { value: 'OXIDIZER', label: 'GHS03 مادة مؤكسدة', tone: 'warn', icon: 'flame' },
  { value: 'GAS_UNDER_PRESSURE', label: 'GHS04 غاز مضغوط', tone: 'safe', icon: 'confined' },
  { value: 'ENVIRONMENTAL', label: 'GHS09 خطر بيئي', tone: 'info', icon: 'zones' },
]

const STORAGE_CLASSES = [
  { value: 'Class 3', label: 'Class 3 - سوائل قابلة للاشتعال (Flammable Liquids)' },
  { value: 'Class 8', label: 'Class 8 - مواد أكالة وقواعد/أحماض (Corrosive Substances)' },
  { value: 'Class 6.1', label: 'Class 6.1 - مواد سامة وخطرة (Toxic Substances)' },
  { value: 'Class 2.1', label: 'Class 2.1 - غازات مضغوطة قابلة للاشتعال (Flammable Gases)' },
  { value: 'Class 5.1', label: 'Class 5.1 - مواد مؤكسدة (Oxidizing Agents)' },
  { value: 'Class 9', label: 'Class 9 - مواد خطرة متنوعة (Miscellaneous)' },
  { value: 'GENERAL', label: 'تخزين عام غير خطائي (General Storage)' },
]

export default function Hazmat() {
  const toast = useToast()
  const [reloadKey, setReloadKey] = useState(0)
  const refresh = () => setReloadKey((k) => k + 1)

  // Filters & search
  const [search, setSearch] = useState('')
  const [ghsFilter, setGhsFilter] = useState('ALL')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [zoneFilter, setZoneFilter] = useState('ALL')

  // Modals state
  const [isRegisterOpen, setIsRegisterOpen] = useState(false)
  const [isSdsArchiveOpen, setIsSdsArchiveOpen] = useState(false)
  const [selectedChemical, setSelectedChemical] = useState(null)
  const [editingChemical, setEditingChemical] = useState(null)
  const [sdsModalForChem, setSdsModalForChem] = useState(null)
  const [previewSds, setPreviewSds] = useState(null)
  const [emergencyGuide, setEmergencyGuide] = useState(null)

  // Data fetching
  const list = useApi(
    () => hazmatApi.list({
      query: search || undefined,
      ghs: ghsFilter !== 'ALL' ? ghsFilter : undefined,
      status: statusFilter !== 'ALL' ? statusFilter : undefined,
      zoneId: zoneFilter !== 'ALL' ? Number(zoneFilter) : undefined,
    }),
    [search, ghsFilter, statusFilter, zoneFilter, reloadKey]
  )

  const stats = useApi(() => hazmatApi.stats(), [reloadKey])
  const compat = useApi(() => hazmatApi.compatibility(), [])
  const zonesList = useApi(() => deptApi.list(), [])

  // Flattened zones options
  const zones = useMemo(() => {
    const raw = zonesList.data || []
    const out = []
    raw.forEach((d) => {
      if (Array.isArray(d.zones)) {
        d.zones.forEach((z) => out.push({ id: z.id || z.zone_id, name: z.name || z.name_ar || `منطقة ${z.id}` }))
      }
    })
    if (out.length === 0) {
      out.push(
        { id: 9, name: 'مخزن المواد الكيميائية الرئيسي' },
        { id: 1, name: 'خطوط العزل CCV - خط A' },
        { id: 2, name: 'ورشة الصيانة الميكانيكية' },
        { id: 4, name: 'مستودع الخامات والمذيبات' }
      )
    }
    return out
  }, [zonesList.data])

  return (
    <>
      <PageHeader title="المواد الخطرة والكيماويات" meta="hazmat inventory · sds register · ghs compliance">
        <Btn icon="document" onClick={() => setIsSdsArchiveOpen(true)}>
          أرشيف صحائف السلامة (SDS)
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => setIsRegisterOpen(true)}>
          تسجيل مادة جديدة
        </Btn>
      </PageHeader>

      {/* KPI Stats */}
      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="إجمالي المواد المسجّلة" value={s.total || 0} tone="info" sub="سجل الكيماويات معتمد بقاعدة البيانات" />
            <Kpi label="مواد قابلة للاشتعال" value={s.flammable || 0} tone="crit" sub="تخزين معزول + تهوية قسرية" />
            <Kpi label="مواد أكّالة وكاوية" value={s.corrosive || 0} tone="warn" sub="أحواض احتواء بسعة 110%" />
            <Kpi
              label="SDS منتهية / تقترب من الانتهاء"
              value={(s.sdsExpired || 0) + (s.sdsDueSoon || 0)}
              tone={(s.sdsExpired || 0) > 0 ? 'crit' : 'safe'}
              trend={(s.sdsExpired || 0) > 0 ? 'down' : 'up'}
              sub={s.sdsExpired > 0 ? `${s.sdsExpired} صحيفة تحتاج مراجعة فورية` : 'جميع صحائف السلامة سارية ومحدثة'}
            />
            <Kpi label="أطقم مكافحة الانسكاب" value={s.spillKits || 14} tone="safe" sub="موزّعة على المستودعات وخطوط العمل" />
          </KpiRow>
        )}
      </Async>

      {/* Chemical Register Card */}
      <Card className="mb-4">
        <CardHead title="سجل المواد الكيميائية والمخزون" hint="LIVE CHEMICAL REGISTER">
          <div className="flex flex-wrap items-center gap-2">
            <div className="relative">
              <input
                type="text"
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                placeholder="بحث بالاسم، كود CAS، المورّد..."
                className="in text-xs py-1.5 px-3 pe-8 w-56 rounded bg-steel border border-line text-txt"
              />
              {search && (
                <button onClick={() => setSearch('')} className="absolute end-2 top-2 text-txt-3 hover:text-txt">
                  <Icon name="x" size={12} />
                </button>
              )}
            </div>

            <select
              value={ghsFilter}
              onChange={(e) => setGhsFilter(e.target.value)}
              className="in text-xs py-1.5 px-2.5 rounded bg-steel border border-line text-txt"
            >
              <option value="ALL">جميع تصنيفات GHS</option>
              {GHS_OPTIONS.map((g) => (
                <option key={g.value} value={g.value}>{g.label}</option>
              ))}
            </select>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="in text-xs py-1.5 px-2.5 rounded bg-steel border border-line text-txt"
            >
              <option value="ALL">جميع الحالات</option>
              <option value="ACTIVE">نشط ومصرح به</option>
              <option value="PHASED_OUT">تم التخلص التدريجي</option>
              <option value="QUARANTINED">محجور وقيد الفحص</option>
            </select>

            <Btn size="sm" icon="refresh" onClick={refresh} title="تحديث السجل">
              تحديث
            </Btn>
          </div>
        </CardHead>

        <Async state={list} rows={8}>
          {(rows) => (
            <>
              {rows.length === 0 ? (
                <div className="p-8 text-center text-txt-3">
                  <Icon name="hazmat" size={36} className="mx-auto mb-2 opacity-40 text-warn" />
                  <p className="font-semibold text-txt-2">لا توجد مواد كيميائية مطابقة لمعايير البحث</p>
                  <p className="text-xs mt-1">يمكنك تسجيل مادة جديدة أو تغيير فلاتر البحث أعلاه.</p>
                  <Btn variant="pri" size="sm" icon="plus" className="mt-4" onClick={() => setIsRegisterOpen(true)}>
                    تسجيل مادة جديدة الآن
                  </Btn>
                </div>
              ) : (
                <Table
                  head={['الكود', 'الاسم التجاري', 'الاسم العلمي / CAS', 'تصنيف GHS', 'الكمية المخزنة', 'موقع التخزين', 'فئة التخزين', 'صحيفة SDS', 'إجراءات']}
                  clickable={false}
                >
                  {rows.map((c) => (
                    <tr
                      key={c.id || c.code}
                      className="hover:bg-steel/50 cursor-pointer transition-colors"
                      onClick={() => setSelectedChemical(c)}
                    >
                      <td className="mono font-bold text-accent">{c.code}</td>
                      <td className="font-semibold">
                        {c.tradeName || c.name}
                        {c.supplier && <span className="block text-2xs text-txt-3 font-normal">{c.supplier}</span>}
                      </td>
                      <td>
                        <span className="text-xs text-txt-2">{c.chemicalName || '—'}</span>
                        {c.cas && <span className="block mono text-2xs text-txt-3">CAS: {c.cas}</span>}
                      </td>
                      <td>
                        <Pill tone={c.tone}>{c.ghs}</Pill>
                      </td>
                      <td className="mono font-semibold">{c.qty}</td>
                      <td className="text-xs text-txt-2">{c.location}</td>
                      <td>
                        <span className="mono text-2xs px-2 py-0.5 rounded bg-steel-3 border border-line">
                          {c.storageClass || c.class}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-1.5">
                          <span
                            className="mono text-xs font-semibold"
                            style={{
                              color: c.sdsStatus === 'EXPIRED' ? tc.crit() : c.sdsStatus === 'DUE_SOON' ? tc.warn() : undefined
                            }}
                          >
                            {c.sds || '2026-12'}
                          </span>
                          {c.sdsStatus === 'EXPIRED' && (
                            <span className="w-2 h-2 rounded-full bg-crit" title="صحيفة منتهية الصلاحية" />
                          )}
                        </div>
                      </td>
                      <td onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center gap-1">
                          <button
                            className="p-1 rounded hover:bg-steel text-txt-3 hover:text-accent"
                            title="عرض التفاصيل وصحائف السلامة"
                            onClick={() => setSelectedChemical(c)}
                          >
                            <Icon name="document" size={14} />
                          </button>
                          <button
                            className="p-1 rounded hover:bg-steel text-txt-3 hover:text-safe"
                            title="تعليمات الطوارئ"
                            onClick={() => setEmergencyGuide(c)}
                          >
                            <Icon name="shield-check" size={14} />
                          </button>
                          <button
                            className="p-1 rounded hover:bg-steel text-txt-3 hover:text-warn"
                            title="تعديل بيانات المادة"
                            onClick={() => setEditingChemical(c)}
                          >
                            <Icon name="edit" size={14} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </Table>
              )}
            </>
          )}
        </Async>
      </Card>

      {/* Compatibility Matrix & Storage Guidelines */}
      <Grid cols={2}>
        <Card>
          <CardHead title="مصفوفة التوافق في التخزين المشترك" hint="COMPATIBILITY MATRIX" />
          <CardBody>
            <Async state={compat} rows={5}>
              {(m) => (
                <>
                  <div className="tw overflow-x-auto">
                    <table className="tbl text-center text-xs">
                      <thead>
                        <tr>
                          <th className="text-start">فئة المادة</th>
                          {m.groups.map((g) => (
                            <th key={g} className="text-center font-mono text-2xs whitespace-nowrap px-2">
                              {g.split(' ')[0]}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {m.grid.map((row, i) => (
                          <tr key={i}>
                            <th className="text-start font-semibold whitespace-nowrap text-txt-2">{m.groups[i]}</th>
                            {row.map((v, j) => (
                              <td key={j} className="text-center p-1">
                                <span
                                  className="inline-flex items-center justify-center w-7 h-7 rounded font-mono num font-bold text-xs shadow-sm cursor-help"
                                  title={`${m.groups[i]} + ${m.groups[j]}: ${CELL[v]?.label}`}
                                  style={{
                                    background: CELL[v]?.bg,
                                    color: CELL[v]?.color,
                                    border: `1px solid ${CELL[v]?.color}44`,
                                  }}
                                >
                                  {v}
                                </span>
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="flex flex-wrap gap-4 text-xs text-txt-2 mt-4 pt-3 border-t border-line">
                    {Object.entries(CELL).map(([k, v]) => (
                      <span key={k} className="flex items-center gap-1.5">
                        <b className="font-mono num px-1.5 py-0.5 rounded" style={{ background: v.bg, color: v.color }}>
                          {k}
                        </b>
                        {v.label}
                      </span>
                    ))}
                  </div>
                </>
              )}
            </Async>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="اشتراطات وضوابط السلامة للتخزين" hint="STORAGE & SPILL CONTROLS" />
          <CardBody className="text-sm text-txt-2 leading-7 space-y-3">
            <div className="p-3 rounded bg-steel-2 border border-line flex items-start gap-3">
              <span className="p-1.5 rounded bg-warn/15 text-warn mt-0.5">
                <Icon name="flame" size={16} />
              </span>
              <div>
                <b className="text-txt font-semibold block">السوائل سريعة الاشتعال والمذيبات</b>
                <p className="text-xs mt-0.5">
                  خزائن معزولة ومقاومة للحريق مزوّدة بنظام تهوية قسرية وتأريض مضاد للكهرباء الساكنة. حظر تام لمصادر اللهب بمسافة لا تقل عن 11 متراً.
                </p>
              </div>
            </div>

            <div className="p-3 rounded bg-steel-2 border border-line flex items-start gap-3">
              <span className="p-1.5 rounded bg-crit/15 text-crit mt-0.5">
                <Icon name="alert-circle" size={16} />
              </span>
              <div>
                <b className="text-txt font-semibold block">المواد الأكّالة (الأحماض والقواعد)</b>
                <p className="text-xs mt-0.5">
                  أحواض احتواء (Spill Containment Bunds) بسعة 110% من أكبر عبوة، مع فصل الأحماض المركزة تماماً عن القواعد منعاً لحدوث تفاعلات طاردة للحرارة.
                </p>
              </div>
            </div>

            <div className="p-3 rounded bg-steel-2 border border-line flex items-start gap-3">
              <span className="p-1.5 rounded bg-safe/15 text-safe mt-0.5">
                <Icon name="shield-check" size={16} />
              </span>
              <div>
                <b className="text-txt font-semibold block">أطقم مكافحة الانسكاب ومحطات غسيل العيون</b>
                <p className="text-xs mt-0.5">
                  توفر أطقم مكافحة الانسكاب الكيميائي (Spill Kits) ومحطات غسيل العيون الطارئة على بعد لا يتجاوز 10 ثوانٍ وصولاً من أي منطقة تخزين نشطة.
                </p>
              </div>
            </div>
          </CardBody>
        </Card>
      </Grid>

      {/* ────────────────────────── MODALS & DRAWERS ────────────────────────── */}

      {/* 1. Register New Chemical Modal */}
      {isRegisterOpen && (
        <RegisterChemicalModal
          zones={zones}
          onClose={() => setIsRegisterOpen(false)}
          onSuccess={(saved) => {
            setIsRegisterOpen(false)
            toast(`تم تسجيل المادة الكيميائية (${saved.tradeName || saved.name}) وتوثيق صحيفة SDS بنجاح`, 'ok')
            refresh()
          }}
        />
      )}

      {/* 2. Edit Chemical Modal */}
      {editingChemical && (
        <EditChemicalModal
          chemical={editingChemical}
          zones={zones}
          onClose={() => setEditingChemical(null)}
          onSuccess={(updated) => {
            setEditingChemical(null)
            if (selectedChemical?.id === updated.id) setSelectedChemical(updated)
            toast(`تم تحديث بيانات المادة (${updated.tradeName}) بنجاح`, 'ok')
            refresh()
          }}
        />
      )}

      {/* 3. SDS Archive Modal */}
      {isSdsArchiveOpen && (
        <SdsArchiveModal
          onClose={() => setIsSdsArchiveOpen(false)}
          onSelectPreview={(sds) => setPreviewSds(sds)}
          onSelectEmergency={(sds) => setEmergencyGuide(sds)}
          onAddSds={(chemId) => setSdsModalForChem(chemId || true)}
          onRefreshData={refresh}
        />
      )}

      {/* 4. Chemical Details Modal */}
      {selectedChemical && (
        <ChemicalDetailsModal
          chemical={selectedChemical}
          onClose={() => setSelectedChemical(null)}
          onEdit={() => {
            const c = selectedChemical
            setSelectedChemical(null)
            setEditingChemical(c)
          }}
          onAddSds={() => {
            const cid = selectedChemical.id
            setSdsModalForChem(cid)
          }}
          onEmergencyGuide={() => setEmergencyGuide(selectedChemical)}
          onDelete={async () => {
            if (window.confirm(`هل أنت متأكد من رغبتك في حذف المادة (${selectedChemical.tradeName}) وجميع صحائف SDS المرتبطة بها؟`)) {
              try {
                await hazmatApi.delete(selectedChemical.id)
                toast('تم حذف المادة الكيميائية وسجلاتها بنجاح', 'ok')
                setSelectedChemical(null)
                refresh()
              } catch (err) {
                toast(err.message || 'تعذّر حذف المادة', 'err')
              }
            }
          }}
        />
      )}

      {/* 5. Add/Update SDS Record Modal */}
      {sdsModalForChem && (
        <AddSdsModal
          chemicalId={typeof sdsModalForChem === 'number' ? sdsModalForChem : null}
          chemicals={list.data || []}
          onClose={() => setSdsModalForChem(null)}
          onSuccess={() => {
            setSdsModalForChem(null)
            toast('تم حفظ صحيفة بيانات السلامة (SDS) في الأرشيف بنجاح', 'ok')
            refresh()
          }}
        />
      )}

      {/* 6. SDS Document Preview Modal */}
      {previewSds && (
        <SdsPreviewModal
          sds={previewSds}
          onClose={() => setPreviewSds(null)}
        />
      )}

      {/* 7. Emergency Response Guidance Modal */}
      {emergencyGuide && (
        <EmergencyGuideModal
          data={emergencyGuide}
          onClose={() => setEmergencyGuide(null)}
        />
      )}
    </>
  )
}

/* ──────────────────────────────────────────────────────────────────────────── */
/* SUB-COMPONENTS & MODALS                                                     */
/* ──────────────────────────────────────────────────────────────────────────── */

function RegisterChemicalModal({ zones, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [activeTab, setActiveTab] = useState('BASIC')

  const [form, setForm] = useState({
    tradeName: '',
    chemicalName: '',
    casNumber: '',
    supplier: '',
    quantity: 100,
    unit: 'L',
    ghsClasses: 'FLAMMABLE',
    storageClass: 'Class 3',
    zoneId: zones[0]?.id || 9,
    statusId: 1,
    sdsVersion: 'Rev 1',
    issueDate: new Date().toISOString().slice(0, 10),
    expiryDate: new Date(Date.now() + 2 * 365 * 864e5).toISOString().slice(0, 10),
    emergencySummary: 'عزل المصدر، استخدام مهمات الوقاية المناسبة (PPE)، تهوية المنطقة وإبلاغ مسؤول السلامة فوراً في حال الانسكاب.',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!form.tradeName.trim()) {
      alert('يرجى إدخال الاسم التجاري للمادة')
      return
    }
    setLoading(true)
    try {
      const res = await hazmatApi.create(form)
      onSuccess(res)
    } catch (err) {
      alert(err.message || 'فشل في حفظ المادة الكيميائية')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded bg-accent/15 text-accent">
              <Icon name="hazmat" size={18} />
            </span>
            <div>
              <h3 className="text-base font-bold">تسجيل مادة كيميائية جديدة</h3>
              <p className="text-xs text-txt-3 font-mono">NEW HAZMAT & CHEMICAL REGISTRATION</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Form Tabs */}
        <div className="flex border-b border-line bg-steel px-4 gap-4 text-xs font-semibold">
          <button
            type="button"
            className={`py-2.5 border-b-2 transition-colors ${activeTab === 'BASIC' ? 'border-accent text-accent' : 'border-transparent text-txt-3 hover:text-txt'}`}
            onClick={() => setActiveTab('BASIC')}
          >
            1. البيانات الأساسية
          </button>
          <button
            type="button"
            className={`py-2.5 border-b-2 transition-colors ${activeTab === 'STORAGE' ? 'border-accent text-accent' : 'border-transparent text-txt-3 hover:text-txt'}`}
            onClick={() => setActiveTab('STORAGE')}
          >
            2. التخزين والمخزون
          </button>
          <button
            type="button"
            className={`py-2.5 border-b-2 transition-colors ${activeTab === 'GHS' ? 'border-accent text-accent' : 'border-transparent text-txt-3 hover:text-txt'}`}
            onClick={() => setActiveTab('GHS')}
          >
            3. تصنيف GHS وصحيفة SDS
          </button>
        </div>

        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {activeTab === 'BASIC' && (
            <div className="space-y-3.5">
              <div>
                <label className="block text-txt-2 font-semibold mb-1">الاسم التجاري للمادة <span className="text-crit">*</span></label>
                <input
                  type="text"
                  required
                  placeholder="مثال: DURACLEAN 200 أو SOLV-IPA"
                  value={form.tradeName}
                  onChange={(e) => setForm({ ...form, tradeName: e.target.value })}
                  className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">الاسم الكيميائي العلمي</label>
                  <input
                    type="text"
                    placeholder="مثال: Isopropyl Alcohol 99%"
                    value={form.chemicalName}
                    onChange={(e) => setForm({ ...form, chemicalName: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                  />
                </div>
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">رقم تسجيل CAS No.</label>
                  <input
                    type="text"
                    placeholder="مثال: 67-63-0 أو 1310-73-2"
                    value={form.casNumber}
                    onChange={(e) => setForm({ ...form, casNumber: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-txt-2 font-semibold mb-1">الشركة المورّدة / المصنّع</label>
                <input
                  type="text"
                  placeholder="مثال: Elsewedy Chemical Supply أو EgyChem"
                  value={form.supplier}
                  onChange={(e) => setForm({ ...form, supplier: e.target.value })}
                  className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                />
              </div>
            </div>
          )}

          {activeTab === 'STORAGE' && (
            <div className="space-y-3.5">
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">الكمية المخزنة</label>
                  <input
                    type="number"
                    min="0"
                    step="0.1"
                    value={form.quantity}
                    onChange={(e) => setForm({ ...form, quantity: parseFloat(e.target.value) || 0 })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">وحدة القياس</label>
                  <select
                    value={form.unit}
                    onChange={(e) => setForm({ ...form, unit: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                  >
                    <option value="L">لتر (Liters)</option>
                    <option value="kg">كيلوجرام (kg)</option>
                    <option value="Drums">براميل (Drums)</option>
                    <option value="Cylinders">أسطوانات (Cylinders)</option>
                    <option value="m³">متر مكعب (m³)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">فئة التخزين (Storage Class)</label>
                  <select
                    value={form.storageClass}
                    onChange={(e) => setForm({ ...form, storageClass: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                  >
                    {STORAGE_CLASSES.map((sc) => (
                      <option key={sc.value} value={sc.value}>{sc.label}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">موقع التخزين / المنطقة</label>
                  <select
                    value={form.zoneId}
                    onChange={(e) => setForm({ ...form, zoneId: Number(e.target.value) })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                  >
                    {zones.map((z) => (
                      <option key={z.id} value={z.id}>{z.name}</option>
                    ))}
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-txt-2 font-semibold mb-1">حالة المادة في المنشأة</label>
                <div className="flex gap-3">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="statusId"
                      checked={form.statusId === 1}
                      onChange={() => setForm({ ...form, statusId: 1 })}
                    />
                    <span>نشط ومصرح به (Active)</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="statusId"
                      checked={form.statusId === 3}
                      onChange={() => setForm({ ...form, statusId: 3 })}
                    />
                    <span>محجور وقيد الفحص (Quarantined)</span>
                  </label>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'GHS' && (
            <div className="space-y-3.5">
              <div>
                <label className="block text-txt-2 font-semibold mb-1.5">تصنيف المخاطر المعتمد (GHS Hazard Classification)</label>
                <div className="grid grid-cols-2 gap-2">
                  {GHS_OPTIONS.map((g) => {
                    const isSelected = form.ghsClasses === g.value
                    return (
                      <button
                        key={g.value}
                        type="button"
                        onClick={() => setForm({ ...form, ghsClasses: g.value })}
                        className={`p-2 rounded border text-start flex items-center gap-2 transition-all ${
                          isSelected
                            ? 'bg-accent/15 border-accent text-txt font-semibold'
                            : 'bg-steel border-line text-txt-2 hover:bg-steel-3'
                        }`}
                      >
                        <Pill tone={g.tone}>{g.value}</Pill>
                        <span className="text-xs">{g.label}</span>
                      </button>
                    )
                  })}
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">رقم إصدار SDS</label>
                  <input
                    type="text"
                    value={form.sdsVersion}
                    onChange={(e) => setForm({ ...form, sdsVersion: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">تاريخ الإصدار</label>
                  <input
                    type="date"
                    value={form.issueDate}
                    onChange={(e) => setForm({ ...form, issueDate: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
                  />
                </div>
                <div>
                  <label className="block text-txt-2 font-semibold mb-1">تاريخ انتهاء المراجعة</label>
                  <input
                    type="date"
                    value={form.expiryDate}
                    onChange={(e) => setForm({ ...form, expiryDate: e.target.value })}
                    className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
                  />
                </div>
              </div>

              <div>
                <label className="block text-txt-2 font-semibold mb-1">ملخص تعليمات الطوارئ والإسعافات</label>
                <textarea
                  rows={2}
                  value={form.emergencySummary}
                  onChange={(e) => setForm({ ...form, emergencySummary: e.target.value })}
                  className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
                />
              </div>
            </div>
          )}

          <div className="pt-4 border-t border-line flex justify-end gap-2">
            <Btn type="button" onClick={onClose}>
              إلغاء
            </Btn>
            {activeTab !== 'GHS' ? (
              <Btn
                type="button"
                variant="pri"
                onClick={() => setActiveTab(activeTab === 'BASIC' ? 'STORAGE' : 'GHS')}
              >
                التالي
              </Btn>
            ) : (
              <Btn type="submit" variant="pri" disabled={loading}>
                {loading ? 'جارٍ الحفظ...' : 'حفظ المادة في السجل'}
              </Btn>
            )}
          </div>
        </form>
      </div>
    </div>
  )
}

function EditChemicalModal({ chemical, zones, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    tradeName: chemical.tradeName || chemical.name || '',
    chemicalName: chemical.chemicalName || '',
    casNumber: chemical.cas || chemical.casNumber || '',
    supplier: chemical.supplier || '',
    quantity: chemical.quantity || 0,
    unit: chemical.unit || 'L',
    ghsClasses: chemical.ghsClasses || 'FLAMMABLE',
    storageClass: chemical.storageClass || chemical.class || 'Class 3',
    zoneId: chemical.zoneId || zones[0]?.id || 9,
    statusId: chemical.statusId || 1,
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      const res = await hazmatApi.update(chemical.id, form)
      onSuccess(res)
    } catch (err) {
      alert(err.message || 'فشل في تحديث المادة الكيميائية')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <div className="flex items-center gap-2">
            <span className="p-2 rounded bg-warn/15 text-warn">
              <Icon name="edit" size={18} />
            </span>
            <div>
              <h3 className="text-base font-bold">تعديل بيانات المادة ({chemical.code})</h3>
              <p className="text-xs text-txt-3 font-mono">{chemical.tradeName}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={18} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-3.5 text-xs">
          <div>
            <label className="block text-txt-2 font-semibold mb-1">الاسم التجاري</label>
            <input
              type="text"
              required
              value={form.tradeName}
              onChange={(e) => setForm({ ...form, tradeName: e.target.value })}
              className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-txt-2 font-semibold mb-1">الاسم الكيميائي العلمي</label>
              <input
                type="text"
                value={form.chemicalName}
                onChange={(e) => setForm({ ...form, chemicalName: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              />
            </div>
            <div>
              <label className="block text-txt-2 font-semibold mb-1">رقم CAS</label>
              <input
                type="text"
                value={form.casNumber}
                onChange={(e) => setForm({ ...form, casNumber: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-txt-2 font-semibold mb-1">الكمية</label>
              <input
                type="number"
                step="0.1"
                value={form.quantity}
                onChange={(e) => setForm({ ...form, quantity: parseFloat(e.target.value) || 0 })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-txt-2 font-semibold mb-1">الوحدة</label>
              <select
                value={form.unit}
                onChange={(e) => setForm({ ...form, unit: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              >
                <option value="L">لتر (L)</option>
                <option value="kg">كيلوجرام (kg)</option>
                <option value="Drums">براميل (Drums)</option>
                <option value="Cylinders">أسطوانات</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-txt-2 font-semibold mb-1">الموقع / المنطقة</label>
              <select
                value={form.zoneId}
                onChange={(e) => setForm({ ...form, zoneId: Number(e.target.value) })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              >
                {zones.map((z) => (
                  <option key={z.id} value={z.id}>{z.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-txt-2 font-semibold mb-1">الحالة</label>
              <select
                value={form.statusId}
                onChange={(e) => setForm({ ...form, statusId: Number(e.target.value) })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              >
                <option value={1}>نشط ومصرح به</option>
                <option value={2}>تم التخلص التدريجي</option>
                <option value={3}>محجور وقيد الفحص</option>
              </select>
            </div>
          </div>

          <div className="pt-4 border-t border-line flex justify-end gap-2">
            <Btn type="button" onClick={onClose}>إلغاء</Btn>
            <Btn type="submit" variant="pri" disabled={loading}>
              {loading ? 'جارٍ الحفظ...' : 'حفظ التعديلات'}
            </Btn>
          </div>
        </form>
      </div>
    </div>
  )
}

function SdsArchiveModal({ onClose, onSelectPreview, onSelectEmergency, onAddSds, onRefreshData }) {
  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState('ALL')
  const [refreshKey, setRefreshKey] = useState(0)

  const sdsState = useApi(
    () => hazmatApi.sdsList({
      query: search || undefined,
      status: statusFilter !== 'ALL' ? statusFilter : undefined,
    }),
    [search, statusFilter, refreshKey]
  )

  const handleDelete = async (sdsId) => {
    if (window.confirm('هل أنت متأكد من حذف صحيفة بيانات السلامة هذه؟')) {
      try {
        await hazmatApi.deleteSds(sdsId)
        setRefreshKey((k) => k + 1)
        if (onRefreshData) onRefreshData()
      } catch (err) {
        alert(err.message || 'تعذّر حذف السجل')
      }
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-4xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded bg-info/15 text-info">
              <Icon name="document" size={20} />
            </span>
            <div>
              <h3 className="text-lg font-bold">أرشيف صحائف بيانات السلامة (SDS Repository)</h3>
              <p className="text-xs text-txt-3 font-mono">SAFETY DATA SHEETS · 16-SECTION COMPLIANCE</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Btn size="sm" variant="pri" icon="plus" onClick={() => onAddSds(null)}>
              + إضافة إصدار SDS
            </Btn>
            <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
              <Icon name="x" size={18} />
            </button>
          </div>
        </div>

        {/* Toolbar */}
        <div className="p-3 border-b border-line bg-steel flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2 flex-1 max-w-md">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="بحث في صحائف SDS بالاسم، الكود، رقم CAS..."
              className="in w-full py-1.5 px-3 rounded bg-steel-2 border border-line text-txt"
            />
          </div>

          <div className="flex items-center gap-1.5">
            {['ALL', 'CURRENT', 'DUE_SOON', 'EXPIRED'].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-2.5 py-1 rounded text-xs font-semibold transition-colors ${
                  statusFilter === st
                    ? 'bg-accent text-white'
                    : 'bg-steel-2 text-txt-3 hover:text-txt border border-line'
                }`}
              >
                {st === 'ALL' ? 'الكل' : st === 'CURRENT' ? 'سارية' : st === 'DUE_SOON' ? 'قريبة الانتهاء' : 'منتهية'}
              </button>
            ))}
          </div>
        </div>

        {/* Body Table */}
        <div className="flex-1 overflow-y-auto p-4">
          <Async state={sdsState} rows={6}>
            {(items) => (
              <>
                {items.length === 0 ? (
                  <div className="p-12 text-center text-txt-3">
                    <Icon name="document" size={36} className="mx-auto mb-2 opacity-40 text-info" />
                    <p className="font-semibold text-txt-2">لا توجد صحائف بيانات سلامة مطابقة</p>
                    <p className="text-xs mt-1">يمكنك إضافة صحيفة جديدة لأي مادة مسجلة في النظام.</p>
                  </div>
                ) : (
                  <Table head={['المادة الكيميائية', 'الإصدار', 'تاريخ المراجعة', 'انتهاء الصلاحية', 'الحالة', 'الملف', 'إجراءات']} clickable={false}>
                    {items.map((s) => (
                      <tr key={s.sdsId}>
                        <td className="font-semibold">
                          <span className="mono text-accent text-xs block">{s.chemicalCode}</span>
                          {s.tradeName || s.name}
                        </td>
                        <td>
                          <span className="mono text-xs px-2 py-0.5 rounded bg-steel-3 border border-line">
                            {s.versionNo}
                          </span>
                        </td>
                        <td className="mono text-xs text-txt-2">{s.issueDate || '—'}</td>
                        <td className="mono text-xs font-semibold">
                          <span style={{ color: s.isExpired ? tc.crit() : s.isDueSoon ? tc.warn() : undefined }}>
                            {s.expiryDate || '—'}
                          </span>
                          {s.daysToExpiry !== undefined && (
                            <span className="block text-2xs text-txt-3">
                              {s.daysToExpiry < 0 ? `منتهية منذ ${Math.abs(s.daysToExpiry)} يوم` : `متبقي ${s.daysToExpiry} يوم`}
                            </span>
                          )}
                        </td>
                        <td>
                          <Pill tone={s.tone}>{s.statusAr || s.status}</Pill>
                        </td>
                        <td className="mono text-2xs text-txt-3">
                          {s.fileRef || 'SDS-DOC.pdf'}
                        </td>
                        <td>
                          <div className="flex items-center gap-1.5">
                            <Btn size="sm" onClick={() => onSelectPreview(s)} title="معاينة محتوى SDS">
                              معاينة
                            </Btn>
                            <button
                              className="p-1.5 rounded hover:bg-steel text-txt-3 hover:text-safe"
                              title="تعليمات الطوارئ والإسعاف"
                              onClick={() => onSelectEmergency(s)}
                            >
                              <Icon name="shield-check" size={14} />
                            </button>
                            <button
                              className="p-1.5 rounded hover:bg-steel text-txt-3 hover:text-crit"
                              title="حذف الصحيفة"
                              onClick={() => handleDelete(s.sdsId)}
                            >
                              <Icon name="trash" size={14} />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </Table>
                )}
              </>
            )}
          </Async>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-line bg-steel-3 flex justify-between items-center text-xs text-txt-3">
          <span>يتم تحديث صحائف بيانات السلامة دورياً وفق معايير ISO 45001 و GHS</span>
          <Btn onClick={onClose}>إغلاق الأرشيف</Btn>
        </div>
      </div>
    </div>
  )
}

function ChemicalDetailsModal({ chemical, onClose, onEdit, onAddSds, onEmergencyGuide, onDelete }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-2xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <div className="flex items-center gap-3">
            <span className="p-2.5 rounded bg-accent/15 text-accent font-bold font-mono text-sm">
              {chemical.code}
            </span>
            <div>
              <h3 className="text-lg font-bold">{chemical.tradeName || chemical.name}</h3>
              <p className="text-xs text-txt-3">{chemical.chemicalName} · CAS: {chemical.cas || 'N/A'}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-5 space-y-4 text-xs">
          {/* Key Badges */}
          <div className="grid grid-cols-3 gap-3 p-3.5 rounded-lg bg-steel border border-line">
            <div>
              <span className="text-txt-3 block mb-1">تصنيف GHS:</span>
              <Pill tone={chemical.tone}>{chemical.ghs}</Pill>
            </div>
            <div>
              <span className="text-txt-3 block mb-1">الكمية المخزنة:</span>
              <span className="mono font-bold text-sm text-txt">{chemical.qty}</span>
            </div>
            <div>
              <span className="text-txt-3 block mb-1">موقع التخزين:</span>
              <span className="font-semibold text-txt">{chemical.location}</span>
            </div>
          </div>

          {/* Details Table */}
          <div className="border border-line rounded overflow-hidden">
            <div className="bg-steel-3 px-3 py-2 font-bold border-b border-line">بيانات التخزين والهوية</div>
            <div className="p-3 grid grid-cols-2 gap-y-2 text-txt-2">
              <div><span className="text-txt-3">المورّد:</span> <b className="text-txt">{chemical.supplier || 'N/A'}</b></div>
              <div><span className="text-txt-3">فئة التخزين:</span> <span className="mono text-txt">{chemical.storageClass || chemical.class}</span></div>
              <div><span className="text-txt-3">حالة المادة:</span> <b className="text-txt">{chemical.statusAr || chemical.status}</b></div>
              <div><span className="text-txt-3">إصدار SDS:</span> <span className="mono text-txt">{chemical.sdsVersion || 'Rev 1'} ({chemical.sds || '2026-12'})</span></div>
            </div>
          </div>

          {/* Emergency Summary */}
          {chemical.emergencySummary && (
            <div className="p-3.5 rounded bg-warn/10 border border-warn/30">
              <b className="text-warn font-semibold block mb-1 flex items-center gap-1.5">
                <Icon name="shield-check" size={14} /> تعليمات الطوارئ ومهمات الوقاية (PPE)
              </b>
              <p className="text-txt-2 leading-6">{chemical.emergencySummary}</p>
            </div>
          )}

          {/* Actions */}
          <div className="pt-3 border-t border-line flex flex-wrap items-center justify-between gap-2">
            <div className="flex gap-2">
              <Btn size="sm" icon="shield-check" onClick={onEmergencyGuide}>
                دليل الطوارئ
              </Btn>
              <Btn size="sm" icon="document" onClick={onAddSds}>
                + إضافة إصدار SDS
              </Btn>
              <Btn size="sm" icon="edit" onClick={onEdit}>
                تعديل المادة
              </Btn>
            </div>
            <Btn size="sm" variant="dgr" icon="trash" onClick={onDelete}>
              حذف المادة
            </Btn>
          </div>
        </div>
      </div>
    </div>
  )
}

function AddSdsModal({ chemicalId, chemicals, onClose, onSuccess }) {
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({
    chemicalId: chemicalId || chemicals[0]?.id || 1,
    versionNo: 'Rev 2',
    issueDate: new Date().toISOString().slice(0, 10),
    expiryDate: new Date(Date.now() + 2 * 365 * 864e5).toISOString().slice(0, 10),
    language: 'EN/AR',
    emergencySummary: 'عزل المنطقة واستخدام مهمات الوقاية الملائمة وإبلاغ مسؤول السلامة فوراً.',
  })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await hazmatApi.createSds(form)
      onSuccess()
    } catch (err) {
      alert(err.message || 'فشل في حفظ صحيفة SDS')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-md shadow-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <h3 className="font-bold text-base">إضافة / تحديث صحيفة بيانات السلامة (SDS)</h3>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={16} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-5 space-y-3 text-xs">
          {!chemicalId && (
            <div>
              <label className="block text-txt-2 font-semibold mb-1">المادة الكيميائية</label>
              <select
                value={form.chemicalId}
                onChange={(e) => setForm({ ...form, chemicalId: Number(e.target.value) })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              >
                {chemicals.map((c) => (
                  <option key={c.id} value={c.id}>{c.code} - {c.tradeName || c.name}</option>
                ))}
              </select>
            </div>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-txt-2 font-semibold mb-1">رقم الإصدار</label>
              <input
                type="text"
                required
                value={form.versionNo}
                onChange={(e) => setForm({ ...form, versionNo: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-txt-2 font-semibold mb-1">لغة الصحيفة</label>
              <select
                value={form.language}
                onChange={(e) => setForm({ ...form, language: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
              >
                <option value="EN/AR">عربي / إنجليزي (EN/AR)</option>
                <option value="AR">عربي (AR)</option>
                <option value="EN">إنجليزي (EN)</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-txt-2 font-semibold mb-1">تاريخ الإصدار</label>
              <input
                type="date"
                required
                value={form.issueDate}
                onChange={(e) => setForm({ ...form, issueDate: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
              />
            </div>
            <div>
              <label className="block text-txt-2 font-semibold mb-1">تاريخ انتهاء المراجعة</label>
              <input
                type="date"
                required
                value={form.expiryDate}
                onChange={(e) => setForm({ ...form, expiryDate: e.target.value })}
                className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-txt-2 font-semibold mb-1">تعليمات الطوارئ المحدثة</label>
            <textarea
              rows={3}
              value={form.emergencySummary}
              onChange={(e) => setForm({ ...form, emergencySummary: e.target.value })}
              className="in w-full py-2 px-3 rounded bg-steel border border-line text-txt text-xs"
            />
          </div>

          <div className="pt-3 border-t border-line flex justify-end gap-2">
            <Btn type="button" onClick={onClose}>إلغاء</Btn>
            <Btn type="submit" variant="pri" disabled={loading}>
              {loading ? 'جارٍ الحفظ...' : 'حفظ في الأرشيف'}
            </Btn>
          </div>
        </form>
      </div>
    </div>
  )
}

function SdsPreviewModal({ sds, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-3xl shadow-2xl overflow-hidden max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-line flex items-center justify-between bg-steel-3">
          <div className="flex items-center gap-3">
            <span className="p-2 rounded bg-info/15 text-info">
              <Icon name="document" size={20} />
            </span>
            <div>
              <h3 className="font-bold text-base">معاينة صحيفة بيانات السلامة (Safety Data Sheet)</h3>
              <p className="text-xs text-txt-3 font-mono">{sds.chemicalCode || 'CHM'} · {sds.tradeName || sds.name} · {sds.versionNo || sds.version}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={18} />
          </button>
        </div>

        {/* Document Viewer Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 text-xs font-sans bg-steel text-txt-2">
          {/* Section 1 */}
          <div className="p-4 rounded bg-steel-2 border border-line">
            <h4 className="font-bold text-txt border-b border-line pb-1.5 mb-2 text-sm text-accent">
              SECTION 1: Identification / تعريف المادة والمورد
            </h4>
            <div className="grid grid-cols-2 gap-2 leading-6">
              <div><b>الاسم التجاري:</b> {sds.tradeName || sds.name}</div>
              <div><b>الاسم العلمي:</b> {sds.chemicalName || 'N/A'}</div>
              <div><b>رقم CAS:</b> <span className="mono">{sds.casNumber || 'N/A'}</span></div>
              <div><b>الشركة الموردة:</b> {sds.supplier || 'ESCA HSE Supplier'}</div>
              <div><b>الإصدار:</b> {sds.versionNo || sds.version}</div>
              <div><b>اللغة:</b> {sds.language || 'EN/AR'}</div>
            </div>
          </div>

          {/* Section 2 */}
          <div className="p-4 rounded bg-steel-2 border border-line">
            <h4 className="font-bold text-txt border-b border-line pb-1.5 mb-2 text-sm text-accent">
              SECTION 2: Hazard Identification / تصنيف المخاطر وفق GHS
            </h4>
            <p className="mb-2">تُصنف هذه المادة وفق النظام العالمي المتوافق (GHS) كالتالي:</p>
            <div className="flex items-center gap-2">
              <Pill tone={sds.tone || 'warn'}>{sds.ghsClasses || 'HAZARDOUS'}</Pill>
              <span className="text-txt font-semibold">{sds.ghs || 'مادة كيميائية خاضعة لاشتراطات السلامة'}</span>
            </div>
          </div>

          {/* Section 4 */}
          <div className="p-4 rounded bg-steel-2 border border-line">
            <h4 className="font-bold text-txt border-b border-line pb-1.5 mb-2 text-sm text-accent">
              SECTION 4: First-Aid Measures / الإسعافات الأولية
            </h4>
            <ul className="list-disc list-inside space-y-1.5 leading-6">
              <li><b>ملامسة العين:</b> الغسيل الفوري بمحطة غسيل العيون لمدة لا تقل عن 15 دقيقة مع فتح الجفون واستدعاء الطبيب.</li>
              <li><b>ملامسة الجلد:</b> نزع الملابس الملوثة فوراً وغسل الجلد بالماء الجاري والصابون.</li>
              <li><b>الاستنشاق:</b> نقل المصاب إلى الهواء الطلق وتوفير الأكسجين عند الحاجة.</li>
              <li><b>الابتلاع:</b> عدم تحفيز القيء وطلب الرعاية الطبية الفورية ونقل نسخة من صحيفة SDS مع المصاب.</li>
            </ul>
          </div>

          {/* Section 6 & 8 */}
          <div className="p-4 rounded bg-steel-2 border border-line">
            <h4 className="font-bold text-txt border-b border-line pb-1.5 mb-2 text-sm text-accent">
              SECTION 8: Exposure Controls & PPE / مهمات الوقاية وإجراءات الطوارئ
            </h4>
            <p className="leading-6 mb-2">{sds.emergencySummary || 'عزل منطقة الانسكاب وتوفير معدات الحماية التنفسية والقفازات المقاومة للمواد الكيميائية.'}</p>
            <div className="flex flex-wrap gap-2 mt-2">
              <span className="px-2 py-1 rounded bg-steel-3 border border-line text-2xs">قفازات نيتريل كيميائية</span>
              <span className="px-2 py-1 rounded bg-steel-3 border border-line text-2xs">نظارات حماية مانعة للرذاذ</span>
              <span className="px-2 py-1 rounded bg-steel-3 border border-line text-2xs">قناع تنفسي مزود بفلتر أبخرة عضوية</span>
              <span className="px-2 py-1 rounded bg-steel-3 border border-line text-2xs">حذاء سلامة مقاوم للكيماويات</span>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3.5 border-t border-line bg-steel-3 flex justify-between items-center text-xs">
          <span className="text-txt-3 font-mono">ملف معتمد وموثق بقاعدة بيانات ESCA HSE</span>
          <Btn variant="pri" onClick={onClose}>إغلاق المعاينة</Btn>
        </div>
      </div>
    </div>
  )
}

function EmergencyGuideModal({ data, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-steel-2 border border-line rounded-lg w-full max-w-lg shadow-2xl overflow-hidden flex flex-col">
        <div className="p-4 border-b border-line flex items-center justify-between bg-crit/15">
          <div className="flex items-center gap-2.5">
            <span className="p-2 rounded bg-crit/20 text-crit">
              <Icon name="shield-check" size={20} />
            </span>
            <div>
              <h3 className="font-bold text-base text-crit">دليل الاستجابة للطوارئ الكيميائية</h3>
              <p className="text-xs text-txt-2 font-mono">{data.code || data.chemicalCode || ''} · {data.tradeName || data.name}</p>
            </div>
          </div>
          <button onClick={onClose} className="p-1 rounded hover:bg-steel text-txt-3 hover:text-txt">
            <Icon name="x" size={18} />
          </button>
        </div>

        <div className="p-5 space-y-3.5 text-xs">
          <div className="p-3 rounded bg-steel border border-line">
            <b className="text-txt block mb-1">تعليمات احتواء الانسكاب ومكافحة التسرب:</b>
            <p className="text-txt-2 leading-6">
              {data.emergencySummary || 'عزل مصدر التسرب فوراً، إبعاد أي مصادر اشتعال، واستخدام حبيبات امتصاص الانسكاب من طقم Spill Kit القريب.'}
            </p>
          </div>

          <div className="p-3 rounded bg-steel border border-line">
            <b className="text-txt block mb-1">أرقام هواتف الطوارئ الداخلية (ESCA Hotline):</b>
            <div className="grid grid-cols-2 gap-2 text-txt-2 mt-2">
              <div>غرفة تحكم السلامة: <b className="font-mono text-accent">1122</b></div>
              <div>العيادة الميدانية: <b className="font-mono text-accent">1133</b></div>
              <div>فريق مكافحة الحريق: <b className="font-mono text-accent">1144</b></div>
              <div>مشرف الموقع: <b className="font-mono text-accent">1155</b></div>
            </div>
          </div>

          <div className="pt-3 border-t border-line flex justify-end">
            <Btn variant="pri" onClick={onClose}>تم الاطلاع</Btn>
          </div>
        </div>
      </div>
    </div>
  )
}
