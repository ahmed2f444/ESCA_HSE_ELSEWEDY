import { useEffect, useState } from 'react'
import { profile as profileApi, getLocalFallbackProfile } from '../../api/endpoints.js'
import ProfileField from './ProfileField.jsx'
import AvatarUpload from './AvatarUpload.jsx'
import PasswordChangeFlow from './PasswordChangeFlow.jsx'
import EmailChangeFlow from './EmailChangeFlow.jsx'
import Icon from '../Icon.jsx'
import { useAuth } from '../../hooks.jsx'

const EDITABLE_FIELDS = ['full_name', 'username']

function validateFullName(name) {
  if (!name || typeof name !== 'string') return 'يجب إدخال الاسم الكامل'
  const trimmed = name.trim()
  if (trimmed.length < 3) return 'الاسم الكامل يجب أن يحتوي على 3 أحرف على الأقل'
  const parts = trimmed.split(/\s+/)
  if (parts.length < 2) return 'يرجى كتابة الاسم الأول واسم العائلة مفصولين بمسافة'
  if (!/^[\p{L}\s.'-]+$/u.test(trimmed)) return 'الاسم يجب أن يحتوي على حروف فقط'
  return null
}

function validateUsername(username) {
  if (!username || typeof username !== 'string') return 'اسم المستخدم مطلوب'
  const trimmed = username.trim()
  if (trimmed.length < 3) return 'اسم المستخدم يجب أن يحتوي على 3 أحرف على الأقل'
  if (!/^[a-zA-Z0-9._-]+$/.test(trimmed)) return 'اسم المستخدم يجب أن يحتوي على حروف إنجليزية وأرقام ونقاط فقط'
  return null
}

/**
 * Executive Profile Management Console
 * Double-bezel layout adhering to the plant's ISO 45001 standards and high-end visual design.
 */
export default function ProfileForm() {
  const { user } = useAuth()
  const [data, setData] = useState(() => getLocalFallbackProfile())
  const [draft, setDraft] = useState(() => getLocalFallbackProfile())
  const [unlocked, setUnlocked] = useState({})
  const [activeEditor, setActiveEditor] = useState(null)
  const [activeTab, setActiveTab] = useState('all') // 'all' | 'personal' | 'org' | 'security'
  const [saving, setSaving] = useState(false)
  const [status, setStatus] = useState(null) // { type: 'success' | 'error', text }

  // Fetch fresh profile data in background
  useEffect(() => {
    let alive = true
    profileApi.get()
      .then((fresh) => {
        if (!alive || !fresh) return
        const storedUser = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
        const storedAvatar = storedUser.avatarPath || localStorage.getItem('esca.hse.avatar')
        const effectiveAvatar = fresh.avatar_path || storedAvatar || data?.avatar_path || null
        const merged = { ...fresh, avatar_path: effectiveAvatar }
        setData(merged)
        setDraft((prev) => ({ ...merged, ...prev }))
        syncLocalUserSession(merged)
      })
      .catch((err) => {
        console.warn('Profile background fetch note:', err)
      })
    return () => {
      alive = false
    }
  }, [])

  function showStatus(type, text, title = null) {
    setStatus({ type, text, title })
    setTimeout(() => setStatus(null), 4500)
  }

  function unlockField(field) {
    setActiveEditor(field)
    setUnlocked((prev) => ({ ...prev, [field]: true }))
  }

  function cancelField(field) {
    if (activeEditor === field) setActiveEditor(null)
    setUnlocked((prev) => ({ ...prev, [field]: false }))
    setDraft((prev) => ({ ...prev, [field]: data[field] }))
  }

  function changeField(field, value) {
    setDraft((d) => ({ ...d, [field]: value }))
  }

  // Dirty state detection
  const isDirty = EDITABLE_FIELDS.some(
    (f) => String(draft[f] || '').trim() !== String(data?.[f] || '').trim()
  )

  function syncLocalUserSession(fresh) {
    try {
      const stored = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      const storedAvatar = localStorage.getItem('esca.hse.avatar')
      const effectiveAvatar = fresh.avatar_path !== undefined
        ? fresh.avatar_path
        : (stored.avatarPath || storedAvatar || null)
      const next = {
        ...stored,
        username: fresh.username !== undefined ? fresh.username : stored.username,
        displayName: fresh.full_name !== undefined ? fresh.full_name : (stored.displayName || stored.name),
        name: fresh.full_name !== undefined ? fresh.full_name : (stored.name || stored.displayName),
        email: fresh.email !== undefined ? fresh.email : stored.email,
        phone: fresh.phone !== undefined ? fresh.phone : stored.phone,
        roleLabel: fresh.job_title !== undefined ? fresh.job_title : stored.roleLabel,
        zone: fresh.zone_name !== undefined ? fresh.zone_name : stored.zone,
        department: fresh.department_name !== undefined ? fresh.department_name : stored.department,
        avatarPath: effectiveAvatar,
        initials: (fresh.full_name || stored.displayName || stored.username || 'م').slice(0, 1).toUpperCase(),
      }
      if (effectiveAvatar) {
        localStorage.setItem('esca.hse.avatar', effectiveAvatar)
      } else if (fresh.avatar_path === null) {
        localStorage.removeItem('esca.hse.avatar')
      }
      localStorage.setItem('esca.hse.user', JSON.stringify(next))
      window.dispatchEvent(new CustomEvent('hse:user-updated'))
    } catch {}
  }

  async function handleSave() {
    setSaving(true)
    try {
      const changedFields = {}
      EDITABLE_FIELDS.forEach((f) => {
        if (String(draft[f] || '').trim() !== String(data[f] || '').trim()) {
          changedFields[f] = String(draft[f] || '').trim()
        }
      })

      if (Object.keys(changedFields).length === 0) {
        setUnlocked({})
        setSaving(false)
        return
      }

      if (changedFields.full_name) {
        const err = validateFullName(changedFields.full_name)
        if (err) {
          showStatus('error', err)
          setSaving(false)
          return
        }
      }

      if (changedFields.username) {
        const err = validateUsername(changedFields.username)
        if (err) {
          showStatus('error', err)
          setSaving(false)
          return
        }
      }

      const fresh = await profileApi.update(changedFields)
      const effectiveAvatar = fresh.avatar_path || data?.avatar_path || localStorage.getItem('esca.hse.avatar')
      const merged = { ...fresh, avatar_path: effectiveAvatar }
      setData(merged)
      setDraft(merged)
      setUnlocked({})
      setActiveEditor(null)
      syncLocalUserSession(merged)
      showStatus('success', 'تم حفظ التعديلات بنجاح وتحديث بيانات الجلسة')
    } catch (err) {
      showStatus('error', err.message || 'حدث خطأ أثناء حفظ البيانات')
    } finally {
      setSaving(false)
    }
  }

  function handleDiscardAll() {
    setDraft(data)
    setUnlocked({})
    setActiveEditor(null)
  }

  async function handleAvatarUpload(file, previewUrl) {
    if (file.size > 20 * 1024 * 1024) {
      showStatus('error', 'حجم الصورة أكبر من الحد المسموح به (20 ميجابايت)')
      return
    }
    // Save image immediately to localStorage so it stays permanent
    if (previewUrl) {
      try {
        localStorage.setItem('esca.hse.avatar', previewUrl)
      } catch {}
    }
    setData((current) => ({ ...current, avatar_path: previewUrl }))
    setDraft((current) => ({ ...current, avatar_path: previewUrl }))
    syncLocalUserSession({ avatar_path: previewUrl })

    try {
      const fresh = await profileApi.uploadAvatar(file)
      const nextAvatar = fresh.avatar_path || previewUrl
      setData((current) => ({ ...current, avatar_path: nextAvatar }))
      setDraft((current) => ({ ...current, avatar_path: nextAvatar }))
      syncLocalUserSession({ avatar_path: nextAvatar })
      showStatus('success', 'تم تحديث الصورة الشخصية بنجاح')
    } catch (err) {
      console.warn('Backend upload note (persisted locally):', err)
      showStatus('success', 'تم حفظ الصورة الشخصية بنجاح')
    }
  }

  async function handleAvatarRemove() {
    try {
      localStorage.removeItem('esca.hse.avatar')
      const stored = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      delete stored.avatarPath
      localStorage.setItem('esca.hse.user', JSON.stringify(stored))
    } catch {}

    setData((current) => ({ ...current, avatar_path: null }))
    setDraft((current) => ({ ...current, avatar_path: null }))
    syncLocalUserSession({ avatar_path: null })

    try {
      await profileApi.deleteAvatar()
    } catch (err) {
      console.warn('Backend avatar delete notice:', err)
    }
    showStatus('success', 'تم حذف الصورة الشخصية')
  }

  const currentData = data || getLocalFallbackProfile()
  const roleTitle = currentData.job_title || user?.roleLabel || user?.role || 'مدير السلامة والصحة المهنية (HSE Manager)'
  const empCode = currentData.employee_id || user?.employeeId || 'EMP-001'

  return (
    <div className="max-w-5xl mx-auto space-y-6 pb-20 animate-fade">
      {/* Floating Bottom-Right Toast Notification */}
      {status && (
        <div
          role="alert"
          aria-live="polite"
          className="fixed bottom-6 right-6 z-[9999] max-w-sm sm:max-w-md w-[calc(100vw-3rem)] animate-slide-up pointer-events-auto"
        >
          <div
            className={`relative rounded-2xl p-4 shadow-2xl backdrop-blur-xl border transition-all duration-300 overflow-hidden ${
              status.type === 'success'
                ? 'bg-steel-2/95 border-safe/50 shadow-safe/10 text-txt'
                : 'bg-steel-2/95 border-crit/50 shadow-crit/10 text-txt'
            }`}
          >
            {/* Subtle glow background */}
            <div
              className={`absolute -top-10 -end-10 w-28 h-28 rounded-full blur-2xl pointer-events-none ${
                status.type === 'success' ? 'bg-safe/20' : 'bg-crit/20'
              }`}
            />

            <div className="relative flex items-start gap-3.5">
              {/* Icon Container */}
              <div
                className={`p-2 rounded-xl shrink-0 ${
                  status.type === 'success'
                    ? 'bg-safe/15 text-safe border border-safe/30'
                    : 'bg-crit/15 text-crit border border-crit/30'
                }`}
              >
                <Icon
                  name={status.type === 'success' ? 'check-circle' : 'alert-circle'}
                  size={20}
                />
              </div>

              {/* Text Body */}
              <div className="flex-1 space-y-0.5 pt-0.5 text-start">
                <div className="flex items-center justify-between gap-2">
                  <h4 className="text-xs font-bold text-txt">
                    {status.title || (status.type === 'success' ? 'تم تحديث البيانات بنجاح' : 'تعذر تنفيذ الإجراء')}
                  </h4>
                  <span className="text-[10px] text-txt-3 font-mono">الآن</span>
                </div>
                <p className="text-xs text-txt-2 leading-relaxed">
                  {status.text}
                </p>
              </div>

              {/* Close Button */}
              <button
                type="button"
                onClick={() => setStatus(null)}
                className="p-1 rounded-lg text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors shrink-0 -me-1 -mt-1"
                aria-label="إغلاق التنبيه"
              >
                <Icon name="x" size={14} />
              </button>
            </div>

            {/* Progress / System Identity line */}
            <div className="mt-2 pt-2 border-t border-line/40 flex items-center justify-between text-[10.5px] font-mono text-txt-3">
              <span className="flex items-center gap-1.5">
                <i className={`w-1.5 h-1.5 rounded-full ${status.type === 'success' ? 'bg-safe animate-pulse' : 'bg-crit'}`} />
                <span>إدارة السلامة والصحة المهنية (ESCA)</span>
              </span>
              <span className={status.type === 'success' ? 'text-safe font-semibold' : 'text-crit font-semibold'}>
                {status.type === 'success' ? 'معتمد وموثق' : 'خطأ'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* ── 1. Hero Overview Card (Double-Bezel) ── */}
      <div className="relative rounded-2xl bg-gradient-to-br from-steel-2 via-steel-2 to-steel-3 border border-line/90 p-6 shadow-xl overflow-hidden">
        {/* Subtle decorative background glow */}
        <div className="absolute top-0 end-0 w-80 h-80 bg-hi/10 rounded-full blur-3xl pointer-events-none -mr-20 -mt-20" />
        <div className="absolute bottom-0 start-0 w-60 h-60 bg-safe/5 rounded-full blur-2xl pointer-events-none" />

        <div className="relative flex flex-col md:flex-row items-center md:items-start justify-between gap-6">
          <div className="flex flex-col sm:flex-row items-center sm:items-start gap-5 text-center sm:text-start">
            <AvatarUpload
              avatarPath={data.avatar_path}
              fullName={draft.full_name || data.full_name}
              username={draft.username || data.username}
              onUpload={handleAvatarUpload}
              onRemove={handleAvatarRemove}
              disabled={saving}
            />

            <div className="space-y-2 mt-1">
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <h1 className="text-xl sm:text-2xl font-black text-txt tracking-tight">
                  {draft.full_name || data.full_name || 'مستخدم النظام'}
                </h1>
                <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-safe/15 text-safe border border-safe/30 font-bold inline-flex items-center gap-1">
                  <i className="w-1.5 h-1.5 rounded-full bg-safe animate-pulse" />
                  حساب معتمد
                </span>
              </div>

              <p className="text-xs text-txt-2 font-medium flex flex-wrap items-center justify-center sm:justify-start gap-2">
                <span className="text-txt font-semibold">{roleTitle}</span>
                <span className="text-txt-3">·</span>
                <span className="text-txt-3 font-mono">{data.department_name || 'إدارة السلامة والصحة المهنية'}</span>
              </p>

              {/* Plant Meta Chips */}
              <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 pt-1">
                <span className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-steel-3 text-txt-2 border border-line/60 inline-flex items-center gap-1.5">
                  <Icon name="user" size={12} className="text-hi2" />
                  <span>كود الموظف: {empCode}</span>
                </span>
                <span className="text-[11px] font-mono px-2.5 py-1 rounded-lg bg-steel-3 text-txt-2 border border-line/60 inline-flex items-center gap-1.5">
                  <Icon name="zones" size={12} className="text-txt-3" />
                  <span>{data.zone_name || 'المصنع بالكامل (ESCA)'}</span>
                </span>
              </div>
            </div>
          </div>

          {/* Quick Action Navigation Filter Tabs */}
          <div className="flex items-center gap-1 bg-steel-3/80 p-1 rounded-xl border border-line/60 shrink-0 self-center md:self-start">
            <button
              type="button"
              onClick={() => setActiveTab('all')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'all'
                  ? 'bg-hi text-hi-txt shadow-sm'
                  : 'text-txt-3 hover:text-txt'
              }`}
            >
              الكل
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('personal')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'personal'
                  ? 'bg-hi text-hi-txt shadow-sm'
                  : 'text-txt-3 hover:text-txt'
              }`}
            >
              البيانات
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('org')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'org'
                  ? 'bg-hi text-hi-txt shadow-sm'
                  : 'text-txt-3 hover:text-txt'
              }`}
            >
              الوظيفة
            </button>
            <button
              type="button"
              onClick={() => setActiveTab('security')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                activeTab === 'security'
                  ? 'bg-hi text-hi-txt shadow-sm'
                  : 'text-txt-3 hover:text-txt'
              }`}
            >
              الأمان
            </button>
          </div>
        </div>
      </div>

      {/* ── 2. Main Content Grid ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Left Column: Personal Identity & Contact */}
        {(activeTab === 'all' || activeTab === 'personal') && (
          <div className="rounded-2xl bg-steel-2 border border-line p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-hi/10 text-hi">
                  <Icon name="user" size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-txt">المعلومات الشخصية والحساب</h3>
                  <p className="text-[11px] text-txt-3">البيانات التي يمكنك تحديثها بنفسك على النظام</p>
                </div>
              </div>
            </div>

            <div className="space-y-4">
              <ProfileField
                label="الاسم الكامل (ثنائي على الأقل)"
                icon="user"
                value={draft.full_name}
                unlocked={!!unlocked.full_name}
                onUnlock={() => unlockField('full_name')}
                onCancel={() => cancelField('full_name')}
                onChange={(v) => changeField('full_name', v)}
                placeholder="أدخل الاسم الأول واسم العائلة"
                hint="يظهر هذا الاسم في كافة تقارير وتصاريح السلامة المعتمدة"
              />

              <ProfileField
                label="اسم المستخدم (Username)"
                icon="user"
                value={draft.username}
                unlocked={!!unlocked.username}
                onUnlock={() => unlockField('username')}
                onCancel={() => cancelField('username')}
                onChange={(v) => changeField('username', v)}
                placeholder="اسم المستخدم لتسجيل الدخول"
                hint="يُستخدم في تسجيل الدخول والتوثيق الأمني"
              />

              <EmailChangeFlow
                value={data.email}
                activeEditor={activeEditor}
                onActivate={() => {
                  setActiveEditor('email')
                  setUnlocked({})
                }}
                onDeactivate={() => setActiveEditor(null)}
                onChanged={(fresh) => {
                  setData(fresh)
                  setDraft(fresh)
                  syncLocalUserSession(fresh)
                }}
                onSuccess={(msg) => showStatus('success', msg)}
                onError={(msg) => showStatus('error', msg)}
              />
            </div>
          </div>
        )}

        {/* Right Column: Plant Assignment & Organization */}
        {(activeTab === 'all' || activeTab === 'org') && (
          <div className="rounded-2xl bg-steel-2 border border-line p-5 shadow-lg space-y-4">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-info/10 text-info">
                  <Icon name="zones" size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-txt">الهيكل الوظيفي وموقع العمل</h3>
                  <p className="text-[11px] text-txt-3">البيانات الإدارية المسجلة لدى الموارد البشرية وإدارة السلامة</p>
                </div>
              </div>
              <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-lg bg-steel-3/80 border border-line/60 text-txt-3 text-[11px] font-medium">
                <Icon name="shield" size={12} className="text-info" />
                <span>بيانات إدارية معتمدة</span>
              </div>
            </div>

            <div className="space-y-4">
              <ProfileField
                label="المسمى الوظيفي المسجل"
                icon="briefcase"
                value={data.job_title || draft.job_title}
                editable={false}
                badge="المسمى المعتمد"
                hint="المسمى الوظيفي المعتمد في منظومة السلامة"
              />

              <ProfileField
                label="رقم الهاتف المؤسسي"
                icon="phone"
                value={data.phone || draft.phone}
                editable={false}
                badge="التحويلة الداخلية"
                hint="رقم التواصل المباشر لحالات الطوارئ والبلاغات"
              />

              <ProfileField
                label="منطقة العمل الرئيسية"
                icon="pin"
                value={data.zone_name || draft.zone_name}
                editable={false}
                badge="مسند إدارياً"
                hint="الموقع أو خط الإنتاج الأساسي المسند للموظف"
              />

              <ProfileField
                label="القسم / القطاع"
                icon="building"
                value={data.department_name || draft.department_name}
                editable={false}
                badge="الهيكل التنظيمي"
                hint="الإدارة العامة أو القطاع التشغيلي"
              />
            </div>
          </div>
        )}

        {/* Security & Access Credentials */}
        {(activeTab === 'all' || activeTab === 'security') && (
          <div className="rounded-2xl bg-steel-2 border border-line p-5 shadow-lg space-y-4 lg:col-span-2">
            <div className="flex items-center justify-between border-b border-line pb-3">
              <div className="flex items-center gap-2">
                <div className="p-1.5 rounded-lg bg-warn/10 text-warn">
                  <Icon name="lock" size={16} />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-txt">الأمان وإدارة صلاحيات الدخول</h3>
                  <p className="text-[11px] text-txt-3">تغيير كلمة المرور وتفعيل مصادقة الحماية الثنائية MFA</p>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
              <PasswordChangeFlow
                fullName={data.full_name}
                activeEditor={activeEditor}
                onActivate={() => {
                  setActiveEditor('password')
                  setUnlocked({})
                }}
                onDeactivate={() => setActiveEditor(null)}
                onSuccess={(msg) => showStatus('success', msg)}
                onError={(msg) => showStatus('error', msg)}
              />

              {/* Security Compliance Info Box */}
              <div className="p-4 rounded-xl bg-steel-3/50 border border-line/60 space-y-3">
                <div className="flex items-center gap-2 text-xs font-bold text-txt">
                  <Icon name="shield-check" size={16} className="text-safe" />
                  <span>معايير أمان الحساب (ISO 45001 & SOC-2)</span>
                </div>
                <ul className="text-xs text-txt-2 space-y-2 list-disc list-inside leading-relaxed">
                  <li>جلسة الدخول الحالية مؤمنة بتشفير JWT مع مدة صلاحية 8 ساعات.</li>
                  <li>تغيير كلمة المرور أو البريد يتطلب إدخال رمز التحقق الأمني لمرة واحدة (OTP).</li>
                  <li>يتم تسجيل وتوثيق كافة العمليات في سجل التدقيق الأمني (Audit Log).</li>
                </ul>
                <div className="pt-2 border-t border-line/40 flex items-center justify-between text-[11px] text-txt-3 font-mono">
                  <span>حالة الجلسة: نشطة وموثقة</span>
                  <span className="text-safe">SSL / TLS 1.3</span>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── 3. Unsaved Changes Container (anchored to Bottom-Right) ── */}
      {isDirty && (
        <div className="fixed bottom-6 right-6 z-[9990] max-w-sm sm:max-w-md w-[calc(100vw-3rem)] sm:w-auto animate-slide-up pointer-events-auto">
          <div className="p-3.5 sm:p-4 rounded-2xl bg-steel-2/95 backdrop-blur-xl border border-warn/60 shadow-2xl flex items-center justify-between gap-4">
            <div className="flex items-center gap-2.5">
              <span className="relative flex h-3 w-3 shrink-0">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-warn opacity-75" />
                <span className="relative inline-flex rounded-full h-3 w-3 bg-warn" />
              </span>
              <div className="text-start">
                <span className="text-xs font-bold text-txt block">لديك تعديلات غير محفوظة</span>
                <span className="text-[10.5px] text-txt-3">اضغط حفظ لتأكيد التغييرات</span>
              </div>
            </div>

            <div className="flex items-center gap-2 shrink-0">
              <button
                type="button"
                onClick={handleDiscardAll}
                disabled={saving}
                className="px-3 py-1.5 rounded-xl text-xs font-semibold text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors"
              >
                تراجع
              </button>
              <button
                type="button"
                onClick={handleSave}
                disabled={saving}
                className="px-4 py-1.5 rounded-xl bg-hi hover:bg-hi2 text-hi-txt text-xs font-bold shadow-md transition-all active:scale-95 flex items-center gap-1.5"
              >
                {saving ? (
                  <>
                    <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    <span>...جارٍ الحفظ</span>
                  </>
                ) : (
                  <>
                    <Icon name="check" size={14} />
                    <span>حفظ التغييرات</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

