import { useState } from 'react'
import { Async, Btn, Card, CardBody, CardHead, Grid, PageHeader, Pill, Table } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { security as secApi } from '../api/endpoints.js'
import { useApi } from '../hooks.jsx'
import tc from '../themeColors.js'

/** One CRUD grade cell. NONE reads as a dash so the eye skips it. */
function Grade({ v }) {
  if (!v || v === 'NONE') return <td className="text-center text-txt-3">—</td>
  const strong = String(v).includes('D') || v === 'CRUD' || v === 'RW'
  const write = /^C|U/.test(String(v))
  return (
    <td className="text-center">
      <span
        className="font-mono num text-2xs font-semibold px-1.5 py-0.5 rounded"
        style={{
          background: strong ? `rgb(var(--c-crit) / 0.14)` : write ? `rgb(var(--c-warn) / 0.14)` : `rgb(var(--c-info) / 0.14)`,
          color: strong ? tc.crit() : write ? tc.warn() : tc.info(),
        }}
      >
        {v}
      </span>
    </td>
  )
}

const ACTION_TONE = (a) =>
  a.includes('BLOCK') || a.includes('SUSPEND') ? tc.crit() : a.includes('APPROVE') ? tc.safe() : a.includes('CREATE') ? tc.warn() : tc.info()

export default function Security() {
  const [q, setQ] = useState('')
  const [term, setTerm] = useState('')

  const log = useApi(() => secApi.auditLog({ q: term }), [term])
  const roles = useApi(() => secApi.roles(), [])
  const sessions = useApi(() => secApi.sessions(), [])

  return (
    <>
      <PageHeader title="الأمن وسجل التدقيق" meta="rbac · append-only audit trail" />

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="مصفوفة الصلاحيات" hint="RBAC_MATRIX · من ملفات المصنع" />
          <Async state={roles} rows={10}>
            {(rows) => (
              <Table
                head={['الدور', 'مستخدمون', 'النطاق', 'حوادث', 'تصاريح', 'تفتيش', 'مخاطر', 'تدريب', 'صحة', 'إدارة', 'اعتماد عالي']}
                clickable={false}
              >
                {rows.map((r) => (
                  <tr key={r.roleId}>
                    <td>
                      <div className="font-medium">{r.roleAr}</div>
                      <div className="mono text-2xs">{r.role}</div>
                    </td>
                    <td className="mono">{r.users}</td>
                    <td className="mono text-2xs">{r.scope}</td>
                    <Grade v={r.incidents} />
                    <Grade v={r.permits} />
                    <Grade v={r.inspections} />
                    <Grade v={r.risks} />
                    <Grade v={r.training} />
                    <Grade v={r.health} />
                    <Grade v={r.admin} />
                    <td className="text-center">
                      {r.approveHighRisk ? (
                        <Icon name="check" size={14} className="text-safe" />
                      ) : (
                        <span className="text-txt-3">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
          <div className="card-b border-t border-line text-2xs text-txt-3 leading-6">
            الحروف زي ما هي في ملف <span className="font-mono num text-txt-2">RBAC_Matrix</span>:
            <span className="font-mono num text-txt-2"> C</span> إنشاء ·
            <span className="font-mono num text-txt-2"> R</span> قراءة ·
            <span className="font-mono num text-txt-2"> U</span> تعديل ·
            <span className="font-mono num text-txt-2"> D</span> حذف/إغلاق ·
            <span className="font-mono num text-txt-2"> NONE</span> بدون وصول.
          </div>
        </Card>

        <Card>
          <CardHead title="الجلسات النشطة" hint="ACTIVE SESSIONS" />
          <Async state={sessions} rows={4}>
            {(rows) => (
              <Table head={['المستخدم', 'الدور', 'الجهاز', 'IP', 'منذ', 'MFA']} clickable={false}>
                {rows.map((s) => (
                  <tr key={s.user}>
                    <td>{s.user}</td>
                    <td className="text-xs text-txt-2">{s.role}</td>
                    <td className="text-xs">{s.device}</td>
                    <td className="mono text-2xs">{s.ip}</td>
                    <td className="mono">{s.since}</td>
                    <td>
                      {s.mfa ? (
                        <Icon name="check" size={15} className="text-safe" />
                      ) : (
                        <span className="text-txt-3 text-2xs font-mono">service</span>
                      )}
                    </td>
                  </tr>
                ))}
              </Table>
            )}
          </Async>
        </Card>
      </Grid>

      <Card className="mb-3.5">
        <CardHead title="سجل التدقيق">
          <form
            className="relative"
            onSubmit={(e) => {
              e.preventDefault()
              setTerm(q)
            }}
          >
            <Icon name="search" size={13} className="absolute top-1/2 -translate-y-1/2 start-2.5 text-txt-3" />
            <input
              className="field py-1.5 ps-8 w-52 text-xs"
              placeholder="بحث بالمستخدم أو الإجراء…"
              value={q}
              onChange={(e) => setQ(e.target.value)}
            />
          </form>
        </CardHead>
        <Async state={log} rows={8}>
          {(rows) =>
            rows.length === 0 ? (
              <div className="py-10 text-center text-txt-3 text-sm">لا توجد سجلات مطابقة</div>
            ) : (
              <Table head={['التوقيت', 'المنفِّذ', 'الإجراء', 'الهدف', 'التفاصيل', 'القناة']} clickable={false}>
                {rows.map((r, i) => (
                  <tr key={i}>
                    <td className="mono whitespace-nowrap">{r.at}</td>
                    <td>{r.actor}</td>
                    <td>
                      <span className="font-mono num text-xs font-semibold" style={{ color: ACTION_TONE(r.action) }}>
                        {r.action}
                      </span>
                    </td>
                    <td className="mono">{r.target}</td>
                    <td className="text-xs text-txt-2">{r.detail}</td>
                    <td>
                      <Pill tone="nu">{r.channel}</Pill>
                    </td>
                  </tr>
                ))}
              </Table>
            )
          }
        </Async>
      </Card>

      <Card>
        <CardHead title="لماذا السجل غير قابل للتعديل" hint="APPEND-ONLY" />
        <CardBody className="text-sm text-txt-2 leading-8">
          كل عملية كتابة في النظام — سواء من مستخدم أو من خدمة الوكيل الآلي — بتضيف صف في جدول التدقيق ومحدش
          بيقدر يعدّله أو يمسحه، بما فيهم مدير النظام. ده اللي بيخلي حزمة تدقيق ISO 45001 مقبولة: المدقق
          الخارجي محتاج يتأكد إن التصريح الفلاني اتعتمد إمتى ومن مين، وإن الاعتماد ده ما اتغيّرش بعد الحادث.
          <br />
          <br />
          لاحظ في السجل فوق: <b className="text-txt font-mono num">agent-service</b> ظاهر كمنفِّذ لإيقاف تصريح —
          الوكيل بيقرأ من قاعدة البيانات مباشرة، لكن أي إجراء بيعمله بيعدّي على نفس الـ API وبيتسجّل بنفس الطريقة.
        </CardBody>
      </Card>
    </>
  )
}
