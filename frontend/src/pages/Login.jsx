import { useState } from 'react'
import { Navigate, useLocation, useNavigate, useSearchParams } from 'react-router-dom'
import Icon from '../components/Icon.jsx'
import { Wordmark } from '../components/layout.jsx'
import { useAuth } from '../hooks.jsx'

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const [params] = useSearchParams()

  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [reveal, setReveal] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(params.get('expired') ? 'انتهت صلاحية الجلسة — سجّل الدخول مرة أخرى' : '')

  if (user) return <Navigate to={loc.state?.from || '/'} replace />

  async function submit(e) {
    e.preventDefault()
    if (!username.trim() || !password.trim()) {
      setError('اكتب اسم المستخدم وكلمة المرور')
      return
    }
    setBusy(true)
    setError('')
    try {
      await login(username.trim(), password.trim())
      nav(loc.state?.from || '/', { replace: true })
    } catch (err) {
      setError(err.message || 'تعذّر تسجيل الدخول')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="min-h-screen flex flex-col">
      <div className="hz-stripe" />

      <div className="flex-1 grid lg:grid-cols-[1fr_420px]">
        {/* Left: what this console is. Kept factual — it's an internal tool. */}
        <section className="hidden lg:flex flex-col justify-between p-12 border-e border-line bg-steel-2">
          <div className="w-full flex justify-center py-2">
            <Wordmark width={520} height={115} centered={true} isWhite={true} />
          </div>

          <div className="max-w-xl">
            <h1 className="text-[27px] font-semibold tracking-tight leading-snug">
              نظام إدارة السلامة والصحة المهنية
            </h1>
            <p className="text-txt-2 text-sm mt-3 leading-8">
              منصّة موحّدة لتسجيل الحوادث، إصدار تصاريح العمل، تقييم المخاطر، جولات التفتيش، ومتابعة
              الكفاءات والتدريب داخل مصنع أكسسوارات الكابلات — مربوطة بالمراقبة الآلية وسجل تدقيق كامل.
            </p>

            <dl className="grid grid-cols-3 gap-4 mt-9 pt-7 border-t border-line">
              {[
                ['9', 'مناطق تشغيل'],
                ['388', 'موظف مغطّى'],
                ['148', 'يوم بدون إصابة مُعطِّلة'],
              ].map(([v, l]) => (
                <div key={l}>
                  <dt className="font-mono num text-[26px] font-bold tracking-tight">{v}</dt>
                  <dd className="text-xs text-txt-3 mt-1">{l}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="font-mono num text-2xs text-txt-3 flex items-center gap-2">
            <Icon name="security" size={13} />
            HSE-MS v2.4 · ISO 45001 · كل عملية تُسجَّل في سجل تدقيق غير قابل للتعديل
          </div>
        </section>

        {/* Right: the form */}
        <section className="flex items-center justify-center p-6">
          <div className="w-full max-w-[340px]">
            <div className="lg:hidden mb-8">
              <Wordmark width={280} height={65} centered={false} isWhite={true} />
            </div>

            <h2 className="text-lg font-semibold">تسجيل الدخول</h2>
            <p className="text-xs text-txt-3 font-mono num mt-1 mb-7">ESCA HSE CONSOLE · SSO / JWT</p>

            <form onSubmit={submit} noValidate>
              <div className="mb-3.5">
                <label className="label" htmlFor="u">
                  اسم المستخدم
                </label>
                {/* Latin-only credentials: turn off the corrections a phone or
                    tablet would otherwise apply to the first character. */}
                <input
                  id="u"
                  className="field"
                  value={username}
                  autoComplete="username"
                  autoCapitalize="none"
                  autoCorrect="off"
                  spellCheck={false}
                  dir="ltr"
                  onChange={(e) => setUsername(e.target.value)}
                />
              </div>

              <div className="mb-3.5">
                <label className="label" htmlFor="p">
                  كلمة المرور
                </label>
                <div className="relative">
                  <input
                    id="p"
                    type={reveal ? 'text' : 'password'}
                    className="field pe-10"
                    value={password}
                    autoComplete="current-password"
                    autoCapitalize="none"
                    autoCorrect="off"
                    spellCheck={false}
                    dir="ltr"
                    onChange={(e) => setPassword(e.target.value)}
                  />
                  <button
                    type="button"
                    onClick={() => setReveal((r) => !r)}
                    aria-label={reveal ? 'إخفاء كلمة المرور' : 'إظهار كلمة المرور'}
                    className="absolute top-1/2 -translate-y-1/2 end-2.5 text-txt-3 hover:text-txt transition-colors"
                  >
                    <Icon name={reveal ? 'eye-off' : 'eye'} size={15} />
                  </button>
                </div>
              </div>

              {error && (
                <div
                  className="text-xs px-3 py-2.5 rounded mb-3.5 flex items-start gap-2"
                  style={{ background: 'rgba(224,72,60,.1)', border: '1px solid rgba(224,72,60,.4)', color: '#f08b82' }}
                >
                  <Icon name="incident" size={14} className="mt-0.5" />
                  {error}
                </div>
              )}

              <button type="submit" className="btn btn-pri w-full justify-center py-2.5" disabled={busy}>
                {busy ? 'جارٍ التحقق…' : 'دخول'}
              </button>
            </form>

            <p className="mt-7 pt-5 border-t border-line text-2xs text-txt-3 leading-6">
              الدخول بحساب الموقع الخاص بك. لو نسيت بياناتك، كلّم إدارة السلامة والصحة المهنية.
            </p>
          </div>
        </section>
      </div>
    </div>
  )
}
