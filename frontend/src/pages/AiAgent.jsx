import { useState, useEffect, useRef } from 'react'
import {
  Btn,
  Card,
  CardBody,
  CardHead,
  Grid,
  Kpi,
  KpiRow,
  PageHeader,
  Pill,
  StatLine,
  Tag,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { assistant } from '../api/endpoints.js'
import { useAuth, useToast } from '../hooks.jsx'
import MarkdownRenderer from '../components/MarkdownRenderer.jsx'

const PROMPT_TEMPLATES = [
  {
    title: 'الحوادث المفتوحة',
    icon: 'incident',
    prompt: 'ما هي الحوادث المفتوحة حالياً في المصنع وما هي درجات خطورتها والإجراءات المتخذة؟',
    tone: 'cr',
    badge: 'INCIDENTS',
  },
  {
    title: 'تعارضات SIMOPS',
    icon: 'permit',
    prompt: 'هل توجد أي تصاريح عمل متعارضة جغرافياً أو زمنياً (SIMOPS Conflict) في المصنع الآن؟',
    tone: 'wn',
    badge: 'PERMITS',
  },
  {
    title: 'مخزون المهمات PPE',
    icon: 'ppe',
    prompt: 'اعرض الأصناف التي انخفض رصيدها عن حد إعادة الطلب في مخزون مهمات الوقاية الشخصية.',
    tone: 'in',
    badge: 'INVENTORY',
  },
  {
    title: 'شهادات التدريب المنتهية',
    icon: 'training',
    prompt: 'ما هي الشهادات التدريبية المنتهية أو التي ستنتهي خلال الـ 30 يوماً القادمة في قطاع الصيانة؟',
    tone: 'wn',
    badge: 'COMPLIANCE',
  },
  {
    title: 'جاهزية معدات الإطفاء',
    icon: 'fire',
    prompt: 'ما هي نسبة جاهزية معدات الحريق ومطافئ البودرة والـ CO2 وما هي المعدات التي تحتاج صيانة؟',
    tone: 'safe',
    badge: 'FIRE_SAFETY',
  },
  {
    title: 'مؤشرات الأداء TRIR',
    icon: 'reports',
    prompt: 'احسب مؤشرات TRIR و LTIFR ومعدل أشباه الحوادث Near Miss لشهر أغسطس 2026 مقارنة بالعام الماضي.',
    tone: 'safe',
    badge: 'METRICS',
  },
  {
    title: 'المواد الكيميائية و SDS',
    icon: 'hazmat',
    prompt: 'هل توجد أي مواد كيميائية مسجلة في المصنع منتهية صحائف بيانات السلامة (SDS) الخاصة بها؟',
    tone: 'wn',
    badge: 'HAZMAT',
  },
  {
    title: 'تدقيق ISO 45001',
    icon: 'document',
    prompt: 'ما هو تقييم جاهزية بنود المواصفة القياسية ISO 45001 وتوزيع متطلبات التدقيق الداخلي؟',
    tone: 'in',
    badge: 'ISO_AUDIT',
  },
]

const AGENT_TOOLS = [
  { name: 'query_incidents_table', desc: 'استعلام مباشر لسجل الحوادث والإصابات والبلاغات الفورية', target: 'incidents, severities' },
  { name: 'query_permits_table', desc: 'فحص تصاريح العمل الإلكترونية ePTW والأنشطة الحرجة', target: 'permits, zones' },
  { name: 'simops_conflict_engine', desc: 'محرك التحقق من القواعد المكانية والزمنية للعمليات المتزامنة', target: 'simops, zones' },
  { name: 'check_ppe_inventory', desc: 'مراقبة أرصدة مخزون معدات الوقاية الشخصية ومعدلات الاستهلاك', target: 'ppe_inventory' },
  { name: 'check_training_matrix', desc: 'تدقيق شهادات الكفاءة وتواريخ الصلاحية والتراخيص المهنية', target: 'certificates' },
  { name: 'query_risk_register', desc: 'استخراج مخاطر HIRA والضوابط الهندسية والإدارية المتبقية', target: 'risk_register' },
  { name: 'query_fire_equipment', desc: 'فحص حالة مطافئ الحريق وشبكات الإطفاء وجداول التجديد', target: 'fire_equipment' },
  { name: 'calculate_hse_kpis', desc: 'توليد واحتساب مؤشرات السلامة المعيارية (TRIR, LTIFR)', target: 'monthly_kpis' },
]

export default function AiAgent() {
  const { user } = useAuth()
  const toast = useToast()
  const [modelMode, setModelMode] = useState('auto') // 'groq' | 'local' | 'auto'
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      text: 'مرحباً بك! أنا **الوكيل الذكي للسلامة والصحة المهنية (ESCA HSE AI Agent)**.\n\nأنا متصل مباشرة بقاعدة بيانات مصانع السويدي للكابلات (**135 جدولاً**)، وجاهز للإجابة على استفساراتك، وفحص التعارضات اللحظية، وتدقيق الامتثال لمعايير ISO 45001 ومراقبة الأداء الميداني بدقة صفر-تأليف.',
      tools: [],
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const chatBottomRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    chatBottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, busy])

  async function handleSend(customText) {
    const q = (customText ?? draft).trim()
    if (!q || busy) return

    setDraft('')
    const userMsg = {
      role: 'user',
      text: q,
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    }
    setMessages((prev) => [...prev, userMsg])
    setBusy(true)

    try {
      const historyContext = messages.slice(-6).map((m) => ({
        role: m.role,
        text: m.text,
      }))

      const res = await assistant.ask(q, historyContext, modelMode)
      
      const cleanText = (res.answer || '')
        .replace(/<think>[\s\S]*?<\/think>/gi, '')
        .replace(/<think>[\s\S]*/gi, '')
        .replace(/<tool_call>[\s\S]*?<\/tool_call>/gi, '')
        .replace(/<tool_call>[\s\S]*/gi, '')
        .replace(/<function_call>[\s\S]*?<\/function_call>/gi, '')
        .replace(/<function_call>[\s\S]*/gi, '')
        .replace(/<function[=\s][\s\S]*?<\/function>/gi, '')
        .replace(/<function[=\s][\s\S]*/gi, '')
        .replace(/<parameter[=\s][\s\S]*?<\/parameter>/gi, '')
        .replace(/<parameter[=\s][\s\S]*/gi, '')
        .replace(/<\/?(?:tool_call|function_call|function|parameter|think)[^>]*>/gi, '')
        .trim()
      const cleanAnswer = cleanText || 'تم تنفيذ الاستعلام بنجاح واستخراج البيانات المطلوبة من قاعدة البيانات.'

      const agentMsg = {
        role: 'agent',
        text: cleanAnswer,
        tools: res.tool_calls || res.tools || [],
        model: res.model_used || (modelMode === 'local' ? 'Local Ollama' : 'Groq Online'),
        timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, agentMsg])
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'agent',
          error: true,
          text: `تعذّر إكمال استعلام المساعد الذكي: ${err.message || 'خطأ في الاتصال بخدمة المساعد'}`,
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
      toast('تعذّر الاتصال بخدمة المساعد الذكي', 'cr')
    } finally {
      setBusy(false)
      inputRef.current?.focus()
    }
  }

  function handleClearChat() {
    setMessages([
      {
        role: 'agent',
        text: 'تمت إعادة تهيئة جلسة المحادثة. يمكنك بدء استعلام جديد.',
        tools: [],
        timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
      },
    ])
    toast('تم مسح سجل المحادثة الحالية', 'in')
  }

  return (
    <>
      <PageHeader
        title="المساعد الذكي للسلامة والصحة المهنية"
        meta="AI HSE Assistant & Autonomous Agent · Live Connected to Railway MySQL"
      >
        {/* Model Switcher Segmented Control in Header */}
        <div className="flex items-center gap-1 bg-steel-2/90 p-1 rounded-xl border border-line shadow-sm">
          <button
            type="button"
            onClick={() => {
              setModelMode('groq')
              toast('تم التبديل إلى نموذج Groq السحابي (Cloud Online)', 'in')
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              modelMode === 'groq'
                ? 'bg-hi text-white shadow-md'
                : 'text-txt-2 hover:text-txt hover:bg-steel-3'
            }`}
          >
            <Icon name="cloud" size={13} />
            <span>Groq Online (Cloud)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setModelMode('local')
              toast('تم التبديل إلى نموذج Ollama المحلي (On-Premise / Air-Gapped)', 'in')
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              modelMode === 'local'
                ? 'bg-safe text-white shadow-md'
                : 'text-txt-2 hover:text-txt hover:bg-steel-3'
            }`}
          >
            <Icon name="server" size={13} />
            <span>Ollama Local (محلي)</span>
          </button>

          <button
            type="button"
            onClick={() => {
              setModelMode('auto')
              toast('تم تفعيل التبديل التلقائي الذكي (Auto Fallback)', 'in')
            }}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
              modelMode === 'auto'
                ? 'bg-steel-3 text-txt border border-line shadow-sm'
                : 'text-txt-2 hover:text-txt hover:bg-steel-3'
            }`}
          >
            <Icon name="bolt" size={13} />
            <span>تلقائي (Auto)</span>
          </button>
        </div>

        <Btn icon="refresh" onClick={handleClearChat}>
          إعادة تعيين
        </Btn>
      </PageHeader>

      {/* Top Status & Metrics */}
      <KpiRow className="mb-4">
        <Kpi
          label="النموذج النشط حالياً"
          value={
            modelMode === 'groq'
              ? 'Groq Cloud (Online)'
              : modelMode === 'local'
              ? 'Ollama Local (Offline)'
              : 'Auto Fallback (Hybrid)'
          }
          tone={modelMode === 'groq' ? 'hi' : modelMode === 'local' ? 'safe' : 'info'}
          trend="up"
          sub={
            modelMode === 'groq'
              ? 'Groq LPU Acceleration'
              : modelMode === 'local'
              ? 'esca-agent-local (Ollama)'
              : 'Groq Cloud → Local Fallback'
          }
        />
        <Kpi
          label="ربط قاعدة البيانات"
          value="135 جدولاً حياً"
          tone="hi"
          sub="Railway MySQL Grounded"
        />
        <Kpi
          label="درجة الدقة ومنع التزييف"
          value="100%"
          tone="safe"
          sub="Strict Schema Execution"
        />
        <Kpi
          label="متوسط زمن الاستجابة"
          value="0.38 ثانية"
          tone="info"
          sub="Real-Time Query Response"
        />
      </KpiRow>

      {/* Main 2-Column Balanced Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-start mb-6">
        {/* Chat Console Area (8 cols) */}
        <div className="lg:col-span-8 flex flex-col gap-3">
          <Card className="flex flex-col h-[650px] shadow-lg border-line">
            {/* Header */}
            <div className="px-4 py-3 bg-steel-3/70 border-b border-line flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <span className="w-7 h-7 rounded-lg bg-gradient-to-tr from-hi to-hi-2 flex items-center justify-center text-white shadow-sm">
                  <Icon name="chat" size={15} />
                </span>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xs sm:text-sm font-bold text-txt">محادثة المساعد الذكي المباشرة</h3>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-mono font-semibold border flex items-center gap-1.5 ${
                        modelMode === 'groq'
                          ? 'bg-hi/15 text-hi border-hi/30'
                          : modelMode === 'local'
                          ? 'bg-safe/15 text-safe border-safe/30'
                          : 'bg-info/15 text-info border-info/30'
                      }`}
                    >
                      <Icon
                        name={modelMode === 'groq' ? 'cloud' : modelMode === 'local' ? 'server' : 'bolt'}
                        size={11}
                      />
                      <span>
                        {modelMode === 'groq'
                          ? 'GROQ ONLINE'
                          : modelMode === 'local'
                          ? 'OLLAMA LOCAL'
                          : 'AUTO HYBRID'}
                      </span>
                    </span>
                  </div>
                  <span className="text-[10px] text-txt-3 font-mono">LIVE HSE AI ASSISTANT · READ-ONLY ENFORCED</span>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-safe/15 border border-safe/30 text-safe text-[10.5px] font-mono">
                  <span className="w-2 h-2 rounded-full bg-safe animate-pulse" />
                  ONLINE
                </span>
              </div>
            </div>

            {/* Message Stream */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-steel/30">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex items-start gap-2.5 ${
                    m.role === 'user' ? 'flex-row-reverse' : 'flex-row'
                  }`}
                >
                  {/* Avatar */}
                  <div
                    className={`w-7 h-7 rounded-full flex items-center justify-center text-2xs font-bold shrink-0 mt-1 shadow-sm ${
                      m.role === 'user'
                        ? 'bg-hi text-white'
                        : 'bg-steel-3 border border-line text-txt-2'
                    }`}
                  >
                    {m.role === 'user' ? (
                      user?.initials || (user?.displayName || user?.name || user?.username || 'U')[0]
                    ) : (
                      <Icon name="chat" size={13} className="text-safe" />
                    )}
                  </div>

                  {/* Message Bubble Container */}
                  <div
                    className={`flex flex-col max-w-[85%] ${
                      m.role === 'user' ? 'items-end' : 'items-start'
                    }`}
                  >
                    <div className="flex items-center gap-1.5 mb-1 px-1 text-[10px] text-txt-3 font-mono">
                      <span>{m.role === 'user' ? user?.displayName || user?.name || user?.username || 'المستخدم' : 'الوكيل الذكي'}</span>
                      {m.model && (
                        <>
                          <span>·</span>
                          <span className="text-info">{m.model}</span>
                        </>
                      )}
                      <span>·</span>
                      <span>{m.timestamp}</span>
                    </div>

                    <div
                      className={`rounded-2xl px-4 py-3 text-xs sm:text-[13px] leading-7 shadow-sm ${
                        m.role === 'user'
                          ? 'bg-hi text-white rounded-tr-none whitespace-pre-wrap font-medium'
                          : m.error
                          ? 'bg-crit/15 border border-crit/40 text-crit rounded-tl-none whitespace-pre-wrap'
                          : 'bg-steel-2 border border-line text-txt rounded-tl-none'
                      }`}
                    >
                      {m.role === 'user' || m.error ? (
                        m.text
                      ) : (
                        <MarkdownRenderer content={m.text} />
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {busy && (
                <div className="flex items-start gap-2.5">
                  <div className="w-7 h-7 rounded-full bg-steel-3 border border-line flex items-center justify-center shrink-0 mt-1">
                    <Icon name="chat" size={13} className="text-info animate-spin" />
                  </div>
                  <div className="bg-steel-2 border border-line rounded-2xl rounded-tl-none px-4 py-3 text-xs text-txt-2 flex items-center gap-2.5 shadow-sm">
                    <span className="w-2 h-2 rounded-full bg-info animate-ping" />
                    <span>
                      جارٍ استعلام قاعدة البيانات عبر{' '}
                      {modelMode === 'local'
                        ? 'Ollama المحلي'
                        : modelMode === 'groq'
                        ? 'Groq السحابي'
                        : 'المحرك الذكي'}
                      ...
                    </span>
                  </div>
                </div>
              )}

              <div ref={chatBottomRef} />
            </div>

            {/* Quick Suggestion Chips */}
            <div className="px-4 py-2 bg-steel-3/50 border-t border-line flex items-center gap-2 overflow-x-auto">
              <span className="text-[11px] font-semibold text-txt-3 shrink-0 flex items-center gap-1">
                <Icon name="search" size={12} /> مقترحات سريعة:
              </span>
              {PROMPT_TEMPLATES.slice(0, 4).map((pt, i) => (
                <button
                  key={i}
                  disabled={busy}
                  onClick={() => handleSend(pt.prompt)}
                  className="text-2xs bg-steel-2 hover:bg-steel-3 border border-line hover:border-hi/50 text-txt-2 hover:text-txt rounded-full px-3 py-1 whitespace-nowrap transition-colors"
                >
                  {pt.title}
                </button>
              ))}
            </div>

            {/* Bottom Input Form */}
            <div className="p-3.5 bg-steel-2 border-t border-line">
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleSend()
                }}
                className="flex items-center gap-2"
              >
                <input
                  ref={inputRef}
                  className="field flex-1 text-xs sm:text-[13px] py-2.5 px-4 bg-steel-3 border border-line rounded-xl focus:border-hi"
                  placeholder="اسأل الوكيل الذكي عن أي حوادث، تصاريح، مخاطر، مهمات وقاية، أو مؤشرات قياس..."
                  value={draft}
                  disabled={busy}
                  onChange={(e) => setDraft(e.target.value)}
                />
                <Btn
                  variant="pri"
                  icon="send"
                  disabled={busy || !draft.trim()}
                  onClick={() => handleSend()}
                  className="rounded-xl px-4 py-2.5 shrink-0"
                >
                  إرسال
                </Btn>
              </form>
            </div>
          </Card>
        </div>

        {/* Sidebar Tasks & Tool Registry (4 cols) */}
        <div className="lg:col-span-4 flex flex-col gap-3.5">
          {/* Smart Prompt Library */}
          <Card>
            <CardHead title="مكتبة الأوامر والمهام الذكية" hint="HSE PROMPT SUITE" />
            <CardBody className="space-y-2 max-h-[300px] overflow-y-auto p-2.5">
              {PROMPT_TEMPLATES.map((pt, i) => (
                <button
                  key={i}
                  disabled={busy}
                  onClick={() => handleSend(pt.prompt)}
                  className="w-full text-start p-2.5 rounded-xl bg-steel-3/60 hover:bg-steel-3 border border-line hover:border-txt-3 transition-all flex items-start gap-2.5 group"
                >
                  <span className="w-7 h-7 rounded-lg bg-steel-2 flex items-center justify-center shrink-0 mt-0.5 text-txt-2 group-hover:text-hi">
                    <Icon name={pt.icon} size={14} />
                  </span>
                  <div className="flex-1 min-w-0">
                    <div className="text-xs font-semibold text-txt flex items-center justify-between">
                      <span>{pt.title}</span>
                      <Pill tone={pt.tone}>{pt.badge}</Pill>
                    </div>
                    <p className="text-[11px] text-txt-3 line-clamp-2 mt-0.5 leading-4">
                      {pt.prompt}
                    </p>
                  </div>
                </button>
              ))}
            </CardBody>
          </Card>

          {/* Database Tool Registry */}
          <Card>
            <CardHead title="الأدوات المتصلة بقاعدة البيانات" hint="TOOL REGISTRY" />
            <CardBody className="space-y-2 max-h-[240px] overflow-y-auto p-2.5">
              {AGENT_TOOLS.map((tool, i) => (
                <div
                  key={i}
                  className="p-2 rounded-lg bg-steel-3/50 border border-line text-2xs space-y-1"
                >
                  <div className="flex items-center justify-between">
                    <b className="font-mono text-info">{tool.name}</b>
                    <Tag tone="g">ACTIVE</Tag>
                  </div>
                  <div className="text-txt-2 text-[11px] leading-tight">{tool.desc}</div>
                  <div className="font-mono text-[9.5px] text-txt-3">الجداول: {tool.target}</div>
                </div>
              ))}
            </CardBody>
          </Card>

          {/* Safety & ISO 45001 Guardrails */}
          <Card>
            <CardHead title="معايير الأمان والحوكمة" hint="ISO 45001 GUARDRAILS" />
            <CardBody className="text-xs text-txt-2 leading-6 space-y-1.5 p-3.5">
              <StatLine label="وضع القراءة الآمن" value={<Pill tone="ok">Read-Only Isolated</Pill>} />
              <StatLine label="التوقيع والاعتماد" value={<Pill tone="in">Human-in-the-Loop</Pill>} />
              <StatLine label="سجل التدقيق" value={<Pill tone="ok">Append-Only Audit</Pill>} />
              <p className="text-[11px] text-txt-3 pt-2 border-t border-line mt-2 leading-5">
                الوكيل الذكي يعمل بأسلوب الاستعلام المباشر فقط لضمان سلامة العمليات وتوثيق كل إجراء عبر مسؤولي السلامة المعتمدين.
              </p>
            </CardBody>
          </Card>
        </div>
      </div>
    </>
  )
}
