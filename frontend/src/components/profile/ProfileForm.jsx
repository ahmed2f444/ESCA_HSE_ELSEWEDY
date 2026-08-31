import { useEffect, useState } from 'react'
import { profile as profileApi } from '../../api/endpoints.js'
import ProfileField from './ProfileField.jsx'
import AvatarUpload from './AvatarUpload.jsx'
import PasswordChangeFlow from './PasswordChangeFlow.jsx'
import EmailChangeFlow from './EmailChangeFlow.jsx'
import { useTheme } from '../../theme.jsx'

const EDITABLE_FIELDS = ['full_name', 'username']

function looksLikeRandomArabicPart(part) {
  if (!/^[\u0600-\u06FF]+$/.test(part) || part.length < 6) return false
  const counts = new Map()
  for (const character of part) {
    counts.set(character, (counts.get(character) || 0) + 1)
  }
  return Math.max(...counts.values()) >= 3
}

/**
 * Theme-agnostic profile page. Layout/structure only — colors come from
 * whichever of styles/dark/profile.css or styles/light/profile.css is
 * loaded, selected via the `theme-dark` / `theme-light` class below.
 *
 * Layout follows the user's hand-drawn sketch exactly:
 *   1. avatar (edit icon on its corner, uploads/removes immediately)
 *   2. email (full width row)
 *   3. two columns:
 *        left:  full name, username, password
 *        right: job title (read-only), phone, zone (read-only), department (read-only)
 *   4. one shared Save button, centered, bottom — commits every unlocked
 *      field at once (per-field edit icons only UNLOCK a field, they do
 *      not save individually — matches the sketch, which has both).
 */
export default function ProfileForm() {
  const { mode } = useTheme()
  const [data, setData] = useState(null) // last saved/fetched record
  const [draft, setDraft] = useState({}) // in-progress edits, keyed by field
  const [unlocked, setUnlocked] = useState({}) // which fields are currently editable
  const [activeEditor, setActiveEditor] = useState(null)
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null) // { type: 'success' | 'error', text }
  const [loadError, setLoadError] = useState(false)

  useEffect(() => {
    profileApi.get()
      .then((fresh) => {
        setData(fresh)
        setDraft(fresh)
      })
      .catch(() => setLoadError(true))
  }, [])

  function showStatus(type, text) {
    setStatus({ type, text })
    setTimeout(() => setStatus(null), 3000)
  }

  function unlockField(field) {
    setActiveEditor(field)
    setUnlocked({ [field]: true })
  }

  function handlePageClick(event) {
    if (!event.target.closest('.field')) {
      setActiveEditor(null)
      setUnlocked({})
    }
  }

  function changeField(field, value) {
    setDraft((d) => ({ ...d, [field]: value }))
  }

  const hasChanges = EDITABLE_FIELDS.some((f) => unlocked[f])

  // Per the data-integrity rule: after saving, replace local state with the
  // FRESH record returned by the API — never trust what the user typed as
  // the new source of truth, always re-sync from the server's response.
  async function handleSave() {
    setSaving(true)
    try {
      const changedFields = {}
      EDITABLE_FIELDS.forEach((f) => {
        if (unlocked[f] && draft[f] !== data[f]) changedFields[f] = draft[f]
      })
      for (const field of EDITABLE_FIELDS) {
        if (unlocked[field] && String(draft[field] || '').trim() === String(data[field] || '').trim()) {
          showStatus('error', field === 'username'
            ? 'اسم المستخدم مستخدم بالفعل'
            : 'يرجى اختيار اسم مستخدم مختلف')
          setSaving(false)
          return
        }
      }
      const requiredFields = {
        full_name: 'يجب كتابة الاسم الأول واسم العائلة مفصولين بمسافة',
        username: 'اسم المستخدم لا يمكن أن يكون فارغاً',
      }
      if (Object.prototype.hasOwnProperty.call(changedFields, 'full_name')
        && changedFields.full_name.trim().length < 8) {
        showStatus('error', 'يجب كتابة الاسم الأول واسم العائلة مفصولين بمسافة')
        setSaving(false)
        return
      }
      if (Object.prototype.hasOwnProperty.call(changedFields, 'full_name')
        && !/^\p{L}+(?: \p{L}+)*$/u.test(changedFields.full_name)) {
        showStatus('error', 'يجب كتابة الاسم الأول واسم العائلة مفصولين بمسافة')
        setSaving(false)
        return
      }
      if (Object.prototype.hasOwnProperty.call(changedFields, 'full_name')
        && changedFields.full_name.trim().split(' ').some((part) => (
          /^[A-Za-z]+$/.test(part)
          && /[A-Z]/.test(part)
          && !/^[A-Z][a-z]+$/.test(part)
        ))) {
        showStatus('error', 'عند استخدام الحروف الكبيرة يجب أن يكون الحرف الأول فقط كبيراً')
        setSaving(false)
        return
      }
      if (Object.prototype.hasOwnProperty.call(changedFields, 'full_name')) {
        const nameParts = changedFields.full_name.trim().split(' ')
        const currentNameParts = String(data.full_name || '').trim().split(/\s+/)
        const matchingCurrentParts = nameParts.filter((part) => currentNameParts.some(
          (currentPart) => part.toLowerCase() === currentPart.toLowerCase(),
        )).length
        const hasSuspiciousPart = nameParts.some((part) => {
          const hasOnlyOneCharacter = [...part].every((character) => character === part[0])
          const isLatinPart = /^[A-Za-z]+$/.test(part)
          const isRandomArabicPart = looksLikeRandomArabicPart(part)
          const hasConsonantSequence = isLatinPart
            && /[B-DF-HJ-NP-TV-Zb-df-hj-np-tv-z]{3,}/.test(part)
          const hasNoVowel = isLatinPart && part.length >= 4 && !/[AEIOUYaeiouy]/.test(part)
          const extendsCurrentNamePart = currentNameParts.some((currentPart) => (
            part.toLowerCase() !== currentPart.toLowerCase()
            && part.toLowerCase().includes(currentPart.toLowerCase())
          ))
          return hasOnlyOneCharacter || isRandomArabicPart || hasConsonantSequence
            || hasNoVowel || extendsCurrentNamePart
        })
        const keepsOnlyOneCurrentPart = matchingCurrentParts === 1
          && currentNameParts.length > 1 && nameParts.length > 1
        if (nameParts.length < 2 || nameParts.some((part) => part.length < 2)
          || hasSuspiciousPart || keepsOnlyOneCurrentPart) {
          showStatus('error', 'يجب كتابة الاسم الأول واسم العائلة مفصولين بمسافة')
          setSaving(false)
          return
        }
      }
      for (const [field, message] of Object.entries(requiredFields)) {
        if (Object.prototype.hasOwnProperty.call(changedFields, field)
          && !String(changedFields[field] || '').trim()) {
          showStatus('error', message)
          setSaving(false)
          return
        }
      }

      let fresh = data
      if (Object.keys(changedFields).length > 0) {
        fresh = await profileApi.update(changedFields)
      }

      setData(fresh)
      setDraft(fresh)
      setUnlocked({})
      showStatus('success', 'تم حفظ التغييرات بنجاح')
    } catch (err) {
      showStatus('error', err.message || 'حدث خطأ أثناء الحفظ')
    } finally {
      setSaving(false)
    }
  }

  async function handleAvatarUpload(file, previewUrl) {
    const previousAvatar = data.avatar_path
    if (file.size > 20 * 1024 * 1024) {
      showStatus('error', 'حجم الصورة أكبر من الحد المسموح به (20 ميجابايت)')
      return
    }
    setData((current) => ({ ...current, avatar_path: previewUrl }))
    try {
      const fresh = await profileApi.uploadAvatar(file)
      setData(fresh)
      setDraft(fresh)
      showStatus('success', 'تم تحديث الصورة')
    } catch (err) {
      setData((current) => ({ ...current, avatar_path: previousAvatar }))
      showStatus('error', err.name === 'AbortError' ? 'استغرق رفع الصورة وقتاً طويلاً' : (err.message || 'تعذر رفع الصورة'))
    }
  }

  async function handleAvatarRemove() {
    try {
      const fresh = await profileApi.deleteAvatar()
      setData(fresh)
      setDraft(fresh)
      showStatus('success', 'تم حذف الصورة')
    } catch (err) {
      showStatus('error', err.message === 'Failed to fetch' ? 'تعذر الاتصال بالخادم' : (err.message || 'تعذر حذف الصورة'))
    }
  }

  if (!data) {
    return (
      <div className="profile-page" onClick={handlePageClick}>
        <p>{loadError ? 'تعذر الاتصال بالخادم' : '...جارٍ التحميل'}</p>
      </div>
    )
  }

  return (
    <div className={`profile-page theme-${mode}`} onClick={handlePageClick}>
      <div className="profile-heading">
        <span className="profile-title">الملف الشخصي</span>
      </div>

      <div className="profile-card">
        <AvatarUpload
          avatarPath={data.avatar_path}
          onUpload={handleAvatarUpload}
          onRemove={handleAvatarRemove}
        />

        <EmailChangeFlow
          value={data.email}
          activeEditor={activeEditor}
          onActivate={() => {
            setActiveEditor('email')
            setUnlocked({})
          }}
          onChanged={(fresh) => {
            setData(fresh)
            setDraft(fresh)
          }}
          onSuccess={(message) => showStatus('success', message)}
          onError={(message) => showStatus('error', message)}
        />

        <div className="field-grid">
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <ProfileField
              label="الاسم الكامل"
              value={draft.full_name}
              unlocked={!!unlocked.full_name}
              onUnlock={() => unlockField('full_name')}
              onChange={(v) => changeField('full_name', v)}
            />
            <ProfileField
              label="اسم المستخدم"
              value={draft.username}
              unlocked={!!unlocked.username}
              onUnlock={() => unlockField('username')}
              onChange={(v) => changeField('username', v)}
            />
            <PasswordChangeFlow
              fullName={data.full_name}
              activeEditor={activeEditor}
              onActivate={() => {
                setActiveEditor('password')
                setUnlocked({})
              }}
              onSuccess={(message) => showStatus('success', message)}
              onError={(message) => showStatus('error', message)}
            />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
            <ProfileField label="المسمى الوظيفي" value={data.job_title} editable={false} />
            <ProfileField
              label="رقم الهاتف"
              value={data.phone}
              editable={false}
            />
            <ProfileField label="المنطقة" value={data.zone_name} editable={false} />
            <ProfileField label="القسم" value={data.department_name} editable={false} />
          </div>
        </div>

        <div className="save-btn-row">
          <button type="button" className="save-btn" disabled={!hasChanges || saving} onClick={handleSave}>
            {saving ? '...جارٍ الحفظ' : 'حفظ'}
          </button>
        </div>

        {status && <p className={`status-msg ${status.type}`}>{status.text}</p>}
      </div>
    </div>
  )
}
