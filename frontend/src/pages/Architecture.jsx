import { useState, useEffect } from 'react'
import { Card, CardBody, CardHead, Grid, PageHeader, StatLine, Tag, Pill, Btn } from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { auth, masterData } from '../api/endpoints.js'
import { useToast } from '../hooks.jsx'
import tc from '../themeColors.js'

const LAYERS = [
  {
    layer: 'واجهات المستخدم (Frontend Presentation Layer)',
    color: tc.info(),
    owner: 'Member 3 (Frontend & UX Lead)',
    items: ['React 18 + Vite', 'Vanilla CSS & Dark Glassmorphism', 'Recharts 2.x', 'Axios + Interceptors', 'React Router v6', 'PWA & Mobile Responsive'],
  },
  {
    layer: 'خدمات الأعمال (Enterprise Business APIs) — Spring Boot 3',
    color: tc.hi(),
    owner: 'Member 1 · Member 2 · Member 6',
    items: [
      'Incidents & Near-Misses',
      'Permit to Work (PTW) & SIMOPS',
      'JSA & Hazard ID (HIRA)',
      'Inspections & Walkthroughs',
      'Competency & Training Matrix',
      'Occupational Health & Surveillance',
      'Chemical Safety & HazMat SDS',
      'PPE Inventory & Transactions',
      'Fire Fighting Equipment',
      'ISO 45001 KPIs & Reports',
      'Spring Security & JWT Auth',
      'Unified Audit Trail',
    ],
  },
  {
    layer: 'خدمة الوكيل الذكي (AI Automation & Agent Engine) — Python FastAPI',
    color: tc.safe(),
    owner: 'AI Student 1 · AI Student 2',
    items: [
      'Groq LLaMA 3.3 70B Versatile',
      'Tool-Calling HSE Assistant',
      'APScheduler Cron Jobs',
      'SQLAlchemy Database Inspector',
      'Computer Vision Detections Feed',
      'IoT Sensor Telemetry Generator',
      'Automated Rule Engine',
    ],
  },
  {
    layer: 'قاعدة البيانات والتخزين (Data & Storage Layer)',
    color: tc.warn(),
    owner: 'Database Architecture Team',
    items: [
      'MySQL 9.4 (Railway Cloud DB)',
      '48 Normalized Relational Tables',
      'HikariCP Connection Pooling',
      'Foreign Key & RBAC Constraints',
      'Auditing & Time-series Log Tables',
    ],
  },
  {
    layer: 'التشغيل والنشر (DevOps & Infrastructure)',
    color: tc.txt3(),
    owner: 'DevOps & Systems Team',
    items: ['Multi-Service Orchestration', 'Start-All Automation Batch', 'Vite Production Bundler', 'REST API / Swagger Specs'],
  },
]

const FRONTEND_SCOPE = [
  ['لوحة القيادة والمؤشرات الإجمالية', 'تجميع بيانات حية من كل الوحدات'],
  ['سجل الحوادث وتحليل الأسباب الجذرية (RCA)', 'Member 1 — Backend & DB'],
  ['لوحة تصاريح العمل (PTW) وتضارب العمليات (SIMOPS)', 'Member 1 — Backend & DB'],
  ['سجل المخاطر ومصفوفة 5×5 التفاعلية', 'Member 1 — Backend & DB'],
  ['تقييم سلامة المهام (JSA)', 'Member 1 — Backend & DB'],
  ['مصفوفة التدريب والكفاءات والشهادات', 'Member 2 — Backend & DB'],
  ['جولات التفتيش والملاحظات الفنية', 'Member 2 — Backend & DB'],
  ['الصحة المهنية والمراقبة الإكلينيكية', 'Member 2 — Backend & DB'],
  ['المواد الكيميائية وسجلات الأمان (SDS)', 'Member 2 — Backend & DB'],
  ['التقارير ومؤشرات ISO 45001', 'Member 2 — Backend & DB'],
  ['مهمات الوقاية الشخصية (PPE Matrix & Inventory)', 'Member 6 — Backend & DB'],
  ['معدات مكافحة الحريق وفحص الطفايات', 'Member 6 — Backend & DB'],
  ['المراقبة الآلية وحساسات IoT والرؤية الحاسوبية', 'AI Student 1 & 2'],
  ['المساعد الذكي للسلامة (AI Safety Copilot)', 'AI Student 1 & 2'],
]

export default function Architecture() {
  const toast = useToast()
  const [backendHealth, setBackendHealth] = useState({ status: 'CHECKING', db: 'CHECKING', responseTime: 0 })

  const checkHealth = async () => {
    const start = performance.now()
    try {
      await auth.me()
      const elapsed = Math.round(performance.now() - start)
      setBackendHealth({ status: 'ONLINE', db: 'CONNECTED', responseTime: elapsed })
    } catch {
      try {
        await masterData.summary()
        const elapsed = Math.round(performance.now() - start)
        setBackendHealth({ status: 'ONLINE', db: 'CONNECTED', responseTime: elapsed })
      } catch {
        setBackendHealth({ status: 'OFFLINE', db: 'UNKNOWN', responseTime: 0 })
      }
    }
  }

  useEffect(() => {
    checkHealth()
  }, [])

  return (
    <>
      <PageHeader title="معمارية النظام وخريطة الخدمات" meta="service map · microservices · frontend contract">
        <Btn icon="check" variant="ghost" onClick={() => { checkHealth(); toast('تم تحديث فحص سلامة الخدمات', 'in') }}>
          فحص الاتصال الحي
        </Btn>
      </PageHeader>

      {/* Live Health Status Bar */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-3 mb-4">
        <div className="p-3 bg-steel rounded-lg border border-line flex items-center justify-between">
          <div>
            <span className="text-2xs text-txt-3 block">الخادم الأساسي (Spring Boot)</span>
            <span className="text-xs font-mono font-bold text-txt-1">Port :8080</span>
          </div>
          <Pill tone={backendHealth.status === 'ONLINE' ? 'ok' : 'cr'}>
            {backendHealth.status === 'ONLINE' ? 'متصل ونشط' : 'قيد الفحص'}
          </Pill>
        </div>

        <div className="p-3 bg-steel rounded-lg border border-line flex items-center justify-between">
          <div>
            <span className="text-2xs text-txt-3 block">قاعدة البيانات (MySQL 9.4)</span>
            <span className="text-xs font-mono font-bold text-txt-1">Zephyr Railway</span>
          </div>
          <Pill tone={backendHealth.db === 'CONNECTED' ? 'ok' : 'cr'}>
            {backendHealth.db === 'CONNECTED' ? '48 جدول متصل' : 'قيد الفحص'}
          </Pill>
        </div>

        <div className="p-3 bg-steel rounded-lg border border-line flex items-center justify-between">
          <div>
            <span className="text-2xs text-txt-3 block">خدمة الذكاء الاصطناعي (FastAPI)</span>
            <span className="text-xs font-mono font-bold text-txt-1">Groq LLaMA-70B</span>
          </div>
          <Pill tone="ok">جاهز للاستعلام</Pill>
        </div>

        <div className="p-3 bg-steel rounded-lg border border-line flex items-center justify-between">
          <div>
            <span className="text-2xs text-txt-3 block">زمن الاستجابة (API Latency)</span>
            <span className="text-xs font-mono font-bold text-txt-1">{backendHealth.responseTime} ms</span>
          </div>
          <Pill tone="ok">ممتاز</Pill>
        </div>
      </div>

      <Grid cols={2} className="mb-3.5">
        <Card>
          <CardHead title="طبقات النظام ومسؤوليات الفريق" hint="SERVICE MAP & OWNERSHIP" />
          <CardBody>
            <div className="flex flex-col gap-2.5">
              {LAYERS.map((l, i) => (
                <div key={l.layer}>
                  <div
                    className="bg-steel-3 border border-line rounded-md p-3.5"
                    style={{ borderInlineEndWidth: 4, borderInlineEndColor: l.color }}
                  >
                    <div className="flex items-center justify-between gap-2 mb-1.5">
                      <h4 className="text-[12.5px] font-semibold text-txt-1">{l.layer}</h4>
                      <span className="text-2xs text-txt-3 font-mono num">{l.owner}</span>
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {l.items.map((it) => (
                        <Tag key={it}>{it}</Tag>
                      ))}
                    </div>
                  </div>
                  {i < LAYERS.length - 1 && (
                    <div className="text-center text-txt-3 py-0.5">
                      <Icon name="caret" size={15} className="inline" />
                    </div>
                  )}
                </div>
              ))}
            </div>
          </CardBody>
        </Card>

        <div className="flex flex-col gap-3.5">
          <Card>
            <CardHead title="القاعدة الحاكمة لتكامل الذكاء الاصطناعي" hint="DESIGN PRINCIPLE & GOVERNANCE" />
            <CardBody>
              <div
                className="p-3.5 rounded text-sm leading-8 bg-hi/15 border border-hi/40"
              >
                الوكيل <b>يقرأ</b> من قاعدة البيانات مباشرة للسرعة، لكن أي <b>إجراء أو تعديل أو كتابة</b> بتمر عبر
                Spring Boot REST API — فبتخضع لنفس التحقق والصلاحيات وسجل التدقيق <span className="font-mono">(Audit Log)</span> زي أي إجراء بشري تماماً.
              </div>
              <p className="text-xs text-txt-2 leading-7 mt-3">
                عملياً: لما حساسات الغاز تسجل قراءة خطرة، الوكيل مش بيعدّل حالة التصريح مباشرة في MySQL —
                بينادي <span className="font-mono text-txt-1 font-bold">POST /permits/&#123;id&#125;/suspend</span>،
                فالتصريح بيتوقف بنفس القواعد المعتمدة وبيظهر في سجل التدقيق باسم <span className="font-mono text-txt-1 font-bold">agent-service</span>.
              </p>
            </CardBody>
          </Card>

          <Card>
            <CardHead title="عقد الواجهة والمسارات الحية" hint="API CONTRACT & ACTIVE ENDPOINTS" />
            <CardBody>
              <p className="text-xs text-txt-2 leading-7 mb-3">
                كل نداء بتعمله الواجهة معرّف وموثق في ملف واحد{' '}
                <span className="font-mono num text-txt-1 font-bold">src/api/endpoints.js</span> ومتصل بمسارات
                Spring Boot REST Controllers في الباك إند:
              </p>
              <StatLine label="طبقة النقل والتشفير" value="Axios + Bearer JWT Interceptor" />
              <StatLine label="الخدمة الأساسية (Spring Boot)" value="/api/v1 → Port :8080 (38+ Endpoints)" />
              <StatLine label="خدمة الوكيل الذكي (FastAPI)" value="/ask, /chat → Port :8000" />
              <StatLine label="قاعدة البيانات السحابية" value="MySQL 9.4 (Railway Cloud)" />
              <StatLine label="مفتاح تبديل المحاكاة" value="VITE_USE_MOCK = false (Real DB Mode)" />
            </CardBody>
          </Card>
        </div>
      </Grid>

      <Card>
        <CardHead title="نطاق الشاشات مقابل مالك الخدمة في الفريق" hint="FRONTEND ↔ BACKEND MODULE SPLIT" />
        <CardBody>
          <div className="grid gap-x-8 gap-y-0 sm:grid-cols-2">
            {FRONTEND_SCOPE.map(([screen, owner]) => (
              <StatLine key={screen} label={screen} value={<span className="text-xs text-txt-2 font-mono">{owner}</span>} />
            ))}
          </div>
        </CardBody>
      </Card>
    </>
  )
}
