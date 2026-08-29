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

const PROMPT_TEMPLATES = [
  // ── RAG Knowledge & Standards ──────────────────────────────────────────
  {
    title: 'اشتراطات الأماكن المغلقة (OSHA)',
    category: 'معايير السلامة',
    icon: 'document',
    prompt: 'ما هي اشتراطات الدخول للأماكن المغلقة وحدود فحص الغازات (O2, LEL, H2S, CO) حسب معايير OSHA 1910.146؟',
    tone: 'in',
    badge: 'RAG OSHA',
  },
  {
    title: 'القواعد الذهبية للسلامة (ESCA)',
    category: 'قواعد السويدي',
    icon: 'reports',
    prompt: 'ما هي القواعد الذهبية العشر للسلامة (ESCA Safety Golden Rules) المعتمدة في مصانع السويدي للكابلات؟',
    tone: 'safe',
    badge: 'Golden Rules',
  },
  {
    title: 'معادلة احتساب TRIR و LTIFR',
    category: 'مؤشرات الأداء',
    icon: 'reports',
    prompt: 'ما هي المعادلة المعتمدة لحساب مؤشرات TRIR و LTIFR والأيام المتبقية لنفاد مخزون المهمات (Days Until Stockout)؟',
    tone: 'safe',
    badge: 'KPIs',
  },
  {
    title: 'بنود مواصفة ISO 45001',
    category: 'الأيزو الدولية',
    icon: 'document',
    prompt: 'اشرح متطلبات البند 6 (Planning & HIRA) والبند 10 (CAPA) في المواصفة القياسية الدولية ISO 45001:2018.',
    tone: 'in',
    badge: 'ISO 45001',
  },

  // ── Live Database Queries ──────────────────────────────────────────────
  {
    title: 'الحوادث المفتوحة والخطورة',
    category: 'استعلام مباشر',
    icon: 'incident',
    prompt: 'ما هي الحوادث المفتوحة حالياً في قاعدة البيانات وما هي درجات خطورتها والإجراءات المتخذة؟',
    tone: 'cr',
    badge: 'Live DB',
  },
  {
    title: 'تصاريح العمل النشطة ePTW',
    category: 'استعلام مباشر',
    icon: 'permit',
    prompt: 'اعرض تصاريح العمل النشطة والمنتهية المسجلة حالياً في قاعدة بيانات الموقع.',
    tone: 'wn',
    badge: 'ePTW',
  },
  {
    title: 'مخزون المهمات تحت حد الطلب',
    category: 'تنبؤ بالمخزون',
    icon: 'ppe',
    prompt: 'اعرض أصناف مهمات الوقاية الشخصية (PPE) التي انخفض رصيدها عن حد إعادة الطلب مع الأيام المتبقية للنفاد.',
    tone: 'in',
    badge: 'PPE Stock',
  },
  {
    title: 'مطافئ الحريق المنتهية الصلاحية',
    category: 'معدات الطوارئ',
    icon: 'fire',
    prompt: 'ما هي مطافئ الحريق ومعدات الإطفاء المنتهية الصلاحية أو التي تحتاج فحص دوري عاجل؟',
    tone: 'cr',
    badge: 'Fire Safety',
  },

  // ── CRUD Action Operations ─────────────────────────────────────────────
  {
    title: 'تسجيل بلاغ حادث فوري',
    category: 'عمليات CRUD',
    icon: 'incident',
    prompt: 'سجل بلاغ حادث جديد: العنوان "تسريب زيت هيدروليكي"، الوصف "تسريب زيت في خط سحب الكابلات رقم 3 دون إصابات"، المنطقة 2، درجة الخطورة MODERATE، نوع الحادث UNSAFE_CONDITION.',
    tone: 'cr',
    badge: 'CRUD Create',
  },
  {
    title: 'اعتماد تصريح عمل ePTW',
    category: 'عمليات CRUD',
    icon: 'permit',
    prompt: 'اعتمد تصريح العمل ePTW رقم 10 وضع ملاحظة الاعتماد "تمت مراجعة خطة العزل وإجراء فحص الغازات والموافقة على بدء العمل".',
    tone: 'safe',
    badge: 'CRUD Update',
  },
  {
    title: 'إضافة إجراء تصحيحي CAPA',
    category: 'عمليات CRUD',
    icon: 'reports',
    prompt: 'انشئ إجراء تصحيحي جديد CAPA: العنوان "تركيب حساسات حرارية إضافية للوحة التحكم"، الأولوية HIGH، موعد الاستحقاق خلال 5 أيام، وتعيين المسؤولية للمهندس المسؤول.',
    tone: 'wn',
    badge: 'CRUD Create',
  },
  {
    title: 'صرف مهمة وقاية PPE',
    category: 'عمليات CRUD',
    icon: 'ppe',
    prompt: 'سجل حركة صرف مهمة وقاية شخصية: صرف عدد 2 خوذة سلامة للموظف رقم 3 وتحديث رصيد المخزون الفعلي.',
    tone: 'in',
    badge: 'CRUD Create',
  },
]

const AGENT_TOOLS = [
  { name: 'search_hse_knowledge', desc: 'استرجاع لوائح ISO 45001، معايير OSHA، وقواعد السويدي الذهبية', target: 'ISO 45001 / OSHA / ESCA SOPs', category: 'RAG' },
  { name: 'search_database_entities', desc: 'بحث ذكي شامل عبر الحوادث، التصاريح، المهمات، الموظفين، والمعدات', target: 'HSE Database Entities', category: 'RAG' },
  { name: 'list_incidents / list_permits', desc: 'استعلام مباشر لسجلات الحوادث وتصاريح العمل الإلكترونية ePTW', target: 'incidents, permits', category: 'READ' },
  { name: 'list_certificates / list_courses', desc: 'استعلام وتدقيق سجلات الشهادات والدورات التدريبية للموظفين', target: 'certificates, training_courses', category: 'READ' },
  { name: 'get_ppe_stock_status', desc: 'تحليل أرصدة المخزون والتنبؤ بمعدلات الاستهلاك ونفاد الأصناف', target: 'ppe_inventory, transactions', category: 'READ' },
  { name: 'get_expired_fire_equipment', desc: 'فحص مطافئ الحريق المنتهية وجداول الاختبار الهيدروستاتيكي', target: 'fire_equipment, inspections', category: 'READ' },
  { name: 'create_incident / create_permit', desc: 'تسجيل الحوادث الفورية وإصدار تصاريح العمل الإلكترونية', target: 'incidents, permits (INSERT)', category: 'CREATE' },
  { name: 'create_certificate / create_capa', desc: 'إصدار شهادات التدريب وإنشاء إجراءات CAPA وصرف مهمات الوقاية', target: 'certificates, capa (INSERT)', category: 'CREATE' },
  { name: 'update_permit_status / update_cert', desc: 'اعتماد التصاريح، تحديث صلاحية الشهادات، وإغلاق الحوادث', target: 'permits, certificates, incidents (UPDATE)', category: 'UPDATE' },
  { name: 'delete_record / cancel_entity', desc: 'إلغاء التصاريح وحذف المسودات مع التوثيق الكامل في سجل التدقيق', target: 'audit_log + Allowed Tables (DELETE)', category: 'DELETE' },
]

export default function AiAgent() {
  const { user } = useAuth()
  const toast = useToast()
  const { mode } = useTheme()
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

  const activeUserRole = user?.role || user?.role_name || (user?.username === 'mostafa' ? 'HSE_MANAGER' : (user?.username === 'admin' ? 'ADMIN' : 'HSE_MANAGER'))
  const isWhiteLogo = mode !== 'light'

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
        user?.username || user?.displayName || 'USR-DEV'
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

      // Check specifically for incident creation
      const incCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_incident' ||
          t.name === 'create_incident' ||
          t.tool === 'create_incident'
      )
      if (incCall) {
        const args = incCall.args || incCall.arguments || {}
        const result = incCall.result || incCall.output || {}
        const title = args.title || result.title || 'بلاغ حادث'
        const notifObj = {
          id: 'NTF-' + (result.notification_id || Date.now()),
          notificationId: result.notification_id || Date.now(),
          title: `تسجيل بلاغ حادث جديد: ${title}`,
          body: `تم تسجيل بلاغ حادث جديد بنجاح في النظام وربطه بسجل التدقيق وإخطار مسؤولي السلامة.`,
          time: 'الآن (مباشر)',
          color: 'var(--crit)',
          type: 'INCIDENT',
          to: '/incidents',
          unread: true,
        }
        window.dispatchEvent(new CustomEvent('hse:notification', { detail: notifObj }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast(`تم تسجيل بلاغ الحادث (${title}) بنجاح وإرسال الإشعار`, 'cr')
      }

      // Check specifically for permit creation / approval
      const permitCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_permit' ||
          t.name === 'create_permit' ||
          t.tool_name === 'update_permit_status' ||
          t.name === 'update_permit_status'
      )
      if (permitCall) {
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
        toast('تم تحديث تصاريح العمل الإلكترونية ePTW بنجاح', 'ok')
      }

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

                    {/* Message Actions (Copy text) */}
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
            {/* Input Box Wrapper */}
            <div className="relative flex items-end gap-2 bg-steel-3/90 border border-line focus-within:border-hi/70 focus-within:ring-2 focus-within:ring-hi/20 rounded-2xl p-2 sm:p-2.5 transition-all shadow-lg">
              {/* Dynamic Auto-Expanding Textarea */}
              <textarea
                ref={textareaRef}
                value={draft}
                disabled={busy}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={handleKeyDown}
                rows={1}
                placeholder="اسأل عن معايير السلامة (OSHA / ISO 45001)، استعلم عن الحوادث والمهمات، أو اطلب إجراء تعديل..."
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
                disabled={busy || !draft.trim()}
                onClick={() => handleSend()}
                className={`w-9 h-9 sm:w-10 sm:h-10 rounded-xl flex items-center justify-center shrink-0 transition-all duration-200 mb-0.5 shadow-md ${
                  draft.trim() && !busy
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
                الدور الحالي: <b className="text-hi">{activeUserRole}</b>
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
