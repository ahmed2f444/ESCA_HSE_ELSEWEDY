import { Async, Btn, Card, CardBody, CardHead, Grid, PageHeader, Pill, StatLine, Table } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { integrations as integApi } from '../api/endpoints.js'
import { useApi, useToast } from '../hooks.jsx'

export default function Integrations() {
  const toast = useToast()
  const list = useApi(() => integApi.list(), [])

  return (
    <>
      <PageHeader title="الربط والتكامل" meta="system integrations · excel seed + rest">
        <Btn icon="refresh" onClick={() => toast('تم تشغيل مزامنة يدوية لكل القنوات', 'in')}>
          مزامنة الآن
        </Btn>
      </PageHeader>

      <Card className="mb-3.5">
        <CardHead title="قنوات التكامل" hint="CONNECTED SYSTEMS" />
        <Async state={list} rows={6}>
          {(rows) => (
            <Table head={['النظام', 'الاتجاه', 'الوسيلة', 'التكرار', 'آخر تشغيل', 'السجلات', 'الحالة']} clickable={false}>
              {rows.map((r) => (
                <tr key={r.system}>
                  <td>{r.system}</td>
                  <td className="text-xs text-txt-2">{r.direction}</td>
                  <td className="mono text-2xs">{r.mode}</td>
                  <td className="text-xs">{r.frequency}</td>
                  <td className="mono">{r.lastRun}</td>
                  <td className="mono">{r.records}</td>
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
          <CardHead title="استيراد ملفات الشركة" hint="EXCEL SEED" />
          <CardBody className="text-sm text-txt-2 leading-8">
            <p className="mb-3">
              البيانات المرجعية (الموظفون، سجل الطفايات، مخزون معدات الوقاية، الكيماويات، هيكل المناطق) بتتحمّل
              من ملفات Excel اللي بتوفرها إدارة المصنع، مش من ربط مباشر بـ ERP. الملفات بتتنضّف وتتحوّل قبل
              التحميل — رؤوس أعمدة غير موحّدة، خلايا مدمجة، ووحدات قياس مختلطة.
            </p>
            <div className="pt-3 border-t border-line">
              <StatLine label="ملفات مستوردة" value="6 ملفات" />
              <StatLine label="سجلات محمّلة" value="911 سجل" />
              <StatLine label="سجلات مرفوضة (تحتاج مراجعة)" value="14" valueClass="text-warn" />
              <StatLine label="آخر عملية استيراد" value="2026-08-04" />
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHead title="حدود التكامل في هذه المرحلة" hint="SCOPE" />
          <CardBody className="text-sm text-txt-2 leading-8 space-y-3">
            <div className="flex gap-2.5">
              <Icon name="check" size={15} className="text-safe mt-1.5" />
              <span>
                <b className="text-txt">مطبّق:</b> استيراد Excel، وواجهات REST بين خدمات المشروع نفسها (الواجهة،
                الخدمة الأساسية، وخدمة الوكيل).
              </span>
            </div>
            <div className="flex gap-2.5">
              <Icon name="clock" size={15} className="text-warn mt-1.5" />
              <span>
                <b className="text-txt">محاكاة:</b> قراءات SCADA والحساسات — مولّدة محلياً بنفس شكل البيانات
                الحقيقية.
              </span>
            </div>
            <div className="flex gap-2.5">
              <Icon name="close" size={15} className="text-crit mt-1.5" />
              <span>
                <b className="text-txt">خارج النطاق:</b> ربط حي بـ ERP/HRMS، كاميرات فعلية، وأنظمة التحكم
                الصناعي — محتاجة بنية وصلاحيات مش متاحة في بيئة التدريب.
              </span>
            </div>
          </CardBody>
        </Card>
      </Grid>
    </>
  )
}
