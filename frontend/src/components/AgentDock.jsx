import { useEffect, useRef, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import Icon from './Icon.jsx'
import MarkdownRenderer from './MarkdownRenderer.jsx'
import { assistant } from '../api/endpoints.js'
import { useAuth } from '../hooks.jsx'

/**
 * Floating AI Safety Assistant Dock with modern glassmorphic aesthetics and model switching.
 */
export default function AgentDock() {
  const { user } = useAuth()
  const [open, setOpen] = useState(false)
  const [modelMode, setModelMode] = useState('auto') // 'groq' | 'local' | 'auto'
  const [messages, setMessages] = useState([
    {
      role: 'agent',
      text: 'مرحباً بك! أنا المساعد الذكي للسلامة والصحة المهنية (ESCA AI Assistant).\n\nكيف يمكنني مساعدتك اليوم في استعلام الحوادث، التصاريح، المخاطر، أو قراءات الحساسات الحية؟',
      timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
    },
  ])
  const [suggestions, setSuggestions] = useState([])
  const [draft, setDraft] = useState('')
  const [busy, setBusy] = useState(false)
  const bodyRef = useRef(null)
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!open || suggestions.length) return
    assistant.suggestions().then(setSuggestions).catch(() => {})
  }, [open, suggestions.length])

  useEffect(() => {
    if (open) {
      setTimeout(() => textareaRef.current?.focus(), 150)
    }
  }, [open])

  // Dedicated container-only scroll to bottom
  const scrollToBottom = useCallback((behavior = 'smooth') => {
    if (bodyRef.current) {
      bodyRef.current.scrollTo({
        top: bodyRef.current.scrollHeight,
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
    const minHeight = 38
    const maxHeight = 120
    const nextHeight = Math.min(Math.max(textarea.scrollHeight, minHeight), maxHeight)
    textarea.style.height = `${nextHeight}px`
    textarea.style.overflowY = textarea.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [draft])

  async function send(question) {
    const q = (question ?? draft).trim()
    if (!q || busy) return
    setDraft('')
    if (textareaRef.current) {
      textareaRef.current.style.height = '38px'
      textareaRef.current.style.overflowY = 'hidden'
    }

    const timeNow = new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' })
    setMessages((m) => [...m, { role: 'user', text: q, timestamp: timeNow }])
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
      const cleanAnswer = cleanText || 'تم استخراج البيانات من قاعدة البيانات بنجاح.'

      // Check if any certificate, permit, incident, or safety action was executed by AI agent
      const toolCalls = res.tool_calls || res.tools || []
      if (toolCalls.length > 0) {
        // Trigger live re-fetch for notifications and database state
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:data-changed'))
      }

      const certCall = toolCalls.find(
        (t) =>
          t.tool_name === 'create_certificate' ||
          t.name === 'create_certificate' ||
          t.name === 'create_training_certificate' ||
          t.tool === 'create_certificate'
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
      }

      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          text: cleanAnswer || 'تم استخراج البيانات من قاعدة البيانات بنجاح.',
          tools: res.tool_calls || res.tools || [],
          model: res.model_used || (modelMode === 'local' ? 'Local Ollama' : 'Groq Online'),
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
    } catch (e) {
      setMessages((m) => [
        ...m,
        {
          role: 'agent',
          error: true,
          text: `تعذّر الاتصال بخدمة المساعد الذكي: ${e.message}`,
          timestamp: new Date().toLocaleTimeString('ar-EG', { hour: '2-digit', minute: '2-digit' }),
        },
      ])
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
        send()
      }
    }
  }

  return (
    <>
      {/* Floating Trigger Button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 end-6 z-[800] group flex items-center gap-3 bg-steel-2 hover:bg-steel-3 border border-line hover:border-hi/60 rounded-full ps-3.5 pe-5 py-2.5 text-xs font-semibold shadow-xl transition-all duration-200 hover:scale-105 active:scale-95"
        >
          <span className="relative flex items-center justify-center w-8 h-8 rounded-full bg-gradient-to-tr from-hi to-hi-2 text-white shadow-md">
            <Icon name="chat" size={16} />
            <span className="absolute -top-0.5 -end-0.5 w-2.5 h-2.5 rounded-full bg-safe border-2 border-steel-2" />
          </span>
          <div className="text-start">
            <div className="text-txt font-semibold leading-tight">المساعد الذكي للسلامة</div>
            <div className="text-[10px] text-txt-3 font-mono">AI SAFETY ASSISTANT</div>
          </div>
        </button>
      )}

      {/* Floating Chat Modal */}
      {open && (
        <section
          className="fixed bottom-6 end-6 z-[800] w-[min(480px,calc(100vw-2rem))] bg-steel-2 border border-line rounded-2xl flex flex-col overflow-hidden shadow-2xl animate-pop"
          style={{
            height: 'min(640px, calc(100vh - 5rem))',
          }}
        >
          {/* Header */}
          <header className="px-4 py-3 bg-steel-3/90 border-b border-line flex items-center justify-between gap-3">
            <div className="flex items-center gap-2.5">
              <span className="w-8 h-8 rounded-lg bg-gradient-to-tr from-hi to-hi-2 flex items-center justify-center text-white shadow-sm shrink-0">
                <Icon name="chat" size={16} />
              </span>
              <div>
                <div className="flex items-center gap-2">
                  <h3 className="text-xs sm:text-[13px] font-bold text-txt">المساعد الذكي للسلامة</h3>
                  <span className="px-1.5 py-0.5 rounded text-[9.5px] font-mono bg-safe/15 text-safe border border-safe/30">
                    ONLINE
                  </span>
                </div>
                <p className="text-[10px] text-txt-3 font-mono">ESCA Safety Assistant</p>
              </div>
            </div>

            <div className="flex items-center gap-1">
              <Link
                to="/ai-agent"
                onClick={() => setOpen(false)}
                title="فتح في صفحة كاملة"
                className="p-1.5 rounded-md text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors"
              >
                <Icon name="external" size={15} />
              </Link>
              <button
                className="p-1.5 rounded-md text-txt-3 hover:text-crit hover:bg-steel-3 transition-colors"
                onClick={() => setOpen(false)}
                aria-label="إغلاق"
              >
                <Icon name="close" size={16} />
              </button>
            </div>
          </header>

          {/* Model Switcher Segmented Control */}
          <div className="px-3.5 py-2 bg-steel-3/60 border-b border-line flex items-center justify-between gap-1 text-[11px]">
            <span className="text-[10.5px] font-semibold text-txt-3 shrink-0">النموذج:</span>
            <div className="flex items-center gap-1 bg-steel-2 p-0.5 rounded-lg border border-line">
              <button
                type="button"
                onClick={() => setModelMode('groq')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'groq'
                    ? 'bg-hi text-white shadow-sm'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="cloud" size={11} />
                <span>Groq Online</span>
              </button>
              <button
                type="button"
                onClick={() => setModelMode('local')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'local'
                    ? 'bg-safe text-white shadow-sm'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="server" size={11} />
                <span>Ollama Local</span>
              </button>
              <button
                type="button"
                onClick={() => setModelMode('auto')}
                className={`px-2 py-1 rounded text-[10.5px] font-semibold flex items-center gap-1 transition-all ${
                  modelMode === 'auto'
                    ? 'bg-steel-3 text-txt shadow-sm border border-line'
                    : 'text-txt-2 hover:text-txt'
                }`}
              >
                <Icon name="bolt" size={11} />
                <span>تلقائي</span>
              </button>
            </div>
          </div>

          {/* Messages Stream */}
          <div ref={bodyRef} className="flex-1 overflow-y-auto p-4 space-y-3.5">
            {messages.map((m, i) => (
              <div
                key={i}
                className={`flex flex-col ${m.role === 'user' ? 'items-end' : 'items-start'}`}
              >
                <div className="flex items-center gap-1.5 mb-1 px-1 text-[10px] text-txt-3 font-mono">
                  <span>{m.role === 'user' ? user?.displayName || user?.name || user?.username || 'أنت' : 'ESCA AI Agent'}</span>
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
                  className={`rounded-xl p-3 text-xs leading-6 max-w-[88%] shadow-sm ${
                    m.role === 'user'
                      ? 'bg-hi text-white rounded-br-none whitespace-pre-wrap font-medium'
                      : m.error
                      ? 'bg-crit/15 border border-crit/40 text-crit rounded-bl-none whitespace-pre-wrap'
                      : 'bg-steel-3/90 border border-line text-txt-1 rounded-bl-none'
                  }`}
                >
                  {m.role === 'user' || m.error ? (
                    m.text
                  ) : (
                    <MarkdownRenderer content={m.text} />
                  )}
                </div>
              </div>
            ))}

            {busy && (
              <div className="flex flex-col items-start">
                <div className="bg-steel-3/90 border border-line rounded-xl p-3 text-xs text-txt-2 flex items-center gap-2">
                  <span className="w-2 h-2 rounded-full bg-info animate-ping" />
                  <span className="text-[11.5px]">
                    جارٍ الاستعلام عبر{' '}
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
          </div>

          {/* Quick suggestions if few messages */}
          {suggestions.length > 0 && messages.length <= 2 && (
            <div className="px-3.5 py-2 bg-steel-3/40 border-t border-line flex items-center gap-1.5 overflow-x-auto">
              <span className="text-[10px] font-semibold text-txt-3 shrink-0">مقترحات:</span>
              {suggestions.slice(0, 3).map((s, idx) => (
                <button
                  key={idx}
                  disabled={busy}
                  onClick={() => send(s)}
                  className="text-[10.5px] bg-steel-3 hover:bg-steel border border-line hover:border-hi/50 text-txt-2 hover:text-txt rounded-md px-2.5 py-1 whitespace-nowrap transition-colors"
                >
                  {s}
                </button>
              ))}
            </div>
          )}

          {/* Input Footer with Auto-Expanding Textarea */}
          <div className="border-t border-line p-3 bg-steel-3/80">
            <div className="flex items-end gap-2 bg-steel-2 border border-line focus-within:border-hi/70 rounded-xl p-1.5 transition-all">
              <textarea
                ref={textareaRef}
                className="flex-1 bg-transparent text-xs text-txt placeholder:text-txt-3 focus:outline-none resize-none px-2 py-1 leading-relaxed max-h-[120px]"
                style={{ minHeight: '38px' }}
                placeholder="اكتب سؤالك للوكيل الذكي… (Shift+Enter لسطر جديد)"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={busy}
                rows={1}
              />
              <button
                type="button"
                onClick={() => send()}
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition-all ${
                  draft.trim() && !busy
                    ? 'bg-hi text-white hover:bg-hi2 active:scale-95 shadow-sm'
                    : 'bg-steel-3 text-txt-3 opacity-60 cursor-not-allowed'
                }`}
                disabled={busy || !draft.trim()}
                aria-label="إرسال"
              >
                <Icon name="send" size={14} />
              </button>
            </div>
          </div>
        </section>
      )}
    </>
  )
}
