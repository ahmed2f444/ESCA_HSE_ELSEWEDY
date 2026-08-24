import { useEffect, useRef, useState } from 'react'
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
  const inputRef = useRef(null)

  useEffect(() => {
    if (!open || suggestions.length) return
    assistant.suggestions().then(setSuggestions).catch(() => {})
  }, [open, suggestions.length])

  useEffect(() => {
    if (open) {
      setTimeout(() => inputRef.current?.focus(), 150)
    }
  }, [open])

  useEffect(() => {
    bodyRef.current?.scrollTo({ top: bodyRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, busy])

  async function send(question) {
    const q = (question ?? draft).trim()
    if (!q || busy) return
    setDraft('')
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
    }
  }

  return (
    <>
      {/* Floating Trigger Button */}
      {!open && (
        <button
          onClick={() => setOpen(true)}
          className="fixed bottom-6 end-6 z-[800] group flex items-center gap-3 bg-steel-2 hover:bg-steel-3 border border-line hover:border-hi/60 rounded-full ps-3.5 pe-5 py-2.5 text-xs font-semibold shadow-2xl transition-all duration-200 hover:scale-105 active:scale-95"
          style={{
            boxShadow: '0 12px 32px rgba(0, 0, 0, 0.45), 0 0 0 1px rgba(255, 255, 255, 0.06)',
          }}
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
          className="fixed bottom-6 end-6 z-[800] w-[min(460px,calc(100vw-2rem))] bg-steel-2/95 backdrop-blur-xl border border-line/80 rounded-2xl flex flex-col overflow-hidden shadow-2xl animate-pop"
          style={{
            height: 'min(640px, calc(100vh - 5rem))',
            boxShadow: '0 24px 60px rgba(0, 0, 0, 0.65), 0 0 0 1px rgba(255, 255, 255, 0.08)',
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
                    LIVE DB
                  </span>
                </div>
                <p className="text-[10px] text-txt-3 font-mono">135 Tables Live Grounding</p>
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

          {/* Input Footer */}
          <form
            className="border-t border-line p-3 bg-steel-3/80 flex items-center gap-2"
            onSubmit={(e) => {
              e.preventDefault()
              send()
            }}
          >
            <input
              ref={inputRef}
              className="field flex-1 text-xs py-2 px-3 bg-steel-2 border-line focus:border-hi"
              placeholder="اكتب سؤالك للوكيل الذكي…"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              disabled={busy}
            />
            <button
              type="submit"
              className="btn btn-pri px-3.5 py-2 rounded-lg shrink-0"
              disabled={busy || !draft.trim()}
              aria-label="إرسال"
            >
              <Icon name="send" size={14} />
            </button>
          </form>
        </section>
      )}
    </>
  )
}
