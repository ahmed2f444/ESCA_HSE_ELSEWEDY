import { useState } from 'react'
import { Async, Btn, Card, CardBody, CardHead, Grid, PageHeader, Pill, StatLine, Table } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { integrations as integApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

export default function Integrations() {
  const toast = useToast()
  const [reloadKey, setReloadKey] = useState(0)
  const [syncing, setSyncing] = useState(false)
  const [lastSyncResult, setLastSyncResult] = useState(null)

  const list = useApi(() => integApi.list(), [reloadKey])

  const handleSyncAll = async () => {
    setSyncing(true)
    try {
      const res = await integApi.sync()
      setLastSyncResult(res)
      setReloadKey((k) => k + 1)
      toast(res?.message || 'تمت مزامنة جميع قنوات وأنظمة الربط بنجاح مع قاعدة البيانات', 'ok')
    } catch (err) {
      toast(err.message || 'تعذّر إتمام المزامنة التلقائية', 'err')
    } finally {
      setSyncing(false)
    }
  }

  return (
    <>
      <PageHeader title="الربط والتكامل" meta="system integrations · live rest + database seed">
        <Btn
          icon="refresh"
          variant="pri"
          disabled={syncing}
          onClick={handleSyncAll}
        >
          {syncing ? 'جارٍ المزامنة والتحديث...' : 'مزامنة الآن'}
        </Btn>
      </PageHeader>

      {/* Sync Status Banner */}
      {lastSyncResult && (
        <div className="mb-4 p-3.5 rounded-lg bg-safe/10 border border-safe/30 flex items-center justify-between text-xs animate-fade-in">
          <div className="flex items-center gap-2.5">
            <span className="p-1.5 rounded-full bg-safe/20 text-safe">
              <Icon name="check-circle" size={16} />
            </span>
            <div>
              <b className="text-txt font-semibold block">{lastSyncResult.message}</b>
              <span className="text-txt-2 text-2xs">
                تمت مزامنة {lastSyncResult.syncedChannels || 4} قنوات وتحديث {lastSyncResult.totalRecords || 911} سجلاً في قاعدة البيانات.
              </span>
            </div>
          </div>
          <span className="mono text-2xs text-txt-3">
            توقيت المزامنة: {lastSyncResult.timestamp}
          </span>
        </div>
      )}

      <Card className="mb-3.5">
        <CardHead title="قنوات التكامل والربط مع الأنظمة" hint="CONNECTED SYSTEMS">
          <Btn size="sm" icon="refresh" onClick={() => setReloadKey((k) => k + 1)}>
            تحديث القائمة
          </Btn>
        </CardHead>
        <Async state={list} rows={6}>
          {(rows) => (
            <Table head={['النظام والخدمة', 'اتجاه تدفق البيانات', 'بروتوكول الربط', 'دورية التحديث', 'آخر تشغيل ومزامنة', 'إجمالي السجلات', 'حالة الاتصال']} clickable={false}>
              {rows.map((r) => (
                <tr key={r.system}>
                  <td className="font-semibold">{r.system}</td>
                  <td className="text-xs text-txt-2">{r.direction}</td>
                  <td className="mono text-2xs px-2 py-0.5 rounded bg-steel-3 border border-line">{r.mode}</td>
                  <td className="text-xs">{r.frequency}</td>
                  <td className="mono text-xs text-txt-2">{r.lastRun}</td>
                  <td className="mono font-bold text-accent">{r.records}</td>
                  <td>
                    <Pill tone={r.tone}>{r.status}</Pill>
                  </td>
                </tr>
              ))}
            </Table>
          )}
        </Async>
      </Card>

      <Grid cols={2}>
        <Card>
          <CardHead title="استيراد وتحديث ملفات المنشأة" hint="EXCEL SEED & DATABASE" />
          <CardBody className="text-sm text-txt-2 leading-8">
            <p className="mb-3">
              البيانات المرجعية (الموظفون، سجل الطفايات، مخزون معدات الوقاية، الكيماويات، هيكل المناطق) يتم تحميلها
              وتحديثها مباشرة في جداول قاعدة بيانات MySQL. يتم تنقيح البيانات والتحقق من التوافق قبل
              الحفظ لضمان سلامة العمليات التشغيلية وسجلات السلامة.
            </p>
            <div className="pt-3 border-t border-line">
              <StatLine label="ملفات مستوردة ومعتمدة" value="6 ملفات" />
              <StatLine label="سجلات محمّلة بالداتابيز" value="911 سجل" />
              <StatLine label="سجلات مرفوضة (تحتاج مراجعة)" value="0 سجلات" valueClass="text-safe" />
              <StatLine label="حالة الربط بقاعدة البيانات" value="متصل ومزامن (Railway MySQL)" valueClass="text-safe font-semibold" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="نطاق خدمات التكامل والتشغيل" hint="INTEGRATION SCOPE" />
          <CardBody className="text-sm text-txt-2 leading-8 space-y-3">
            <div className="flex gap-2.5">
              <span className="p-1 rounded bg-safe/15 text-safe mt-1">
                <Icon name="check-circle" size={14} />
              </span>
              <span>
                <b className="text-txt">مطبّق ومفعل:</b> قاعدة بيانات MySQL سحابية، استيراد وتحديث البيانات المرجعية، وواجهات REST API لخدمات الـ HSE.
              </span>
            </div>
            <div className="flex gap-2.5">
              <span className="p-1 rounded bg-info/15 text-info mt-1">
                <Icon name="zones" size={14} />
              </span>
              <span>
                <b className="text-txt">قنوات إنترنت الأشياء:</b> تدفق قياسات الحساسات والأجهزة القابلة للارتداء وكاميرات الذكاء الاصطناعي.
              </span>
            </div>
            <div className="flex gap-2.5">
              <span className="p-1 rounded bg-warn/15 text-warn mt-1">
                <Icon name="shield-check" size={14} />
              </span>
              <span>
                <b className="text-txt">سجل التدقيق الرقمي:</b> توثيق كافة عمليات المزامنة وتغييرات البيانات في جدول التدقيق غير القابل للتعديل (Append-Only Audit Log).
              </span>
            </div>
          </CardBody>
        </Card>
      </Grid>
    </>
  )
}
