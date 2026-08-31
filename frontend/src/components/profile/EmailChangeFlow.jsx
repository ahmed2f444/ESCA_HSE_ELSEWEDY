import { useEffect, useState } from 'react'
import { profile as profileApi } from '../../api/endpoints.js'

export default function EmailChangeFlow({ value, activeEditor, onActivate, onChanged, onSuccess, onError }) {
  const [step, setStep] = useState('locked')
  const [secondsLeft, setSecondsLeft] = useState(0)
  const [code, setCode] = useState('')
  const [newEmail, setNewEmail] = useState(value || '')
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    if (activeEditor !== 'email' && step !== 'locked') {
      setStep('locked')
      setCode('')
      setNewEmail(value || '')
      setSecondsLeft(0)
    }
  }, [activeEditor, step, value])

  useEffect(() => {
    if (step !== 'verify' || secondsLeft <= 0) return undefined
    const timer = setInterval(() => setSecondsLeft((seconds) => seconds - 1), 1000)
    return () => clearInterval(timer)
  }, [step, secondsLeft])

  useEffect(() => {
    if (step === 'verify' && secondsLeft <= 0) {
      setStep('locked')
      setCode('')
      setNewEmail(value || '')
    }
  }, [step, secondsLeft, value])

  async function requestCode() {
    setBusy(true)
    try {
      const response = await profileApi.requestEmailCode()
      setSecondsLeft(response.expiresInSeconds || 120)
      setStep('verify')
      onSuccess('تم إرسال رمز تحقق جديد')
    } catch {
      onError('تعذر إرسال رمز التحقق')
    } finally {
      setBusy(false)
    }
  }

  async function verifyCode(event) {
    event.preventDefault()
    const email = newEmail.trim().toLowerCase()
    if (email.length < 5) {
      onError('البريد الإلكتروني يجب أن يحتوي على 5 أحرف على الأقل')
      return
    }
    if (!/^[^\s@]+@esca\.local$/.test(email)) {
      onError('يجب أن ينتهي البريد الإلكتروني بـ @esca.local')
      return
    }
    setBusy(true)
    try {
      const fresh = await profileApi.verifyEmailCode(code, newEmail)
      onChanged(fresh)
      setStep('locked')
      setCode('')
      setSecondsLeft(0)
      onSuccess('تم تغيير البريد الإلكتروني بنجاح')
    } catch (error) {
      onError(error.message || 'تعذر تغيير البريد الإلكتروني')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="field field-row-full">
      <span className="field-label">البريد الإلكتروني</span>
      {step === 'locked' && (
        <div className="field-value-row">
          <span className="field-value-text">{value}</span>
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
          <input
            className="field-input password-flow-input"
            value={newEmail}
            type="email"
            placeholder="البريد الإلكتروني الجديد"
            onChange={(event) => setNewEmail(event.target.value)}
            required
          />
          <button type="button" className="save-btn" disabled={busy} onClick={requestCode}>
            {busy ? '...جارٍ الإرسال' : 'طلب رمز التحقق'}
          </button>
        </div>
      )}
      {step === 'verify' && (
        <form className="password-flow" onSubmit={verifyCode}>
          <span className="password-countdown">الوقت المتبقي: {secondsLeft} ثانية</span>
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
            value={newEmail}
            type="email"
            placeholder="البريد الإلكتروني الجديد"
            onChange={(event) => setNewEmail(event.target.value)}
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
