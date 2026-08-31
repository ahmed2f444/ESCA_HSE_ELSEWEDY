import { useEffect, useState } from 'react'
import { profile as profileApi } from '../../api/endpoints.js'
import Icon from '../Icon.jsx'

export default function EmailChangeFlow({
  value,
  activeEditor,
  onActivate,
  onDeactivate,
  onChanged,
  onSuccess,
  onError,
}) {
  const [step, setStep] = useState('locked') // 'locked' | 'request' | 'verify'
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [code, setCode] = useState('')
  const [newEmail, setNewEmail] = useState(value || '')
  const [developmentCode, setDevelopmentCode] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (activeEditor !== 'email' && step !== 'locked') {
      setStep('locked')
      setCode('')
      setNewEmail(value || '')
      setSecondsLeft(0)
      setDevelopmentCode('')
    }
  }, [activeEditor, step, value])

  useEffect(() => {
    if (step !== 'verify' || secondsLeft <= 0) return undefined
    const timer = setInterval(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearInterval(timer)
  }, [step, secondsLeft])

  function handleCancel() {
    setStep('locked')
    setCode('')
    setNewEmail(value || '')
    setSecondsLeft(0)
    setDevelopmentCode('')
    onDeactivate?.()
  }

  async function handleRequestCode() {
    const email = newEmail.trim().toLowerCase()
    if (email.length < 5) {
      onError('البريد الإلكتروني يجب أن يحتوي على 5 أحرف على الأقل')
      return
    }
    if (!/^[^\s@]+@(?:esca\.local|elsewedy\.com)$/i.test(email)) {
      onError('يجب أن ينتهي البريد الإلكتروني بنطاق الشركة المعتمد (@esca.local أو @elsewedy.com)')
      return
    }
    if (email === String(value || '').trim().toLowerCase()) {
      onError('البريد الجديد مطابق للبريد الحالي')
      return
    }

    setBusy(true)
    try {
      const response = await profileApi.requestEmailCode()
      setSecondsLeft(response.expiresInSeconds || 120)
      setDevelopmentCode(response.developmentCode || '')
      setStep('verify')
      onSuccess(response.developmentCode
        ? `رمز التحقق التجريبي: ${response.developmentCode}`
        : 'تم إرسال رمز التحقق إلى بريدك الإلكتروني')
    } catch (err) {
      onError(err.message || 'تعذر إرسال رمز التحقق')
    } finally {
      setBusy(false)
    }
  }

  async function handleVerify(e) {
    e.preventDefault()
    if (!code.trim()) {
      onError('يرجى إدخال رمز التحقق المكون من 6 أرقام')
      return
    }
    setBusy(true)
    try {
      const fresh = await profileApi.verifyEmailCode(code.trim(), newEmail.trim().toLowerCase())
      onChanged(fresh)
      setStep('locked')
      setCode('')
      setSecondsLeft(0)
      setDevelopmentCode('')
      onDeactivate?.()
      onSuccess('تم تحديث البريد الإلكتروني بنجاح')
    } catch (error) {
      onError(error.message || 'تعذر تغيير البريد الإلكتروني — تأكد من صحة الرمز')
    } finally {
      setBusy(false)
    }
  }

  const formatTimer = (s) => {
    const mins = Math.floor(s / 60)
    const secs = s % 60
    return `${mins}:${secs < 10 ? '0' : ''}${secs}`
  }

  return (
    <div className="flex flex-col gap-1.5 w-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-2 px-1">
        <label className="flex items-center gap-1.5 text-xs font-bold text-txt-2">
          <Icon name="mail" size={14} className="text-txt-3" />
          <span>البريد الإلكتروني المؤسسي</span>
        </label>
        <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-safe/10 text-safe border border-safe/25">
          <Icon name="check-circle" size={11} />
          <span>موثق بالـ MFA</span>
        </span>
      </div>

      {/* Locked State: Display Row */}
      {step === 'locked' && (
        <div className="group relative rounded-xl border border-line/70 hover:border-line bg-steel-3/50 hover:bg-steel-3/80 transition-all duration-200">
          <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 min-h-[44px]">
            <span className="text-sm font-medium font-mono text-txt truncate select-text">
              {value || '—'}
            </span>
            <button
              type="button"
              onClick={() => {
                onActivate()
                setStep('request')
                setNewEmail(value || '')
              }}
              className="p-1.5 rounded-lg text-txt-3 hover:text-hi2 hover:bg-steel-2/90 transition-all duration-150 active:scale-90 border border-transparent hover:border-line/50"
              title="تغيير البريد الإلكتروني"
            >
              <Icon name="edit" size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 1: Request OTP State */}
      {step === 'request' && (
        <div className="p-4 rounded-xl border border-hi/40 bg-steel-2 shadow-lg animate-fade flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-txt">الخطوة 1: أدخل البريد الإلكتروني الجديد</span>
            <button
              type="button"
              onClick={handleCancel}
              className="text-txt-3 hover:text-txt p-1 rounded hover:bg-steel-3"
            >
              <Icon name="x" size={15} />
            </button>
          </div>

          <div className="flex flex-col gap-2 sm:flex-row sm:items-center">
            <input
              type="email"
              dir="ltr"
              value={newEmail}
              placeholder="username@esca.local"
              onChange={(e) => setNewEmail(e.target.value)}
              className="flex-1 bg-steel-3 border border-line focus:border-hi text-txt rounded-lg px-3 py-2 text-sm font-mono outline-none"
              autoFocus
            />
            <button
              type="button"
              disabled={busy || !newEmail.trim()}
              onClick={handleRequestCode}
              className="px-4 py-2 rounded-lg bg-hi hover:bg-hi2 text-hi-txt font-semibold text-xs transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm shrink-0 flex items-center justify-center gap-1.5"
            >
              {busy ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>...جارٍ الإرسال</span>
                </>
              ) : (
                <>
                  <Icon name="send" size={13} />
                  <span>طلب رمز التحقق</span>
                </>
              )}
            </button>
          </div>
          <span className="text-[11px] text-txt-3">
            سيتم إرسال رمز أمان إلى البريد الحالي للتحقق من هويتك قبل اعتماد التغيير.
          </span>
        </div>
      )}

      {/* Step 2: Verify Code State */}
      {step === 'verify' && (
        <form
          onSubmit={handleVerify}
          className="p-4 rounded-xl border border-safe/40 bg-steel-2 shadow-lg animate-fade flex flex-col gap-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-txt">الخطوة 2: أدخل رمز التحقق (OTP)</span>
              <span
                className={`text-2xs font-mono font-bold px-2 py-0.5 rounded-full ${
                  secondsLeft > 30
                    ? 'bg-safe/15 text-safe border border-safe/30'
                    : 'bg-crit/15 text-crit border border-crit/30 animate-pulse'
                }`}
              >
                ⏱ {formatTimer(secondsLeft)}
              </span>
            </div>
            <button
              type="button"
              onClick={handleCancel}
              className="text-txt-3 hover:text-txt p-1 rounded hover:bg-steel-3"
            >
              <Icon name="x" size={15} />
            </button>
          </div>

          {developmentCode && (
            <div className="p-2 rounded-lg bg-hi/10 border border-hi/25 text-hi text-xs font-mono flex items-center justify-between">
              <span>رمز التحقق التجريبي (Dev):</span>
              <strong className="text-sm tracking-widest">{developmentCode}</strong>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <div className="flex flex-col gap-1">
              <span className="text-[11px] text-txt-3">رمز التحقق (6 أرقام):</span>
              <input
                type="text"
                dir="ltr"
                inputMode="numeric"
                maxLength={6}
                value={code}
                placeholder="000000"
                onChange={(e) => setCode(e.target.value.replace(/\D/g, ''))}
                className="bg-steel-3 border border-line focus:border-safe text-txt text-center rounded-lg px-3 py-2 text-base font-mono tracking-widest font-bold outline-none"
                autoFocus
                required
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-[11px] text-txt-3">البريد الجديد المراد تعيينه:</span>
              <input
                type="email"
                dir="ltr"
                value={newEmail}
                readOnly
                className="bg-steel-3/60 border border-line/50 text-txt-2 rounded-lg px-3 py-2 text-sm font-mono outline-none"
              />
            </div>
          </div>

          <div className="flex items-center justify-end gap-2 mt-1">
            {secondsLeft <= 0 ? (
              <button
                type="button"
                onClick={handleRequestCode}
                disabled={busy}
                className="px-3 py-1.5 rounded-lg text-xs font-semibold bg-warn/15 hover:bg-warn/25 text-warn border border-warn/30 transition-all"
              >
                إعادة إرسال الرمز
              </button>
            ) : null}

            <button
              type="submit"
              disabled={busy || !code.trim() || secondsLeft <= 0}
              className="px-5 py-2 rounded-lg bg-safe hover:bg-safe/90 text-white font-semibold text-xs transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-1.5"
            >
              {busy ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>...جارٍ التحقق</span>
                </>
              ) : (
                <>
                  <Icon name="check" size={14} />
                  <span>تأكيد واعتماد البريد</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

