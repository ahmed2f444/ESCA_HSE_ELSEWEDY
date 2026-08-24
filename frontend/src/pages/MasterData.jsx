import { Async, Card, CardBody, CardHead, Grid, PageHeader, Pill, Table } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { masterData } from '../api/endpoints.js'
import { useApi } from '../hooks.jsx'

/**
 * Reference-data coverage — the Summary sheet of the master-data workbook,
 * rendered live from the loaded rows.
 *
 * The KPI counts are recomputed from the seed rather than copied out of the
 * sheet's own summary block. If a future drop of workbooks disagrees with its
 * own cover sheet, this screen shows the discrepancy instead of hiding it.
 */
export default function MasterData() {
  const data = useApi(() => masterData.summary(), [])

  return (
    <>
      <PageHeader title="ملخص البيانات المرجعية" meta="master data summary · loaded from plant workbooks" />

      <Async state={data} rows={6}>
        {(d) => {
          const loaded = Object.fromEntries(
            [
              ['Departments', d.departments.length],
              ['Zones', d.zoneCount],
              ['Employees', null],
              ['Active employees', null],
              ['Application users', null],
              ['RBAC roles', null],
            ].map(([k, v]) => [k, v])
          )

          return (
            <>
              <Card className="mb-3.5">
                <CardHead title={d.title || 'ESCA HSE | Master Data Summary'}>
                  <Pill tone="ok">
                    <Icon name="check" size={11} /> تم التحميل
                  </Pill>
                </CardHead>
                <CardBody>
                  <p className="text-sm text-txt-2 italic mb-4">{d.subtitle}</p>
                  <div className="grid sm:grid-cols-2 gap-x-8 max-w-2xl">
                    <div className="stat-line">
                      <span>As-of date</span>
                      <b>{d.asOfDate}</b>
                    </div>
                    <div className="stat-line">
                      <span>As-of timestamp</span>
                      <b>{d.asOfTimestamp}</b>
                    </div>
                  </div>
                </CardBody>
              </Card>

              <Grid cols={2}>
                <Card>
                  <CardHead title="مؤشرات التغطية" hint="KPI / VALUE" />
                  <Table head={['KPI', 'Value', 'من الملف']} clickable={false}>
                    {d.kpis.map((k) => {
                      const live = loaded[k.label]
                      const match = live == null || Number(live) === Number(k.value)
                      return (
                        <tr key={k.label}>
                          <td className="font-semibold">{k.label}</td>
                          <td className="mono text-[14px] font-bold text-txt">{k.value}</td>
                          <td>
                            {match ? (
                              <Icon name="check" size={14} className="text-safe" />
                            ) : (
                              <Pill tone="wn">محمّل {live}</Pill>
                            )}
                          </td>
                        </tr>
                      )
                    })}
                  </Table>
                </Card>

                <Card>
                  <CardHead title="عدد العاملين حسب القسم" hint="HEADCOUNT" />
                  <Table head={['Department', 'Headcount']} clickable={false}>
                    {d.headcountByDepartment.map((r) => (
                      <tr key={r.department}>
                        <td>{r.department}</td>
                        <td className="mono">{r.headcount}</td>
                      </tr>
                    ))}
                  </Table>
                </Card>
              </Grid>

              <Card className="mt-3.5">
                <CardHead title="الأقسام المحمّلة من الملفات" hint="LOADED DEPARTMENTS" />
                <Table
                  head={['الكود', 'القسم', 'الاسم بالإنجليزية', 'العاملون', 'المناطق', 'الحوادث', 'الطفايات', 'آخر جولة']}
                  clickable={false}
                >
                  {d.departments.map((z) => (
                    <tr key={z.code}>
                      <td className="mono">{z.code}</td>
                      <td>{z.name}</td>
                      <td className="text-xs text-txt-2">{z.nameEn}</td>
                      <td className="mono">{z.headcount}</td>
                      <td className="mono">{z.zoneCount}</td>
                      <td className="mono">{z.incidents}</td>
                      <td className="mono">{z.extinguishers}</td>
                      <td className="mono">{z.lastInspection}</td>
                    </tr>
                  ))}
                </Table>
              </Card>

              <Card className="mt-3.5">
                <CardHead title="مصدر البيانات" hint="SOURCE WORKBOOKS" />
                <CardBody>
                  <p className="text-sm text-txt-2 leading-8 mb-3">
                    كل الأرقام في النظام محمّلة من ملفات Excel اللي وفّرها المصنع — مافيش أرقام مكتوبة بالإيد.
                    إعادة التحميل بأمر واحد لما تيجي نسخة جديدة من الملفات:
                  </p>
                  <p className="mb-3">
                    <code className="font-mono num text-xs bg-steel px-2 py-1 rounded border border-line">
                      python etl/build_seed.py
                    </code>
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {d.sheets.generatedFrom.map((f) => (
                      <span key={f} className="tag">
                        {f}
                      </span>
                    ))}
                  </div>
                  <div className="mt-3.5 pt-3 border-t border-line grid sm:grid-cols-2 gap-x-8">
                    <div className="stat-line">
                      <span>عدد الجداول المحمّلة</span>
                      <b>{d.sheets.sheetCount}</b>
                    </div>
                    <div className="stat-line">
                      <span>إجمالي السجلات</span>
                      <b>{d.sheets.rowCount.toLocaleString('en-US')}</b>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </>
          )
        }}
      </Async>
    </>
  )
}
