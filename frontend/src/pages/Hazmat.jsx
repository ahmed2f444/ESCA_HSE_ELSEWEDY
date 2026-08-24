import { Async, Btn, Card, CardBody, CardHead, Grid, Kpi, KpiRow, PageHeader, Pill, Table } from '../components/ui.jsx'
import { hazmat as hazmatApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

const CELL = {
  '✓': { color: '#38B87C', label: 'تخزين مشترك مسموح' },
  '!': { color: '#F09030', label: 'فصل إلزامي' },
  X: { color: '#E0483C', label: 'محظور التخزين معاً' },
}

export default function Hazmat() {
  const toast = useToast()
  const list = useApi(() => hazmatApi.list(), [])
  const stats = useApi(() => hazmatApi.stats(), [])
  const compat = useApi(() => hazmatApi.compatibility(), [])

  return (
    <>
      <PageHeader title="المواد الخطرة والكيماويات" meta="hazmat inventory · sds register">
        <Btn icon="document" onClick={() => toast('فتح أرشيف صحائف بيانات السلامة (SDS)', 'in')}>
          أرشيف SDS
        </Btn>
        <Btn variant="pri" icon="plus" onClick={() => toast('تسجيل مادة جديدة', 'in')}>
          تسجيل مادة
        </Btn>
      </PageHeader>

      <Async state={stats} rows={3}>
        {(s) => (
          <KpiRow>
            <Kpi label="مواد مسجّلة" value={s.total} tone="info" sub="كل المواد لها SDS في الملف" />
            <Kpi label="قابلة للاشتعال" value={s.flammable} tone="crit" sub="تخزين منفصل إلزامي" />
            <Kpi label="أكّالة" value={s.corrosive} tone="warn" sub="تحتاج حوض احتواء" />
            <Kpi label="SDS منتهية المراجعة" value={s.sdsExpired} tone="crit" trend="down" sub="تحتاج تحديث من المورّد" />
            <Kpi label="أطقم مكافحة الانسكاب" value={s.spillKits} tone="safe" sub="موزّعة على المناطق" />
          </KpiRow>
        )}
      </Async>

      <Card className="mb-3.5">
        <CardHead title="سجل المواد الكيميائية" hint="CHEMICAL REGISTER" />
        <Async state={list} rows={8}>
          {(rows) => (
            <Table head={['الكود', 'المادة', 'التصنيف GHS', 'الكمية', 'موقع التخزين', 'الفئة', 'مراجعة SDS']} clickable={false}>
              {rows.map((c) => (
                <tr key={c.code}>
                  <td className="mono">{c.code}</td>
                  <td>{c.name}</td>
                  <td>
                    <Pill tone={c.tone}>{c.ghs}</Pill>
                  </td>
                  <td className="mono">{c.qty}</td>
                  <td className="text-xs text-txt-2">{c.location}</td>
                  <td className="mono text-2xs">{c.class}</td>
                  <td className="mono" style={{ color: c.sds < '2025-06' ? '#E0483C' : undefined }}>
                    {c.sds}
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Async>
      </Card>

      <Grid cols={2}>
        <Card>
          <CardHead title="مصفوفة التوافق في التخزين" hint="COMPATIBILITY MATRIX" />
          <CardBody>
            <Async state={compat} rows={5}>
              {(m) => (
                <>
                  <div className="tw">
                    <table className="tbl" style={{ textAlign: 'center' }}>
                      <thead>
                        <tr>
                          <th />
                          {m.groups.map((g) => (
                            <th key={g} className="text-center">
                              {g}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {m.grid.map((row, i) => (
                          <tr key={i}>
                            <th className="text-start">{m.groups[i]}</th>
                            {row.map((v, j) => (
                              <td key={j} className="text-center">
                                <span
                                  className="inline-flex items-center justify-center w-7 h-7 rounded font-mono num font-bold text-xs"
                                  title={CELL[v].label}
                                  style={{ background: `${CELL[v].color}22`, color: CELL[v].color, border: `1px solid ${CELL[v].color}55` }}
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
                  <div className="flex flex-wrap gap-4 text-xs text-txt-2 mt-3">
                    {Object.entries(CELL).map(([k, v]) => (
                      <span key={k} className="flex items-center gap-1.5">
                        <b className="font-mono num" style={{ color: v.color }}>
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
          <CardHead title="ضوابط التخزين المطبّقة" hint="STORAGE CONTROLS" />
          <CardBody className="text-sm text-txt-2 leading-8 space-y-3">
            <p>
              خزانة المذيبات مزوّدة بتهوية قسرية وحوض احتواء بسعة 110% من أكبر عبوة، والأسيتون والأسيتيلين
              مفصولان عن أي مصدر إشعال بمسافة لا تقل عن 11م — نفس الحد المستخدم في قاعدة تعارض العمل الساخن.
            </p>
            <p>
              كل مادة مرتبطة بصحيفة بيانات السلامة (SDS) الخاصة بها، وأي مادة صحيفتها أقدم من سنتين تظهر
              بالأحمر في السجل لأن بيانات الطوارئ فيها ممكن تكون اتغيّرت.
            </p>
            <p className="text-txt-3 text-xs">
              طباعة ملصقات GHS خارج نطاق المشروع التدريبي — السجل بيحتفظ ببيانات التصنيف فقط.
            </p>
          </CardBody>
        </Card>
      </Grid>
    </>
  )
}
