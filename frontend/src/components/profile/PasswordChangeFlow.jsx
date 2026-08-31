import { useEffect, useState } from 'react'
import { profile as profileApi } from '../../api/endpoints.js'
import { containsNamePart } from './nameMatching.js'

export default function PasswordChangeFlow({ fullName, activeEditor, onActivate, onSuccess, onError }) {
  const [step, setStep] = useState('locked')
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [code, setCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [developmentCode, setDevelopmentCode] = useState('')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (activeEditor !== 'password' && step !== 'locked') {
      setStep('locked')
      setCode('')
      setNewPassword('')
      setDevelopmentCode('')
      setSecondsLeft(0)
    }
  }, [activeEditor, step])

  useEffect(() => {
    if (step !== 'verify' || secondsLeft <= 0) return undefined
    const timer = setInterval(() => setSecondsLeft((seconds) => seconds - 1), 1000)
    return () => clearInterval(timer)
  }, [step, secondsLeft])

  useEffect(() => {
    if (step === 'verify' && secondsLeft <= 0) {
      setStep('locked')
      setCode('')
      setNewPassword('')
    }
  }, [step, secondsLeft])

  async function requestCode() {
    setBusy(true)
    try {
      const response = await profileApi.requestPasswordCode()
      setSecondsLeft(response.expiresInSeconds || 120)
      setDevelopmentCode(response.developmentCode || '')
      setStep('verify')
      onSuccess(response.developmentCode
        ? `رمز التحقق للتجربة: ${response.developmentCode}`
        : 'تم إرسال رمز تحقق جديد')
    } catch {
      onError('تعذر إرسال رمز التحقق')
    } finally {
      setBusy(false)
    }
  }

  async function verifyCode(event) {
    event.preventDefault()
    if (newPassword.length < 5) {
      onError('كلمة المرور يجب أن تحتوي على 5 أحرف على الأقل')
      return
    }
    if (containsNamePart(newPassword, fullName)) {
      onError('كلمة المرور يجب ألا تحتوي على اسم المستخدم')
      return
    }
    setBusy(true)
    try {
      await profileApi.verifyPasswordCode(code, newPassword)
      setStep('locked')
      setCode('')
      setNewPassword('')
      setDevelopmentCode('')
      setSecondsLeft(0)
      onSuccess('تم تغيير كلمة المرور بنجاح')
    } catch (error) {
      onError(error.message || 'تعذر تغيير كلمة المرور')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="field">
      <span className="field-label">كلمة المرور</span>
      {step === 'locked' && (
        <div className="field-value-row">
          <span className="field-value-text">*********</span>
          <button type="button" className="field-icon-btn" onClick={() => {
            onActivate()
            setStep('request')
          }} title="تعديل">
            ✎
          </button>
        </div>
      )}

      {step === 'request' && (
        <div className="password-flow">
          <button type="button" className="save-btn" disabled={busy} onClick={requestCode}>
            {busy ? '...جارٍ الإرسال' : 'طلب رمز التحقق'}
          </button>
        </div>
      )}

      {step === 'verify' && (
        <form className="password-flow" onSubmit={verifyCode}>
          <span className="password-countdown">الوقت المتبقي: {secondsLeft} ثانية</span>
          {developmentCode && (
            <span className="development-code">رمز التحقق: {developmentCode}</span>
          )}
          <input
            className="field-input password-flow-input"
            value={code}
            inputMode="numeric"
            maxLength={6}
            placeholder="رمز التحقق"
            onChange={(event) => setCode(event.target.value)}
            required
          />
          <input
            className="field-input password-flow-input"
            value={newPassword}
            type="password"
            placeholder="كلمة المرور الجديدة"
            onChange={(event) => setNewPassword(event.target.value)}
            required
          />
          <button type="submit" className="save-btn" disabled={busy || secondsLeft <= 0}>
            {busy ? '...جارٍ التأكيد' : 'تأكيد'}
          </button>
        </form>
      )}
    </div>
  )
}
