import { useState, useEffect, useRef, useCallback } from 'react'
import { Link } from 'react-router-dom'
import {
  Btn,
  Pill,
} from '../components/ui.jsx'
import Icon from '../components/Icon.jsx'
import { assistant } from '../api/endpoints.js'
import { useAuth, useToast } from '../hooks.jsx'
import { useTheme } from '../theme.jsx'
import { Wordmark } from '../components/layout.jsx'
import MarkdownRenderer from '../components/MarkdownRenderer.jsx'
import { ROLE_AR } from '../labels.js'
import { useVoiceAssistant } from '../useVoiceAssistant.js'
import VoiceSoundWave from '../components/VoiceSoundWave.jsx'

const PROMPT_TEMPLATES = [
  // ── 1. Dashboard & Metrics (لوحة القيادة) ──────────────────────────────
  {
    title: 'ملخص مؤشرات السلامة العامة (Dashboard)',
    category: 'لوحة القيادة',
    icon: 'dashboard',
    prompt: 'اعرض ملخص لوحة قيادة السلامة التنفيذية وساعات العمل الآمنة ومعدل الجاهزية ومعدلات الحوادث المفتوحة.',
    tone: 'safe',
    badge: 'Dashboard',
  },
  {
    title: 'معادلة ومؤشرات TRIR و LTIFR',
    category: 'مؤشرات الأداء',
    icon: 'reports',
    prompt: 'ما هي المعادلة المعتمدة لحساب مؤشرات TRIR و LTIFR والأيام المتبقية لنفاد مخزون المهمات (Days Until Stockout)؟',
    tone: 'safe',
    badge: 'KPIs',
  },

  // ── 2. Reports & ISO 45001 Analytics (التقارير والتحليلات) ─────────────
  {
    title: 'تصدير تقرير السلامة الشهري Excel',
    category: 'التقارير والتحليلات',
    icon: 'reports',
    prompt: 'قم بتصدير مصنف تقارير السلامة والامتثال لمواصفة ISO 45001 لشهر يوليو 2026 إلى ملف Excel.',
    tone: 'in',
    badge: 'Report Export',
  },
  {
    title: 'متطلبات بنود ISO 45001',
    category: 'الأيزو الدولية',
    icon: 'document',
    prompt: 'اشرح متطلبات البند 6 (Planning & HIRA) والبند 10 (CAPA) في المواصفة القياسية الدولية ISO 45001:2018.',
    tone: 'in',
    badge: 'ISO 45001',
  },

  // ── 3. Incidents & Reporting (الحوادث والبلاغات) ─────────────────────────
  {
    title: 'تسجيل بلاغ حادث فوري',
    category: 'الحوادث والبلاغات',
    icon: 'incident',
    prompt: 'سجل بلاغ حادث جديد: العنوان "تسريب زيت هيدروليكي"، الوصف "تسريب زيت في خط سحب الكابلات رقم 3 دون إصابات"، المنطقة 2، درجة الخطورة MODERATE، نوع الحادث UNSAFE_CONDITION.',
    tone: 'cr',
    badge: 'CRUD Incident',
  },
  {
    title: 'تحليل السبب الجذري RCA (5 Whys)',
    category: 'الحوادث والبلاغات',
    icon: 'incident',
    prompt: 'اعرض تحليل السبب الجذري RCA وملخص الأسباب الجذرية لحوادث الانسكابات الكيميائية في مصنع الكابلات.',
    tone: 'wn',
    badge: 'RCA Analysis',
  },

  // ── 4. Risk Assessment - HIRA (تقييم المخاطر) ───────────────────────────
  {
    title: 'تسجيل تقييم مخاطر HIRA جديد',
    category: 'تقييم المخاطر',
    icon: 'risk',
    prompt: 'سجل تقييم مخاطر جديد (HIRA) لنشاط "تغيير بكرات خط العزل CCV"، الخطر المحتمل "سقوط أحمال ثقيلة"، مستوى الخطر MEDIUM مع إجراءات التحكم الوقائية.',
    tone: 'wn',
    badge: 'HIRA Risk',
  },

  // ── 5. Work Permits - PTW (تصاريح العمل) ────────────────────────────────
  {
    title: 'إصدار تصريح عمل ساخن ePTW',
    category: 'تصاريح العمل',
    icon: 'permit',
    prompt: 'انشئ تصريح عمل إلكتروني جديد (Hot Work): لحام مسارات كابلات الجهد المتوسط في المنطقة 3، مدة 8 ساعات، مع فحص الغازات وإجراءات العزل.',
    tone: 'safe',
    badge: 'ePTW Permit',
  },
  {
    title: 'فحص تعارضات العمليات المتزامنة SIMOPS',
    category: 'تصاريح العمل',
    icon: 'permit',
    prompt: 'افحص تعارضات العمليات المتزامنة (SIMOPS) لجميع تصاريح العمل النشطة في منطقة الإنتاج رقم 2 واعرض تقرير الأمان.',
    tone: 'cr',
    badge: 'SIMOPS Check',
  },

  // ── 6. Job Safety Analysis - JSA (تحليل المهام) ──────────────────────────
  {
    title: 'إنشاء وثيقة تحليل سلامة المهام JSA',
    category: 'تحليل المهام',
    icon: 'jsa',
    prompt: 'انشئ وثيقة تحليل سلامة مهمة (JSA) لعملية "صيانة الرافعات العلوية وتغيير المحركات" في المنطقة 1 مع متطلبات تصريح العمل وإجراءات السلامة.',
    tone: 'in',
    badge: 'JSA Create',
  },

  // ── 7. Fire Safety Equipment (معدات الحريق) ─────────────────────────────
  {
    title: 'مطافئ الحريق المنتهية ومعدات الإطفاء',
    category: 'معدات الحريق',
    icon: 'fire',
    prompt: 'ما هي مطافئ الحريق ومعدات الإطفاء المنتهية الصلاحية أو التي تحتاج فحص دوري عاجل في جميع المناطق؟',
    tone: 'cr',
    badge: 'Fire Safety',
  },
  {
    title: 'أمر شغل صيانة لمعدة إطفاء',
    category: 'معدات الحريق',
    icon: 'fire',
    prompt: 'سجل أمر شغل صيانة وإعادة تعبئة وضغط هيدروستاتيكي لطفاية البودرة الجافة كود FE-001.',
    tone: 'in',
    badge: 'Fire Service',
  },

  // ── 8. PPE Management (معدات الوقاية) ───────────────────────────────────
  {
    title: 'رفع طلب توريد مهمات (Supply Order)',
    category: 'معدات الوقاية',
    icon: 'ppe',
    prompt: 'ارفع طلب توريد رسمي عاجل لجميع أصناف مهمات الوقاية الشخصية التي انخفض رصيدها عن حد إعادة الطلب لسد عجز المخزن وتغطية الاستهلاك الشهري.',
    tone: 'cr',
    badge: 'PPE Reorder',
  },
  {
    title: 'صرف مهمة وقاية شخصية PPE',
    category: 'معدات الوقاية',
    icon: 'ppe',
    prompt: 'سجل حركة صرف مهمة وقاية شخصية: صرف عدد 2 خوذة أمان عازلة للموظف أحمد سامي وتحديث رصيد المخزن آلياً.',
    tone: 'safe',
    badge: 'PPE Transaction',
  },

  // ── 9. Inspections & Patrols (التفتيش والجولات) ─────────────────────────
  {
    title: 'جدولة جولة تفتيش سلامة دورية',
    category: 'التفتيش والجولات',
    icon: 'inspection',
    prompt: 'جدول جولة تفتيش سلامة دورية جديدة لنظام LOTO والسلامة الكهربائية في عنبر 2 الأسبوع القادم.',
    tone: 'in',
    badge: 'CRUD Schedule',
  },
  {
    title: 'تسجيل جولة ميدانية واعتماد نتيجتها',
    category: 'التفتيش والجولات',
    icon: 'inspection',
    prompt: 'سجل جولة تفتيش ميدانية مكتملة في عنبر 1 بنسبة التزام 96% مع تسجيل ملاحظة عدم ارتداء نظارات واقية لعامل الصيانة.',
    tone: 'safe',
    badge: 'CRUD Walk',
  },

  // ── 10. Hazardous Materials (المواد الخطرة) ──────────────────────────────
  {
    title: 'فحص التوافق وصحائف سلامة المواد MSDS',
    category: 'المواد الخطرة',
    icon: 'hazmat',
    prompt: 'اعرض قائمة المواد الكيميائية الخطرة بالموقع وافحص التوافق الكيميائي لمادة Acetone مع باقي المواد المخزنة.',
    tone: 'wn',
    badge: 'HazMat MSDS',
  },

  // ── 11. Occupational Health (الصحة المهنية) ──────────────────────────────
  {
    title: 'توثيق فحص طبي دوري للموظفين',
    category: 'الصحة المهنية',
    icon: 'health',
    prompt: 'سجل نتيجة فحص طبي دوري (قياس السمع والوظائف الرئوية) للموظف رقم 2 بنتيجة FIT وتحديث السجل الصحي.',
    tone: 'safe',
    badge: 'Health Exam',
  },

  // ── 12. Training & Certification (التدريب والتأهيل) ──────────────────────
  {
    title: 'اعتماد وتجديد شهادة تدريبية',
    category: 'التدريب والتأهيل',
    icon: 'training',
    prompt: 'سجل اعتماد وتجديد شهادة تدريب السلامة الكيميائية المتقدمة للموظف أحمد سامي لمدة عام كامل وتحديث مصفوفة الكفاءة.',
    tone: 'safe',
    badge: 'Training Cert',
  },

  // ── 13. Automated Monitoring & IoT (المراقبة الآلية) ─────────────────────
  {
    title: 'حساسات الغازات وقراءات IoT المباشرة',
    category: 'المراقبة الآلية',
    icon: 'iot',
    prompt: 'اعرض أحدث تنبيهات حساسات الغازات والحرارة الذكية وقراءات كاميرات مراقبة مهمات الوقاية (AI Vision).',
    tone: 'cr',
    badge: 'IoT & Vision',
  },

  // ── 14. System Integration & APIs (الربط والتكامل) ───────────────────────
  {
    title: 'فحص حالة الربط والتكامل مع الأنظمة',
    category: 'الربط والتكامل',
    icon: 'integrations',
    prompt: 'اعرض حالة تكامل الأنظمة الخارجية (ERP, SAP, SCADA, Access Control) وتدقيق سجلات المزامنة.',
    tone: 'in',
    badge: 'Integrations',
  },

  // ── 15. Security & Audits (الأمن والتدقيق) ───────────────────────────────
  {
    title: 'تدقيق سجلات العمليات والأمان (Audit Log)',
    category: 'الأمن والتدقيق',
    icon: 'security',
    prompt: 'اعرض أحدث سجلات التدقيق غير القابلة للتعديل (Immutable Audit Log) لعمليات AI والتحقق من بصمات SHA-256.',
    tone: 'safe',
    badge: 'Audit Trail',
  },

  // ── 16. Reference Data & Zones (البيانات المرجعية والمناطق) ──────────────
  {
    title: 'استعلام الأقسام والمناطق وسجلات الموظفين',
    category: 'البيانات المرجعية',
    icon: 'departments',
    prompt: 'اعرض قائمة أقسام المصنع ومناطق العمل والمسؤولين المعينين لكل منطقة مع نسب الإشغال والامتثال.',
    tone: 'in',
    badge: 'Master Data',
  },
]

const AGENT_TOOLS = [
  { name: 'search_hse_knowledge', desc: 'استرجاع لوائح ISO 45001، معايير OSHA، وقواعد السويدي الذهبية', target: 'ISO 45001 / OSHA / ESCA SOPs', category: 'RAG' },
  { name: 'search_database_entities', desc: 'بحث ذكي شامل عبر الحوادث، التصاريح، المهمات، الموظفين، والمعدات', target: 'HSE Database Entities', category: 'RAG' },
  { name: 'list_incidents / create_incident', desc: 'تسجيل واستعلام ومتابعة سجلات الحوادث وتوليد نماذج الإبلاغ الخارجية', target: 'incidents, rca (CRUD)', category: 'CREATE' },
  { name: 'list_permits / create_permit', desc: 'إصدار واعتماد وتحديث تصاريح العمل الإلكترونية ePTW وفحص تعارضات SIMOPS', target: 'permits, simops (CRUD)', category: 'CREATE' },
  { name: 'schedule_safety_inspection', desc: 'جدولة جولات التفتيش والسلامة الميدانية وتوليد قوائم الفحص الذكية', target: 'inspections, checklists (CRUD)', category: 'CREATE' },
  { name: 'create_risk_assessment', desc: 'تسجيل وتحديث سجل تقييم المخاطر الميدانية ومصفوفة HIRA', target: 'risk_register (CRUD)', category: 'CREATE' },
  { name: 'create_jsa / update_jsa', desc: 'إنشاء وتوثيق وثائق تحليل سلامة المهام والأنشطة الحرجة', target: 'jsa_records (CRUD)', category: 'CREATE' },
  { name: 'get_expired_fire_equipment', desc: 'متابعة وفحص معدات الإطفاء وشبكة الحريق وأوامر شغل الصيانة', target: 'fire_equipment, fixed_assets (CRUD)', category: 'READ' },
  { name: 'create_ppe_supply_order', desc: 'رفع طلبات التوريد الآلية وإدارة حركات صرف ومخزون مهمات الوقاية', target: 'ppe_inventory, transactions (CRUD)', category: 'CREATE' },
  { name: 'add_chemical / list_chemicals', desc: 'إدارة سجل المواد الخطرة والتوافق الكيميائي وصحائف السلامة MSDS', target: 'chemicals_inventory (CRUD)', category: 'CREATE' },
  { name: 'record_medical_exam', desc: 'تسجيل الفحوصات الطبية الدورية ومتابعة التعرضات المهنية', target: 'medical_exams, hygiene (CRUD)', category: 'CREATE' },
  { name: 'create_certificate', desc: 'توثيق واعتماد شهادات التدريب والسلامة وتحديث مصفوفة الكفاءة', target: 'certificates, training_courses (CRUD)', category: 'CREATE' },
  { name: 'add_iot_sensor / log_ai_event', desc: 'ربط الحساسات الذكية وتسجيل أحداث كاميرات الذكاء الاصطناعي', target: 'iot_sensors, ai_events (CRUD)', category: 'CREATE' },
  { name: 'export_reports_excel / pdf', desc: 'تصدير وإرسال التقارير التنفيذية للإدارة وتفعيل الجدولة التلقائية', target: 'reports_engine, analytics (EXPORT)', category: 'ACTION' },
  { name: 'list_audit_logs / roles', desc: 'مراجعة سجلات التدقيق المشفرة وتوزيع الصلاحيات وأدوار النظام', target: 'audit_log, security_roles (AUDIT)', category: 'READ' },
  { name: 'delete_record / cancel_entity', desc: 'إلغاء التصاريح وحذف السجلات مع التوثيق الكامل في سجل التدقيق', target: 'audit_log + Railway DB (SUPERUSER)', category: 'DELETE' },
]

export default function AiAgent() {
  const { user } = useAuth()
  const toast = useToast()
  const { mode } = useTheme()
  const isWhiteLogo = mode !== 'light'
  const [modelMode, setModelMode] = useState('auto')
  const [copiedIndex, setCopiedIndex] = useState(null)
  
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      text: 'مرحباً بك! أنا **المساعد الذكي للسلامة والصحة المهنية (ESCA HSE AI Assistant)**.\n\nأنا متصل مباشرة بقاعدة بيانات مصانع السويدي للكابلات ومجهز بمحرك **RAG** لمعايير السلامة (ISO 45001, OSHA 1910, ESCA Golden Rules) وبصلاحيات **CRUD كاملة** لإنشاء وتحديث وإدارة السجلات وفقاً لنظام الصلاحيات وسجل التدقيق الآلي.\n\nكيف يمكنني خدمتك اليوم؟',
      tools: [],
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  
  const chatMessagesRef = useRef(null)
  const textareaRef = useRef(null)

  const [showVoiceLangMenu, setShowVoiceLangMenu] = useState(false)

  const voice = useVoiceAssistant({
    onTranscript: (t) => {
      if (t && t.trim()) {
        setDraft(t.trim())
      }
    },
    defaultLang: 'auto',
  })

  const activeUserRole =
    user?.role ||
    user?.role_name ||
    (user?.username === 'mostafa'
      ? 'HSE_MANAGER'
      : user?.username === 'admin'
      ? 'ADMIN'
      : user?.username === 'department.manager' || user?.username === 'esca.user03'
      ? 'PRODUCTION_SUPERVISOR'
      : 'WORKER')

  const displayUserRole =
    user?.roleAr ||
    user?.roleLabel ||
    user?.job_title ||
    user?.jobTitle ||
    ROLE_AR[activeUserRole] ||
    ROLE_AR[user?.role] ||
    activeUserRole

  // Dedicated container-only scroll to bottom without jumping the outer window
  const scrollToBottom = useCallback((behavior = 'smooth') => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTo({
        top: chatMessagesRef.current.scrollHeight,
        behavior,
      })
    }
  }, [])

  useEffect(() => {
    const raf = requestAnimationFrame(() => {
      scrollToBottom('smooth')
    })
    return () => cancelAnimationFrame(raf)
  }, [messages, busy, scrollToBottom])

  // Auto-expanding textarea height calculation
  useEffect(() => {
    const textarea = textareaRef.current
    if (!textarea) return
    textarea.style.height = 'auto'
    const minHeight = 44
    const maxHeight = 180
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
    textarea.style.height = `${nextHeight}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [draft])

  async function handleSend(customText) {
    const q = (customText ?? draft).trim()
    if (!q || busy) return

    setDraft('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '44px'
      textareaRef.current.style.overflowY = 'hidden'
    }

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

      const res = await assistant.ask(
        q,
        historyContext,
        modelMode,
        activeUserRole,
        user?.username || user?.employeeId || 'USR-DEV'
      )
      
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
      const cleanAnswer = cleanText || 'تم تنفيذ العملية بنجاح واستخراج البيانات المطلوبة من قاعدة البيانات.'
      const toolCalls = res.tool_calls || res.tools || []
      if (toolCalls.length > 0) {
        // Trigger live re-fetch for notifications, training matrix, and all page states
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
      }

      // Check specifically for certificate creation / update
      const certCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_certificate' ||
          t.name === 'create_certificate' ||
          t.name === 'create_training_certificate' ||
          t.tool === 'create_certificate' ||
          t.tool_name === 'update_certificate_status' ||
          t.name === 'update_certificate_status'
      )
      if (certCall) {
        const args = certCall.args || certCall.arguments || {}
        const result = certCall.result || certCall.output || {}
        const empName = args.employee_name || result.employee || result.employee_name || 'موظف'
        const courseName = args.course_name || result.course || result.course_name || 'دورة تدريبية'
        const isExp = result.status === 'EXPIRED' || result.is_expired || result.live_notification_triggered

        const notifObj = {
          id: 'NTF-' + (result.notification_id || Date.now()),
          notificationId: result.notification_id || Date.now(),
          title: isExp
            ? `تنبيه أتمتة السلامة: انتهاء صلاحية شهادة ${empName}`
            : `توثيق واعتماد شهادة تدريبية: ${empName}`,
          body: isExp
            ? `انتهت صلاحية شهادة تدريب الموظف ${empName} لدورة (${courseName}) — تم إطلاق تنبيه السلامة الآلي (AUT-002).`
            : `تم توثيق واعتماد شهادة تدريب (${courseName}) للموظف ${empName} بنجاح في مصفوفة الكفاءة وتحديث سجلات السلامة.`,
          time: 'الآن (مباشر)',
          color: isExp ? 'var(--crit)' : 'var(--safe)',
          type: isExp ? 'AUTOMATION_CERTIFICATE_EXPIRY' : 'TRAINING',
          to: '/training',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        if (isExp) {
          toast(`🚨 تنبيه فوري: انتهت صلاحية شهادة ${empName} وتم إطلاق إشعار السلامة الآلي!`, 'wn')
        } else {
          toast(`تم توثيق واعتماد شهادة ${empName} بنجاح في مصفوفة الكفاءة وتحديث الإشعارات`, 'ok')
        }
      }

      // Check specifically for permit creation / approval / status / delete / SIMOPS
      const permitCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_permit' ||
          t.name === 'create_permit' ||
          t.tool_name === 'update_permit_status' ||
          t.name === 'update_permit_status' ||
          t.tool_name === 'update_permit' ||
          t.name === 'update_permit' ||
          t.tool_name === 'delete_permit' ||
          t.name === 'delete_permit' ||
          t.tool_name === 'close_all_permits' ||
          t.name === 'close_all_permits' ||
          t.tool_name === 'delete_all_permits' ||
          t.name === 'delete_all_permits' ||
          t.tool_name === 'check_simops_conflicts' ||
          t.name === 'check_simops_conflicts'
      )
      if (permitCall) {
        const tName = permitCall.tool_name || permitCall.name || ''
        const result = permitCall.result || permitCall.output || {}
        const args = permitCall.args || permitCall.arguments || {}
        const isDelete = tName.includes('delete')
        const isSimops = tName.includes('simops')
        const pCode = result.permit_code || `PTW-${result.permit_id || args.permit_id || ''}`

        const notifObj = {
          id: 'NTF-PTW-' + (result.permit_id || Date.now()),
          notificationId: result.permit_id || Date.now(),
          title: isSimops
            ? `فحص تعارضات العمليات المتزامنة SIMOPS (${result.conflicts_count || 0} تعارض)`
            : isDelete
            ? `حذف / إلغاء تصريح العمل (${pCode})`
            : `تصريح عمل إلكتروني ePTW: ${pCode}`,
          body: result.message || 'تم تحديث سجل تصاريح العمل الإلكترونية ePTW وإدارة المخاطر بنجاح.',
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : isSimops ? 'var(--warn)' : 'var(--safe)',
          type: 'PERMIT',
          to: '/permits',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث تصاريح العمل الإلكترونية ePTW بنجاح', 'ok')
      }

      // Check specifically for inspections & findings
      const inspCall = toolCalls.find(
        (t) =>
          t.tool_name === 'schedule_safety_inspection' ||
          t.name === 'schedule_safety_inspection' ||
          t.tool_name === 'submit_inspection_walk' ||
          t.name === 'submit_inspection_walk' ||
          t.tool_name === 'create_inspection_finding' ||
          t.name === 'create_inspection_finding' ||
          t.tool_name === 'update_inspection_status' ||
          t.name === 'update_inspection_status' ||
          t.tool_name === 'update_inspection' ||
          t.name === 'update_inspection' ||
          t.tool_name === 'delete_inspection' ||
          t.name === 'delete_inspection' ||
          t.tool_name === 'update_inspection_finding' ||
          t.name === 'update_inspection_finding' ||
          t.tool_name === 'delete_inspection_finding' ||
          t.name === 'delete_inspection_finding'
      )
      if (inspCall) {
        const tName = inspCall.tool_name || inspCall.name || ''
        const args = inspCall.args || inspCall.arguments || {}
        const result = inspCall.result || inspCall.output || {}
        const isDelete = tName.includes('delete')
        const isFinding = tName.includes('finding')

        const notifObj = {
          id: 'NTF-INSP-' + (result.inspection_id || result.finding_id || Date.now()),
          notificationId: result.inspection_id || result.finding_id || Date.now(),
          title: isDelete
            ? `حذف سجل #${result.inspection_id || result.finding_id || args.inspection_id || ''}`
            : isFinding
            ? `ملاحظات التفتيش وعدم المطابقة (${args.category || result.category || 'ميدانية'})`
            : `جولات التفتيش: ${args.inspection_type || result.inspection_type || 'جولة سلامة'}`,
          body: result.message || `تم تنفيذ العملية بنجاح وتحديث لوحة جولات السلامة والتفتيش.`,
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : isFinding ? 'var(--warn)' : 'var(--safe)',
          type: 'INSPECTION',
          to: '/inspections',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث سجلات التفتيش والجولات بنجاح', 'ok')
      }

      // Check specifically for PPE & Safety Equipment
      const ppeCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_ppe_supply_order' ||
          t.name === 'create_ppe_supply_order' ||
          t.tool_name === 'create_ppe_transaction' ||
          t.name === 'create_ppe_transaction' ||
          t.tool_name === 'delete_ppe_transaction' ||
          t.name === 'delete_ppe_transaction' ||
          t.tool_name === 'add_ppe_item' ||
          t.name === 'add_ppe_item' ||
          t.tool_name === 'update_ppe_item' ||
          t.name === 'update_ppe_item' ||
          t.tool_name === 'delete_ppe_item' ||
          t.name === 'delete_ppe_item' ||
          t.tool_name === 'update_ppe_stock' ||
          t.name === 'update_ppe_stock' ||
          t.tool_name === 'record_fixed_safety_asset_inspection' ||
          t.name === 'record_fixed_safety_asset_inspection'
      )
      if (ppeCall) {
        const tName = ppeCall.tool_name || ppeCall.name || ''
        const result = ppeCall.result || ppeCall.output || {}
        const args = ppeCall.args || ppeCall.arguments || {}
        const isOrder = tName.includes('supply_order')
        const isTx = tName.includes('transaction')
        const isFixed = tName.includes('fixed_safety')

        const notifObj = {
          id: 'NTF-PPE-' + (result.transaction_id || result.order_reference || result.ppe_item_id || Date.now()),
          notificationId: result.transaction_id || result.ppe_item_id || Date.now(),
          title: isOrder
            ? `طلب توريد مهمات الوقاية (${result.order_reference || 'PO-PPE'})`
            : isTx
            ? `حركة مهمات الوقاية: ${result.transaction_type_ar || 'صرف / إرجاع'}`
            : isFixed
            ? `فحص معدات السلامة: ${result.asset_name || 'معدة سلامة ثابتة'}`
            : `تحديث مخزون الوقاية: ${result.item_code || result.name_ar || 'صنف مهمة'}`,
          body: result.message || 'تم تحديث سجلات مهمات الوقاية الشخصية ومخزون السلامة بنجاح.',
          time: 'الآن (مباشر)',
          color: isOrder ? 'var(--info)' : 'var(--safe)',
          type: 'PPE',
          to: '/ppe',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث مهمات الوقاية ومخزون السلامة بنجاح', 'ok')
      }

      // Check specifically for Risk Assessment (HIRA)
      const riskCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_risk_assessment' ||
          t.name === 'create_risk_assessment' ||
          t.tool_name === 'update_risk_assessment' ||
          t.name === 'update_risk_assessment'
      )
      if (riskCall) {
        const result = riskCall.result || riskCall.output || {}
        const args = riskCall.args || riskCall.arguments || {}
        const notifObj = {
          id: 'NTF-RISK-' + (result.risk_id || Date.now()),
          notificationId: result.risk_id || Date.now(),
          title: `تقييم المخاطر الميدانية (HIRA #${result.risk_id || ''})`,
          body: result.message || `تم تسجيل تقييم الخطر (${result.hazard || args.hazard || 'مخاطر تشغيلية'}) وتحديث مصفوفة المخاطر.`,
          time: 'الآن (مباشر)',
          color: result.risk_level === 'HIGH' || result.risk_level === 'CRITICAL' ? 'var(--crit)' : 'var(--warn)',
          type: 'RISK_ASSESSMENT',
          to: '/risk',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث سجل تقييم المخاطر بنجاح', 'ok')
      }

      // Check specifically for Job Safety Analysis (JSA)
      const jsaCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_jsa' ||
          t.name === 'create_jsa' ||
          t.tool_name === 'update_jsa' ||
          t.name === 'update_jsa'
      )
      if (jsaCall) {
        const result = jsaCall.result || jsaCall.output || {}
        const args = jsaCall.args || jsaCall.arguments || {}
        const notifObj = {
          id: 'NTF-JSA-' + (result.jsa_id || Date.now()),
          notificationId: result.jsa_id || Date.now(),
          title: `تحليل سلامة المهام (JSA #${result.jsa_id || ''})`,
          body: result.message || `تم اعتماد وثيقة تحليل سلامة المهمة (${result.task_name || args.task_name || 'مهمة عمل'}) بنجاح.`,
          time: 'الآن (مباشر)',
          color: 'var(--safe)',
          type: 'JSA',
          to: '/jsa',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث وثيقة تحليل سلامة المهمة بنجاح', 'ok')
      }

      // Check specifically for HazMat / Chemicals
      const hazmatCall = toolCalls.find(
        (t) =>
          t.tool_name === 'add_chemical' ||
          t.name === 'add_chemical' ||
          t.tool_name === 'update_chemical' ||
          t.name === 'update_chemical' ||
          t.tool_name === 'update_chemical_stock' ||
          t.name === 'update_chemical_stock'
      )
      if (hazmatCall) {
        const result = hazmatCall.result || hazmatCall.output || {}
        const args = hazmatCall.args || hazmatCall.arguments || {}
        const notifObj = {
          id: 'NTF-HAZ-' + (result.chemical_id || Date.now()),
          notificationId: result.chemical_id || Date.now(),
          title: `سجل المواد الكيميائية والخطرة: ${result.trade_name || args.trade_name || 'مادة كيميائية'}`,
          body: result.message || 'تم تحديث بيانات صحيفة السلامة (MSDS) والتوافق الكيميائي للمادة بنجاح.',
          time: 'الآن (مباشر)',
          color: 'var(--warn)',
          type: 'HAZMAT',
          to: '/hazmat',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث سجل المواد الخطرة بنجاح', 'ok')
      }

      // Check specifically for Occupational Health / Medical Exam
      const healthCall = toolCalls.find(
        (t) =>
          t.tool_name === 'record_medical_exam' ||
          t.name === 'record_medical_exam' ||
          t.tool_name === 'schedule_medical_exam' ||
          t.name === 'schedule_medical_exam' ||
          t.tool_name === 'update_medical_exam' ||
          t.name === 'update_medical_exam'
      )
      if (healthCall) {
        const result = healthCall.result || healthCall.output || {}
        const args = healthCall.args || healthCall.arguments || {}
        const notifObj = {
          id: 'NTF-HLT-' + (result.exam_id || Date.now()),
          notificationId: result.exam_id || Date.now(),
          title: `الصحة المهنية والفحص الطبي: ${result.employee_name || args.employee_name || 'موظف'}`,
          body: result.message || 'تم توثيق نتيجة الفحص الطبي وتحديث سجل الكفاءة والملائمة الصحية.',
          time: 'الآن (مباشر)',
          color: result.fitness_result === 'UNFIT' ? 'var(--crit)' : 'var(--safe)',
          type: 'OCCUPATIONAL_HEALTH',
          to: '/occupational-health',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم توثيق بيانات الفحص الطبي بنجاح', 'ok')
      }

      // Check specifically for AI Vision & IoT Monitoring
      const iotCall = toolCalls.find(
        (t) =>
          t.tool_name === 'add_iot_sensor' ||
          t.name === 'add_iot_sensor' ||
          t.tool_name === 'update_iot_sensor' ||
          t.name === 'update_iot_sensor' ||
          t.tool_name === 'log_ai_event' ||
          t.name === 'log_ai_event'
      )
      if (iotCall) {
        const result = iotCall.result || iotCall.output || {}
        const args = iotCall.args || iotCall.arguments || {}
        const notifObj = {
          id: 'NTF-IOT-' + (result.sensor_id || result.event_id || Date.now()),
          notificationId: result.sensor_id || result.event_id || Date.now(),
          title: `المراقبة الآلية والحساسات البيئية (${result.sensor_tag || args.sensor_tag || 'حساس ذكي'})`,
          body: result.message || 'تم تسجيل بيانات الحساس الذكي وتحديث منظومة المراقبة الآلية الحية.',
          time: 'الآن (مباشر)',
          color: 'var(--info)',
          type: 'IOT_MONITORING',
          to: '/ai-iot',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث منظومة المراقبة الآلية والحساسات', 'ok')
      }

      // Check specifically for CAPA
      const capaCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_capa' ||
          t.name === 'create_capa' ||
          t.tool_name === 'update_capa_status' ||
          t.name === 'update_capa_status'
      )
      if (capaCall) {
        const result = capaCall.result || capaCall.output || {}
        const args = capaCall.args || capaCall.arguments || {}
        const notifObj = {
          id: 'NTF-CAPA-' + (result.capa_id || Date.now()),
          notificationId: result.capa_id || Date.now(),
          title: `إجراء تصحيحي ووقائي (CAPA #${result.capa_id || ''})`,
          body: result.message || `تم تحديث خطة الإجراءات التصحيحية (${result.title || args.title || 'إجراء سلامة'}).`,
          time: 'الآن (مباشر)',
          color: 'var(--warn)',
          type: 'CAPA',
          to: '/reports',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تحديث سجل الإجراءات التصحيحية CAPA', 'ok')
      }

      // Check specifically for Master Data / Employee / Superuser
      const masterCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_employee' ||
          t.name === 'create_employee' ||
          t.tool_name === 'update_employee' ||
          t.name === 'update_employee' ||
          t.tool_name === 'delete_record' ||
          t.name === 'delete_record' ||
          t.tool_name === 'cancel_entity' ||
          t.name === 'cancel_entity' ||
          t.tool_name === 'execute_database_dml' ||
          t.name === 'execute_database_dml'
      )
      if (masterCall) {
        const tName = masterCall.tool_name || masterCall.name || ''
        const result = masterCall.result || masterCall.output || {}
        const args = masterCall.args || masterCall.arguments || {}
        const isDelete = tName.includes('delete') || tName.includes('cancel')
        const notifObj = {
          id: 'NTF-ADM-' + Date.now(),
          notificationId: Date.now(),
          title: isDelete
            ? `إجراء إداري: حذف / إلغاء سجل (${args.table_name || args.entity_type || 'قاعدة البيانات'})`
            : `البيانات المرجعية والموظفين: ${result.display_name || args.display_name || 'تحديث البيانات'}`,
          body: result.message || 'تم تحديث البيانات المركزية وقيد العملية في سجل التدقيق غير القابل للتعديل.',
          time: 'الآن (مباشر)',
          color: isDelete ? 'var(--crit)' : 'var(--safe)',
          type: 'MASTER_DATA',
          to: '/departments',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تنفيذ الإجراء الإداري وتحديث البيانات', 'ok')
      }

      // Check specifically for fire equipment actions (inspections, service, add, update)
      const fireCall = toolCalls.find(
        (t) =>
          t.tool_name === 'log_fire_inspection' ||
          t.name === 'log_fire_inspection' ||
          t.tool_name === 'service_fire_equipment' ||
          t.name === 'service_fire_equipment' ||
          t.tool_name === 'add_fire_equipment' ||
          t.name === 'add_fire_equipment' ||
          t.tool_name === 'update_fire_equipment' ||
          t.name === 'update_fire_equipment'
      )
      if (fireCall) {
        const result = fireCall.result || fireCall.output || {}
        const args = fireCall.args || fireCall.arguments || {}
        const tName = fireCall.tool_name || fireCall.name || ''
        const isService = tName.includes('service')
        const tag = result.equipment_tag || args.equipment_tag || `FE-${args.equipment_id || ''}`

        const notifObj = {
          id: 'NTF-FIRE-' + (result.inspection_id || result.work_order_id || Date.now()),
          notificationId: result.inspection_id || Date.now(),
          title: isService
            ? `أمر شغل صيانة إطفاء (${result.work_order_id || 'WO-FIRE'}): ${tag}`
            : `فحص وتفتيش معدة الإطفاء: ${tag}`,
          body: result.message || 'تم تحديث سجلات معدات وشبكة الإطفاء ومكافحة الحريق بنجاح.',
          time: 'الآن (مباشر)',
          color: 'var(--safe)',
          type: 'FIRE_SAFETY',
          to: '/fire-equipment',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || `تم تنفيذ عملية معدة الإطفاء (${tag}) بنجاح`, 'ok')
      }

      // Check if Incident / RCA / Export / Template / Dashboard action was executed
      const incCall = toolCalls.find(
        (t) =>
          t.tool_name === 'export_incidents_excel' ||
          t.name === 'export_incidents_excel' ||
          t.tool_name === 'generate_external_report_template' ||
          t.name === 'generate_external_report_template' ||
          t.tool_name === 'create_incident_rca' ||
          t.name === 'create_incident_rca' ||
          t.tool_name === 'create_incident' ||
          t.name === 'create_incident' ||
          t.tool_name === 'refresh_dashboard' ||
          t.name === 'refresh_dashboard'
      )
      if (incCall) {
        const tName = incCall.tool_name || incCall.name || ''
        const result = incCall.result || incCall.output || {}
        const isExport = tName.includes('export')
        const isTmpl = tName.includes('template')
        const isRca = tName.includes('rca')
        const isDash = tName.includes('dashboard')

        if (isExport) {
          window.dispatchEvent(new CustomEvent('hse:export-incidents', { detail: { rows: result.rows, summary: result.summary } }))
        }
        if (isTmpl) {
          window.dispatchEvent(new CustomEvent('hse:open-template-modal', { detail: { templateType: result.template_type, data: result } }))
        }
        if (isDash) {
          window.dispatchEvent(new CustomEvent('hse:refresh-dashboard'))
        }

        const notifObj = {
          id: 'NTF-INC-' + (result.incident_id || result.rca_id || Date.now()),
          notificationId: result.incident_id || result.rca_id || Date.now(),
          title: isExport
            ? 'تصدير سجل الحوادث إلى ملف Excel'
            : isTmpl
            ? `توليد ${result.title || 'النموذج الرسمي'}`
            : isRca
            ? `تحليل السبب الجذري للحادث #${result.incident_id || 'INC'}`
            : isDash
            ? 'تحديث لوحة قيادة السلامة الحية'
            : `تسجيل بلاغ حادث جديد (${result.incident_id || 'INC'})`,
          body: result.message || 'تم تنفيذ العملية وتحديث سجلات السلامة بنجاح.',
          time: 'الآن (مباشر)',
          color: isExport ? 'var(--info)' : isDash ? 'var(--info)' : isRca ? 'var(--warn)' : 'var(--safe)',
          type: isDash ? 'DASHBOARD' : 'INCIDENT',
          to: isDash ? '/' : '/incidents',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(result.message || 'تم تنفيذ عملية السلامة بنجاح', 'ok')
      }

      // Check if Reports & Analytics action was executed
      const reportCall = toolCalls.find(
        (t) =>
          t.tool_name === 'export_reports_excel' ||
          t.name === 'export_reports_excel' ||
          t.tool_name === 'export_reports_pdf' ||
          t.name === 'export_reports_pdf' ||
          t.tool_name === 'send_report_to_management' ||
          t.name === 'send_report_to_management' ||
          t.tool_name === 'generate_custom_report' ||
          t.name === 'generate_custom_report' ||
          t.tool_name === 'open_ready_report' ||
          t.name === 'open_ready_report' ||
          t.tool_name === 'schedule_report' ||
          t.name === 'schedule_report'
      )
      if (reportCall) {
        const tName = reportCall.tool_name || reportCall.name || ''
        const result = reportCall.result || reportCall.output || {}
        const args = reportCall.args || reportCall.arguments || {}

        const isExcel = tName === 'export_reports_excel'
        const isPdf = tName === 'export_reports_pdf'
        const isSend = tName === 'send_report_to_management'
        const isCustom = tName === 'generate_custom_report'
        const isReady = tName === 'open_ready_report'
        const isSched = tName === 'schedule_report'

        if (isExcel) {
          window.dispatchEvent(new CustomEvent('hse:export-reports-excel', { detail: result }))
        }
        if (isPdf) {
          window.dispatchEvent(new CustomEvent('hse:export-reports-pdf', { detail: result }))
        }
        if (isSend) {
          window.dispatchEvent(new CustomEvent('hse:send-management', { detail: { ...args, ...result, autoSubmit: true } }))
        }
        if (isCustom) {
          window.dispatchEvent(new CustomEvent('hse:open-custom-report-builder', { detail: result }))
        }
        if (isReady) {
          window.dispatchEvent(new CustomEvent('hse:open-ready-report', { detail: { reportId: result.report_id || args.report_id } }))
        }
        if (isSched) {
          window.dispatchEvent(new CustomEvent('hse:schedule-report', { detail: result }))
        }
        window.dispatchEvent(new CustomEvent('hse:data-changed'))

        const notifObj = {
          id: 'NTF-RPT-' + (result.dispatch_id || result.schedule_id || Date.now()),
          notificationId: result.dispatch_id || Date.now(),
          title: isExcel
            ? 'تصدير مصنف تقارير السلامة Excel'
            : isPdf
            ? 'تصدير / طباعة التقرير التنفيذي PDF'
            : isSend
            ? `إرسال ${result.report_type || 'التقرير التنفيذي'} للإدارة`
            : isCustom
            ? `توليد ${result.title || 'تقرير مخصص'}`
            : isReady
            ? `فحص ${result.title || 'التقرير الجاهز'}`
            : 'تفعيل جدولة تقرير السلامة الآلي',
          body: result.message || 'تمت أتمتة إجراء التقارير بنجاح وتحديث لوحة التحليلات.',
          time: 'الآن (مباشر)',
          color: isSend ? 'var(--pri)' : isPdf ? 'var(--info)' : isExcel ? 'var(--safe)' : 'var(--warn)',
          type: 'REPORTS_ANALYTICS',
          to: '/reports',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        toast(result.message || 'تمت أتمتة إجراء التقارير بنجاح', 'ok')
      }

      const msgId = 'msg-' + Date.now()
      const agentMsg = {
        id: msgId,
        role: 'agent',
        text: cleanAnswer,
        tools: res.tool_calls || res.tools || [],
        model: res.model_used || (modelMode === 'local' ? 'Local Ollama' : 'Groq Online'),
        timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
      }

      setMessages((prev) => [...prev, agentMsg])

      if (voice.autoSpeak) {
        voice.speak(cleanAnswer, msgId)
      }
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
      setTimeout(() => textareaRef.current?.focus(), 50)
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      if (e.nativeEvent?.isComposing) return
      e.preventDefault()
      if (!busy && draft.trim()) {
        handleSend()
      }
    }
  }

  function handleClearChat() {
    setMessages([
      {
        role: 'agent',
        text: 'تمت إعادة تهيئة جلسة المحادثة. يمكنك بدء استعلام جديد أو طلب تنفيذ عمليات على قاعدة البيانات.',
        tools: [],
        timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
      },
    ])
    toast('تم مسح سجل المحادثة الحالية', 'in')
    if (textareaRef.current) {
      textareaRef.current.focus()
    }
  }

  const copyToClipboard = async (text, index) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedIndex(index)
      toast('تم نسخ النص إلى الحافظة', 'safe')
      setTimeout(() => setCopiedIndex(null), 2000)
    } catch {
      toast('تعذّر نسخ النص', 'cr')
    }
  }

  const isFreshState = messages.length <= 1

  return (
    <div className="flex flex-col w-full max-w-5xl mx-auto min-h-[calc(100vh-10rem)] animate-fade pb-2">
      {/* ── 1. Hero / Header Section Featuring Company Logo ────────────────── */}
      <header className="flex flex-col items-center justify-center text-center pt-2 pb-5 px-4 select-none">
        <div className="flex items-center justify-center mb-2">
          <Wordmark height={48} centered={true} isWhite={isWhiteLogo} />
        </div>
        <h1 className="text-sm sm:text-base font-semibold tracking-wide text-txt-2">
          Your Helpful AI Assistant
        </h1>
        <p className="text-[11px] sm:text-xs text-txt-3 mt-0.5">
          المساعد الذكي لمنظومة السلامة والصحة المهنية (ESCA HSE) · معايير ISO 45001 & OSHA
        </p>

        {/* Status Indicators & Control Bar */}
        <div className="mt-3.5 flex items-center justify-center gap-2 sm:gap-3 flex-wrap">
          {/* Model Switcher Segmented Control */}
          <div className="flex items-center gap-1 bg-steel-2/90 p-1 rounded-xl border border-line shadow-sm">
            <button
              type="button"
              onClick={() => {
                setModelMode('groq')
                toast('تم التبديل إلى نموذج Groq السحابي (Cloud Online)', 'in')
              }}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                modelMode === 'groq'
                  ? 'bg-hi text-white shadow-md'
                  : 'text-txt-2 hover:text-txt hover:bg-steel-3'
              }`}
            >
              <Icon name="cloud" size={13} />
              <span>Groq Online</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setModelMode('local')
                toast('تم التبديل إلى نموذج Ollama المحلي (On-Premise)', 'in')
              }}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                modelMode === 'local'
                  ? 'bg-safe text-white shadow-md'
                  : 'text-txt-2 hover:text-txt hover:bg-steel-3'
              }`}
            >
              <Icon name="server" size={13} />
              <span>Ollama Local</span>
            </button>

            <button
              type="button"
              onClick={() => {
                setModelMode('auto')
                toast('تم تفعيل التبديل التلقائي الذكي (Auto Hybrid)', 'in')
              }}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                modelMode === 'auto'
                  ? 'bg-steel-3 text-txt border border-line shadow-sm'
                  : 'text-txt-2 hover:text-txt hover:bg-steel-3'
              }`}
            >
              <Icon name="bolt" size={13} />
              <span>تلقائي (Auto)</span>
            </button>
            {/* Voice Auto-Speak Toggle */}
            <button
              type="button"
              onClick={voice.toggleAutoSpeak}
              title={voice.autoSpeak ? 'القراءة الصوتية التلقائية مفعلة (انقر للتعطيل)' : 'تفعيل القراءة الصوتية التلقائية'}
              className={`px-2.5 sm:px-3 py-1.5 rounded-lg text-xs font-semibold flex items-center gap-1.5 transition-all ${
                voice.autoSpeak
                  ? 'bg-safe/20 text-safe border border-safe/40 shadow-sm'
                  : 'text-txt-2 hover:text-txt hover:bg-steel-3 border border-transparent'
              }`}
            >
              <Icon name={voice.autoSpeak ? 'volume' : 'volume-off'} size={13} />
              <span>{voice.autoSpeak ? 'الصوت التلقائي (مفعل)' : 'الصوت التلقائي'}</span>
              {voice.isSpeaking && <VoiceSoundWave isSpeaking={true} size="sm" />}
            </button>
          </div>

          {/* New Chat Button */}
          <Btn
            icon="refresh"
            onClick={handleClearChat}
            className="rounded-xl px-3 py-1.5 text-xs text-txt-2 hover:text-txt bg-steel-2 hover:bg-steel-3 border border-line"
          >
            محادثة جديدة
          </Btn>
        </div>
      </header>

      {/* ── 2. Main Chat Shell (Centered Stream Layout) ────────────────────── */}
      <div className="flex-1 flex flex-col rounded-3xl border border-line bg-steel-2/70 backdrop-blur-xl shadow-2xl overflow-hidden relative min-h-[520px]">
        {/* Chat Feed Scroll Area */}
        <div
          ref={chatMessagesRef}
          className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-6 scroll-smooth"
        >
          {/* Welcome / Starter Cards for Fresh Session */}
          {isFreshState && (
            <div className="max-w-3xl mx-auto my-2 space-y-4 animate-fade">
              <div className="p-4 sm:p-5 rounded-2xl bg-steel-3/40 border border-line/80 text-start space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-txt">
                  <span className="w-6 h-6 rounded-lg bg-hi/15 text-hi flex items-center justify-center">
                    <Icon name="bolt" size={13} />
                  </span>
                  <span>أهلاً بك في المساعد الذكي لمصانع السويدي للكابلات</span>
                </div>
                <p className="text-xs text-txt-2 leading-relaxed">
                  يمكنك الاستفسار عن معايير الأمان، استعراض الحوادث وتصاريح العمل والمهمات، أو طلب إنشاء وتعديل السجلات مباشرة بصلاحياتك المعتمدة. إليك نماذج جاهزة للبدء:
                </p>
              </div>

              {/* Quick Starter Prompt Cards */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {PROMPT_TEMPLATES.slice(0, 6).map((pt, idx) => (
                  <button
                    key={idx}
                    type="button"
                    disabled={busy}
                    onClick={() => handleSend(pt.prompt)}
                    className="p-3.5 rounded-2xl bg-steel-3/60 hover:bg-steel-3 border border-line hover:border-hi/50 text-start transition-all duration-200 group flex items-start gap-3 active:scale-[0.99]"
                  >
                    <span className="w-8 h-8 rounded-xl bg-steel-2 flex items-center justify-center shrink-0 text-txt-2 group-hover:text-hi transition-colors mt-0.5 shadow-sm">
                      <Icon name={pt.icon} size={15} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between gap-1 mb-1">
                        <span className="text-xs font-semibold text-txt group-hover:text-hi transition-colors">
                          {pt.title}
                        </span>
                        <span className="text-[10px] font-mono font-medium text-txt-3 px-1.5 py-0.5 rounded bg-steel-2 border border-line/60">
                          {pt.badge}
                        </span>
                      </div>
                      <p className="text-[11px] text-txt-3 line-clamp-2 leading-tight">
                        {pt.prompt}
                      </p>
                    </div>
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Active Conversation Messages */}
          <div className="max-w-3xl mx-auto space-y-6">
            {messages.map((m, i) => {
              const isUser = m.role === 'user'
              return (
                <div
                  key={i}
                  className={`flex items-start gap-3 sm:gap-3.5 ${
                    isUser ? 'flex-row-reverse' : 'flex-row'
                  } group animate-fade`}
                >
                  {/* User / Agent Avatar */}
                  <div
                    className={`w-8 h-8 sm:w-9 sm:h-9 rounded-2xl flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 shadow-md ${
                      isUser
                        ? 'bg-gradient-to-tr from-hi to-hi2 text-white'
                        : 'bg-steel-3 border border-line text-txt'
                    }`}
                  >
                    {isUser ? (
                      user?.initials || (user?.displayName || user?.name || user?.username || 'U')[0]
                    ) : (
                      <span className="text-safe flex items-center justify-center">
                        <Icon name="chat" size={16} />
                      </span>
                    )}
                  </div>

                  {/* Message Content Container */}
                  <div
                    className={`flex flex-col max-w-[86%] sm:max-w-[80%] ${
                      isUser ? 'items-end' : 'items-start'
                    }`}
                  >
                    {/* Meta info */}
                    <div className="flex items-center gap-1.5 mb-1 px-1 text-[10.5px] text-txt-3 font-mono">
                      <span>{isUser ? user?.displayName || user?.name || user?.username || 'أنت' : 'ESCA AI Assistant'}</span>
                      {m.model && (
                        <>
                          <span>·</span>
                          <span className="text-info font-medium">{m.model}</span>
                        </>
                      )}
                      <span>·</span>
                      <span>{m.timestamp}</span>
                    </div>

                    {/* Message Bubble */}
                    <div
                      className={`rounded-2xl px-4 py-3 sm:px-5 sm:py-3.5 text-xs sm:text-[13px] leading-relaxed shadow-sm transition-all relative ${
                        isUser
                          ? 'bg-hi text-white rounded-tr-none whitespace-pre-wrap font-medium shadow-hi/10'
                          : m.error
                          ? 'bg-crit/10 border border-crit/40 text-crit rounded-tl-none whitespace-pre-wrap'
                          : 'bg-steel-3/90 border border-line text-txt rounded-tl-none'
                      }`}
                    >
                      {isUser || m.error ? (
                        m.text
                      ) : (
                        <MarkdownRenderer content={m.text} />
                      )}

                      {/* Tool Calls Execution Badge */}
                      {!isUser && m.tools && m.tools.length > 0 && (
                        <div className="mt-3 pt-2.5 border-t border-line/60 flex items-center gap-1.5 flex-wrap">
                          <span className="text-[10px] font-mono text-txt-3">العمليات المنفذة:</span>
                          {m.tools.map((t, tidx) => (
                            <span
                              key={tidx}
                              className="text-[10px] font-mono px-2 py-0.5 rounded-md bg-steel-2 text-info border border-line"
                            >
                              {t.name || t.tool || 'database_op'}
                            </span>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Message Actions (Copy & Read Aloud) */}
                    {!isUser && !m.error && (
                      <div className="flex items-center gap-2 mt-1.5 px-1">
                        <button
                          type="button"
                          onClick={() => copyToClipboard(m.text, i)}
                          className="inline-flex items-center gap-1 text-[10.5px] text-txt-3 hover:text-txt hover:bg-steel-3 px-2 py-0.5 rounded-md transition-colors"
                          title="نسخ الإجابة"
                        >
                          <Icon name={copiedIndex === i ? 'check' : 'document'} size={12} />
                          <span>{copiedIndex === i ? 'تم النسخ' : 'نسخ'}</span>
                        </button>
                        <button
                          type="button"
                          onClick={() => voice.speak(m.text, m.id || i)}
                          className={`inline-flex items-center gap-1 text-[10.5px] px-2 py-0.5 rounded-md transition-colors ${
                            voice.activeSpeakingId === (m.id || i) && voice.isSpeaking
                              ? 'bg-safe/15 text-safe font-semibold'
                              : 'text-txt-3 hover:text-hi hover:bg-steel-3'
                          }`}
                          title={voice.activeSpeakingId === (m.id || i) && voice.isSpeaking ? 'إيقاف الصوت' : 'استمع للإجابة'}
                        >
                          <Icon name={voice.activeSpeakingId === (m.id || i) && voice.isSpeaking ? 'stop' : 'volume'} size={12} />
                          <span>{voice.activeSpeakingId === (m.id || i) && voice.isSpeaking ? 'إيقاف' : 'استمع'}</span>
                          {voice.activeSpeakingId === (m.id || i) && voice.isSpeaking && (
                            <VoiceSoundWave isSpeaking={true} size="sm" />
                          )}
                        </button>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}

            {/* Thinking / Busy Indicator */}
            {busy && (
              <div className="flex items-start gap-3 sm:gap-3.5 animate-fade">
                <div className="w-8 h-8 sm:w-9 sm:h-9 rounded-2xl bg-steel-3 border border-line flex items-center justify-center shrink-0 mt-0.5 shadow-md">
                  <Icon name="chat" size={15} className="text-info animate-spin" />
                </div>
                <div className="bg-steel-3/90 border border-line rounded-2xl rounded-tl-none px-4 py-3 sm:px-5 sm:py-3.5 text-xs text-txt-2 flex items-center gap-3 shadow-sm">
                  <span className="w-2.5 h-2.5 rounded-full bg-info animate-ping" />
                  <span>
                    جارٍ استعلام قاعدة البيانات وتنفيذ العمليات عبر{' '}
                    <b className="text-txt font-semibold">
                      {modelMode === 'local'
                        ? 'Ollama المحلي'
                        : modelMode === 'groq'
                        ? 'Groq السحابي'
                        : 'المحرك الهجين (Auto)'}
                    </b>
                    ...
                  </span>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* ── 3. Quick Chips Above Prompt Bar (Optional suggestions during chat) ── */}
        {!isFreshState && (
          <div className="px-4 py-2 bg-steel-3/40 border-t border-line/60 flex items-center gap-2 overflow-x-auto no-scrollbar">
            <span className="text-[11px] font-semibold text-txt-3 shrink-0 flex items-center gap-1">
              <Icon name="search" size={12} /> استعلامات سريعة:
            </span>
            {PROMPT_TEMPLATES.slice(0, 5).map((pt, i) => (
              <button
                key={i}
                type="button"
                disabled={busy}
                onClick={() => handleSend(pt.prompt)}
                className="text-2xs bg-steel-2 hover:bg-steel-3 border border-line hover:border-hi/50 text-txt-2 hover:text-txt rounded-full px-3 py-1 whitespace-nowrap transition-colors"
              >
                {pt.title}
              </button>
            ))}
          </div>
        )}

        {/* ── 4. Clean Docked Prompt Input Bar ─────────────────────────────── */}
        <div className="sticky bottom-0 z-20 p-3 sm:p-4 bg-steel-2/95 backdrop-blur-xl border-t border-line">
          <div className="max-w-3xl mx-auto w-full flex flex-col gap-1.5">
            {/* Live Listening Banner */}
            {voice.isListening && (
              <div className="px-4 py-2 bg-crit/10 border border-crit/30 rounded-xl flex items-center justify-between text-xs text-crit animate-pulse shadow-md">
                <div className="flex items-center gap-2.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-crit animate-ping" />
                  <span className="font-semibold text-xs">
                    جارٍ الاستماع للصوت ({voice.availableLanguages?.find((l) => l.id === voice.langMode)?.label || 'تلقائي'})
                  </span>
                  <VoiceSoundWave isListening={true} size="md" />
                </div>
                <span className="text-[11px] text-txt-3 font-mono">تحدث ثم اضغط الميكروفون مجدداً للإرسال</span>
              </div>
            )}

            {/* Live Transcribing Banner */}
            {voice.isTranscribing && (
              <div className="px-4 py-2 bg-hi/10 border border-hi/30 rounded-xl flex items-center justify-between text-xs text-hi animate-fade shadow-md">
                <div className="flex items-center gap-2.5">
                  <Icon name="refresh" size={13} className="animate-spin text-hi" />
                  <span className="font-semibold text-xs">جارٍ معالجة الصوت عبر محرك Whisper العصبي...</span>
                </div>
                <span className="text-[11px] text-txt-3 font-mono">دقة متقدمة للمصطلحات واللهجات</span>
              </div>
            )}

            {/* Input Box Wrapper */}
            <div className="relative flex items-end gap-2 bg-steel-3/90 border border-line focus-within:border-hi/70 focus-within:ring-2 focus-within:ring-hi/20 rounded-2xl p-2 sm:p-2.5 transition-all shadow-lg">
              {/* Unified Clean Microphone & Language Control */}
              <div className="relative inline-flex items-center rounded-xl bg-steel-2 border border-line p-0.5 mb-0.5 shrink-0 shadow-sm focus-within:border-hi/50">
                <button
                  type="button"
                  onClick={voice.toggleListening}
                  disabled={voice.isTranscribing}
                  title={voice.isListening ? 'إيقاف التسجيل الصوتي' : 'تحدث بالصوت (Voice Input)'}
                  className={`h-9 px-2.5 rounded-lg flex items-center gap-1.5 transition-all duration-200 ${
                    voice.isListening
                      ? 'mic-btn-active text-white animate-pulse'
                      : voice.isTranscribing
                      ? 'bg-hi/20 text-hi cursor-wait'
                      : 'text-txt-2 hover:text-hi hover:bg-steel active:scale-95'
                  }`}
                  aria-label="تسجيل صوتي"
                >
                  {voice.isTranscribing ? (
                    <Icon name="refresh" size={14} className="animate-spin text-hi" />
                  ) : (
                    <Icon name="mic" size={15} />
                  )}
                  <span className="text-[11px] font-medium hidden sm:inline">
                    {voice.isListening ? 'تسجيل...' : 'صوت'}
                  </span>
                </button>

                <div className="w-px h-5 bg-line/80 mx-0.5" />

                <button
                  type="button"
                  onClick={() => setShowVoiceLangMenu((prev) => !prev)}
                  title="اختيار لغة أو لهجة التحدث"
                  className="h-9 px-2 rounded-lg text-[10.5px] font-mono text-txt-3 hover:text-txt hover:bg-steel flex items-center gap-1 transition-colors"
                >
                  <Icon name="globe" size={12} />
                  <span className="font-semibold">{voice.availableLanguages?.find((l) => l.id === voice.langMode)?.code || 'AUTO'}</span>
                  <Icon name="caret" size={10} className="text-txt-3" />
                </button>

                {showVoiceLangMenu && (
                  <div className="absolute bottom-11 right-0 w-64 bg-steel-3 border border-line rounded-xl p-1 shadow-xl z-50 animate-scale-in">
                    <div className="px-2.5 py-1 text-[10.5px] font-semibold text-txt-3 border-b border-line mb-1">
                      لغة ولهجة التحدث
                    </div>
                    {voice.availableLanguages?.map((lang) => (
                      <button
                        key={lang.id}
                        type="button"
                        onClick={() => {
                          voice.changeLangMode(lang.id)
                          setShowVoiceLangMenu(false)
                        }}
                        className={`w-full text-right px-2.5 py-1.5 rounded-lg text-xs flex items-center justify-between transition-colors ${
                          voice.langMode === lang.id
                            ? 'bg-hi/15 text-hi font-semibold border border-hi/30'
                            : 'text-txt-2 hover:text-txt hover:bg-steel-2'
                        }`}
                      >
                        <span className="flex items-center gap-2">
                          <span className="font-mono text-[10px] px-1 py-0.5 rounded bg-steel border border-line text-txt-3 font-semibold">{lang.code}</span>
                          <span>{lang.label}</span>
                        </span>
                        {voice.langMode === lang.id && <Icon name="check" size={12} className="text-hi" />}
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Dynamic Auto-Expanding Textarea */}
              <textarea
                ref={textareaRef}
                value={draft}
                disabled={busy}
                onChange={(e) => {
                  if (voice.isListening) {
                    voice.stopListening()
                  }
                  if (voice.clearInterimTranscript) {
                    voice.clearInterimTranscript()
                  }
                  setDraft(e.target.value)
                }}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder={
                  voice.isListening
                    ? voice.interimTranscript
                      ? `🎙️ ${voice.interimTranscript}`
                      : 'جارٍ الاستماع والتسجيل... تحدث الآن، واضغط الميكروفون عند الانتهاء'
                    : voice.isTranscribing
                    ? 'جارٍ معالجة الصوت...'
                    : 'اسأل عن معايير السلامة، أو تحدث بالصوت… (Shift+Enter لسطر جديد)'
                }
                className="flex-1 bg-transparent text-xs sm:text-[13px] text-txt placeholder:text-txt-3 focus:outline-none resize-none px-2 py-1.5 max-h-[180px] leading-relaxed"
                style={{ minHeight: '44px' }}
              />

              {/* Clear draft action if multiline typing */}
              {draft.length > 20 && (
                <button
                  type="button"
                  onClick={() => setDraft('')}
                  title="مسح النص"
                  className="p-2 text-txt-3 hover:text-txt rounded-xl hover:bg-steel-2 transition-colors shrink-0 mb-0.5"
                >
                  <Icon name="close" size={14} />
                </button>
              )}

              {/* Send Button */}
              <button
                type="button"
                disabled={busy || !draft.trim() || voice.isTranscribing}
                onClick={() => handleSend()}
                className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200 mb-0.5 shadow-md ${
                  draft.trim() && !busy && !voice.isTranscribing
                    ? 'bg-hi text-white hover:bg-hi2 active:scale-95 shadow-hi/20'
                    : 'bg-steel-2 text-txt-3 cursor-not-allowed opacity-60'
                }`}
                aria-label="إرسال"
              >
                <Icon name="send" size={16} />
              </button>
            </div>

            {/* Keyboard & Status Hint */}
            <div className="flex items-center justify-between px-2 text-[10px] text-txt-3 font-mono">
              <span>
                اضغط <kbd className="px-1 py-0.5 rounded bg-steel-3 border border-line text-txt-2">Enter</kbd> للإرسال · <kbd className="px-1 py-0.5 rounded bg-steel-3 border border-line text-txt-2">Shift + Enter</kbd> لسطر جديد
              </span>
              <span className="hidden sm:inline">
                الدور الحالي: <b className="text-hi">{displayUserRole}</b>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
