import { useEffect, useState } from 'react'
import { profile as profileApi } from '../../api/endpoints.js'
import { containsNamePart } from './nameMatching.js'
import Icon from '../Icon.jsx'

export default function PasswordChangeFlow({
  fullName,
  activeEditor,
  onActivate,
  onDeactivate,
  onSuccess,
  onError,
}) {
  const [step, setStep] = useState('locked') // 'locked' | 'request' | 'verify'
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [developmentCode, setDevelopmentCode] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (activeEditor !== 'password' && step !== 'locked') {
      setStep('locked')
      setCode('')
      setNewPassword('')
      setConfirmPassword('')
      setDevelopmentCode('')
      setSecondsLeft(0)
    }
  }, [activeEditor, step])

  useEffect(() => {
    if (step !== 'verify' || secondsLeft <= 0) return undefined
    const timer = setInterval(() => setSecondsLeft((s) => s - 1), 1000)
    return () => clearInterval(timer)
  }, [step, secondsLeft])

  function handleCancel() {
    setStep('locked')
    setCode('')
    setNewPassword('')
    setConfirmPassword('')
    setSecondsLeft(0)
    setDevelopmentCode('')
    onDeactivate?.()
  }

  async function handleRequestCode() {
    setBusy(true)
    try {
      const response = await profileApi.requestPasswordCode()
      setSecondsLeft(response.expiresInSeconds || 120)
      setDevelopmentCode(response.developmentCode || '')
      setStep('verify')
      onSuccess(response.developmentCode
        ? `رمز التحقق التجريبي: ${response.developmentCode}`
        : 'تم إرسال رمز التحقق الأمني بنجاح')
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
    if (newPassword.length < 5) {
      onError('كلمة المرور يجب أن تحتوي على 5 أحرف على الأقل')
      return
    }
    if (confirmPassword && newPassword !== confirmPassword) {
      onError('كلمتا المرور غير متطابقتين')
      return
    }
    if (containsNamePart(newPassword, fullName)) {
      onError('كلمة المرور يجب ألا تحتوي على اسم المستخدم أو جزء منه لأسباب أمنية')
      return
    }

    setBusy(true)
    try {
      await profileApi.verifyPasswordCode(code.trim(), newPassword)
      setStep('locked')
      setCode('')
      setNewPassword('')
      setConfirmPassword('')
      setDevelopmentCode('')
      setSecondsLeft(0)
      onDeactivate?.()
      onSuccess('تم تحديث كلمة المرور بنجاح')
    } catch (error) {
      onError(error.message || 'تعذر تغيير كلمة المرور — تأكد من صحة الرمز')
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
          <Icon name="lock" size={14} className="text-txt-3" />
          <span>كلمة المرور والحماية</span>
        </label>
        <span className="inline-flex items-center gap-1 text-[10px] font-mono px-2 py-0.5 rounded-full bg-steel-3 text-txt-3 border border-line/50">
          <Icon name="shield-check" size={11} className="text-safe" />
          <span>مشفرة بنظام SHA-256</span>
        </span>
      </div>

      {/* Locked State: Display Row */}
      {step === 'locked' && (
        <div className="group relative rounded-xl border border-line/70 hover:border-line bg-steel-3/50 hover:bg-steel-3/80 transition-all duration-200">
          <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 min-h-[44px]">
            <span className="text-sm font-mono tracking-widest text-txt-3 select-none">
              ••••••••••••••••
            </span>
            <button
              type="button"
              onClick={() => {
                onActivate()
                setStep('request')
              }}
              className="p-1.5 rounded-lg text-txt-3 hover:text-hi2 hover:bg-steel-2/90 transition-all duration-150 active:scale-90 border border-transparent hover:border-line/50"
              title="تغيير كلمة المرور"
            >
              <Icon name="edit" size={14} />
            </button>
          </div>
        </div>
      )}

      {/* Step 1: Request MFA Code */}
      {step === 'request' && (
        <div className="p-4 rounded-xl border border-hi/40 bg-steel-2 shadow-lg animate-fade flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-bold text-txt">الخطوة 1: طلب رمز التحقق الأمني (MFA)</span>
            <button
              type="button"
              onClick={handleCancel}
              className="text-txt-3 hover:text-txt p-1 rounded hover:bg-steel-3"
            >
              <Icon name="x" size={15} />
            </button>
          </div>

          <p className="text-xs text-txt-2 leading-relaxed">
            لحماية حسابك وبيانات المنشأة، يتطلب تغيير كلمة المرور إصدار رمز تحقق أمني لمرة واحدة (OTP) يتم إرساله إلى وسيلة الاتصال المعتمدة لديك.
          </p>

          <div className="flex items-center justify-end gap-2 pt-1">
            <button
              type="button"
              onClick={handleCancel}
              className="px-3 py-1.5 rounded-lg text-xs font-medium text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors"
            >
              إلغاء
            </button>
            <button
              type="button"
              disabled={busy}
              onClick={handleRequestCode}
              className="px-4 py-2 rounded-lg bg-hi hover:bg-hi2 text-hi-txt font-semibold text-xs transition-all active:scale-95 disabled:opacity-50 shadow-sm flex items-center gap-1.5"
            >
              {busy ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>...جارٍ إرسال الرمز</span>
                </>
              ) : (
                <>
                  <Icon name="key" size={13} />
                  <span>إرسال رمز التحقق (OTP)</span>
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Step 2: Verify Code & Set New Password */}
      {step === 'verify' && (
        <form
          onSubmit={handleVerify}
          className="p-4 rounded-xl border border-safe/40 bg-steel-2 shadow-lg animate-fade flex flex-col gap-3"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-txt">الخطوة 2: إدخال الرمز وكلمة المرور الجديدة</span>
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

          <div className="flex flex-col gap-1">
            <span className="text-[11px] text-txt-3">رمز التحقق الأمني (6 أرقام):</span>
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

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
            <div className="flex flex-col gap-1">
              <div className="flex items-center justify-between">
                <span className="text-[11px] text-txt-3">كلمة المرور الجديدة:</span>
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="text-txt-3 hover:text-txt text-[10px] flex items-center gap-1"
                >
                  <Icon name={showPassword ? 'eye-off' : 'eye'} size={12} />
                  <span>{showPassword ? 'إخفاء' : 'إظهار'}</span>
                </button>
              </div>
              <input
                type={showPassword ? 'text' : 'password'}
                dir="ltr"
                value={newPassword}
                placeholder="••••••••"
                onChange={(e) => setNewPassword(e.target.value)}
                className="bg-steel-3 border border-line focus:border-hi text-txt rounded-lg px-3 py-2 text-sm font-mono outline-none"
                required
              />
            </div>

            <div className="flex flex-col gap-1">
              <span className="text-[11px] text-txt-3">تأكيد كلمة المرور:</span>
              <input
                type={showPassword ? 'text' : 'password'}
                dir="ltr"
                value={confirmPassword}
                placeholder="••••••••"
                onChange={(e) => setConfirmPassword(e.target.value)}
                className={`bg-steel-3 border text-txt rounded-lg px-3 py-2 text-sm font-mono outline-none ${
                  confirmPassword && confirmPassword !== newPassword
                    ? 'border-crit focus:border-crit'
                    : 'border-line focus:border-safe'
                }`}
                required
              />
            </div>
          </div>

          {/* Password Quality Tips */}
          <div className="flex items-center justify-between text-[11px] text-txt-3 px-0.5">
            <span>5 أحرف على الأقل — يجب ألا تحتوي على اسمك</span>
            {confirmPassword && confirmPassword === newPassword && (
              <span className="text-safe flex items-center gap-1 font-semibold">
                <Icon name="check" size={12} /> متطابقة
              </span>
            )}
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
              disabled={busy || !code.trim() || newPassword.length < 5 || secondsLeft <= 0}
              className="px-5 py-2 rounded-lg bg-safe hover:bg-safe/90 text-white font-semibold text-xs transition-all active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm flex items-center gap-1.5"
            >
              {busy ? (
                <>
                  <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>...جارٍ التحديث</span>
                </>
              ) : (
                <>
                  <Icon name="check" size={14} />
                  <span>تأكيد كلمة المرور الجديدة</span>
                </>
              )}
            </button>
          </div>
        </form>
      )}
    </div>
  )
}

