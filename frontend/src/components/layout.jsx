import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import Icon from './Icon.jsx'
import AgentDock from './AgentDock.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import ThemeSwitcher from './ThemeSwitcher.jsx'
import { useAuth, useCan, useClock, usePolling } from '../hooks.jsx'
import { dashboard, notifications as notificationsApi, training as trainingApi } from '../api/endpoints.js'
import { useTheme } from '../theme.jsx'
import { canOpen } from '../permissions.js'
import { USE_MOCK } from '../api/client.js'

/** Nav order follows the plant's own priority: what gets someone hurt first. */
export const NAV = [
  { to: '/', label: 'لوحة القيادة', icon: 'gauge', end: true },
  { to: '/master-data', label: 'البيانات المرجعية', icon: 'document' },
  { to: '/departments', label: 'الأقسام والمناطق', icon: 'zones' },
  { to: '/incidents', label: 'الحوادث والبلاغات', icon: 'incident', badge: 3 },
  { to: '/fire-equipment', label: 'معدات الحريق', icon: 'fire', badge: 4 },
  { to: '/ppe', label: 'معدات الوقاية', icon: 'ppe' },
  { to: '/inspections', label: 'التفتيش والجولات', icon: 'inspection' },
  { to: '/risk', label: 'تقييم المخاطر', icon: 'risk' },
  { to: '/permits', label: 'تصاريح العمل', icon: 'permit' },
  { to: '/jsa', label: 'JSA وتحليل المهام', icon: 'jsa' },
  { to: '/hazmat', label: 'المواد الخطرة', icon: 'hazmat' },
  { to: '/occupational-health', label: 'الصحة المهنية', icon: 'health' },
  { to: '/training', label: 'التدريب والتأهيل', icon: 'training' },
  { to: '/ai-iot', label: 'المراقبة الآلية', icon: 'ai', badge: 2 },
  { to: '/ai-agent', label: 'الوكيل الذكي', icon: 'chat', badge: 'AI' },
  { to: '/integrations', label: 'الربط والتكامل', icon: 'integrations' },
  { to: '/security', label: 'الأمن والتدقيق', icon: 'security' },
  { to: '/architecture', label: 'معمارية النظام', icon: 'architecture' },
  { to: '/reports', label: 'التقارير', icon: 'reports' },
]

import elsewedyLogoWhite from '../assets/elsewedy-brand-logo-white.png'
import elsewedyLogoDark from '../assets/elsewedy-brand-logo-dark.png'

/** Official Elsewedy Electric — Cable Accessories Brand Image Asset */
export function Wordmark({ scale = 1, className = '', height = 42, width, centered = false, isWhite = true }) {
  const imgSrc = isWhite ? elsewedyLogoWhite : elsewedyLogoDark

  return (
    <div
      dir="ltr"
      className={`inline-flex select-none ${centered ? 'justify-center mx-auto' : 'items-center'} ${className}`}
      style={{
        transform: scale !== 1 ? `scale(${scale})` : undefined,
        transformOrigin: centered ? 'center center' : 'left center',
      }}
    >
      <img
        src={imgSrc}
        alt="ELSEWEDY ELECTRIC | CABLE ACCESSORIES"
        className="w-auto object-contain block max-w-full drop-shadow-md select-none"
        style={{
          height: height ? `${height}px` : '42px',
          width: width ? `${width}px` : 'auto',
        }}
        draggable={false}
      />
    </div>
  )
}

/**
 * Floating Small Container for Live Automation Engine Notifications
 */
function LiveNotificationCard({ item, onDismiss, onAction, onMarkRead }) {
  const isExpired =
    item.type === 'AUTOMATION_CERTIFICATE_EXPIRY' ||
    item.type === 'AUTOMATION_PERMIT_OVERDUE' ||
    item.type === 'AUTOMATION_CAPA_OVERDUE' ||
    item.type === 'AUTOMATION_RISK_REVIEW' ||
    (item.title && (item.title.includes('انتهاء') || item.title.includes('متأخر') || item.title.includes('مراجعة'))) ||
    (item.body && (item.body.includes('انتهت') || item.body.includes('تجاوز') || item.body.includes('متأخر')))
  const isCritical = isExpired || item.severityId >= 3

  const getIconName = () => {
    if (item.type === 'PERMIT' || item.type === 'AUTOMATION_PERMIT_OVERDUE') return 'permit'
    if (item.type === 'TRAINING' || item.type === 'AUTOMATION_CERTIFICATE_EXPIRY') return 'training'
    if (item.type === 'RISK' || item.type === 'AUTOMATION_RISK_REVIEW') return 'risk'
    if (item.type === 'FIRE_EQUIPMENT') return 'fire'
    if (item.type === 'CHEMICAL') return 'hazmat'
    return 'incident'
  }

  const borderColor = isCritical ? 'border-crit/70' : 'border-safe/70'
  const glowShadow = isCritical
    ? 'shadow-[0_8px_30px_rgba(224,72,60,0.35)]'
    : 'shadow-[0_8px_30px_rgba(56,184,124,0.3)]'
  const accentBadgeBg = isCritical
    ? 'bg-crit/15 text-crit border-crit/30'
    : 'bg-safe/15 text-safe border-safe/30'

  // Auto-dismiss in 7.5 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onDismiss()
    }, 7500)
    return () => clearTimeout(timer)
  }, [onDismiss])

  return (
    <div
      className={`relative bg-steel-2/95 backdrop-blur-xl border ${borderColor} ${glowShadow} rounded-xl p-4 text-start transition-all duration-300 transform translate-y-0 animate-pop overflow-hidden`}
      role="alert"
    >
      {/* Top Header Bar */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span className="relative flex h-2.5 w-2.5">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isCritical ? 'bg-crit' : 'bg-safe'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                isCritical ? 'bg-crit' : 'bg-safe'
              }`}
            />
          </span>
          <span
            className={`px-2 py-0.5 rounded-full text-[10.5px] font-bold tracking-wide border ${accentBadgeBg} font-mono`}
          >
            ⚡ محرك الأتمتة الذكي (AI Automation Engine)
          </span>
        </div>
        <button
          onClick={onDismiss}
          className="text-txt-3 hover:text-white p-1 rounded hover:bg-steel-3 transition-colors"
          title="إغلاق الإشعار"
        >
          <Icon name="x" size={13} />
        </button>
      </div>

      {/* Title & Body */}
      <div className="flex items-start gap-3">
        <div
          className={`p-2 rounded-lg shrink-0 mt-0.5 ${
            isCritical ? 'bg-crit/20 text-crit' : 'bg-safe/20 text-safe'
          }`}
        >
          <Icon name={getIconName()} size={17} />
        </div>
        <div className="flex-1 min-w-0">
          <h4 className="text-xs font-bold text-txt-1 leading-snug">{item.title}</h4>
          <p className="text-2xs text-txt-2 mt-1 leading-relaxed">{item.body || item.message}</p>
          <div className="flex items-center justify-between mt-2.5 pt-2 border-t border-line/60">
            <span className="text-[10px] text-txt-3 font-mono">الآن (إشعار فوري مباشر)</span>
            <div className="flex items-center gap-2">
              <button
                onClick={onMarkRead}
                className="text-[11px] text-txt-3 hover:text-txt-1 transition-colors px-2 py-1 rounded hover:bg-steel-3"
              >
                تحديد كمقروء
              </button>
              <button
                onClick={onAction}
                className={`text-[11px] font-semibold px-2.5 py-1 rounded text-white transition-transform active:scale-95 flex items-center gap-1 ${
                  isCritical ? 'bg-crit hover:bg-crit/90' : 'bg-safe hover:bg-safe/90'
                }`}
              >
                <span>عرض التفاصيل</span>
                <Icon name="chevron" size={11} className="rotate-180" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Animated countdown bar */}
      <div className="absolute bottom-0 start-0 h-[2px] w-full bg-line overflow-hidden">
        <div
          className={`h-full ${isCritical ? 'bg-crit' : 'bg-safe'}`}
          style={{
            animation: 'shrinkProgress 7.5s linear forwards',
          }}
        />
      </div>
    </div>
  )
}

function LiveNotificationToasts({ alerts, onMarkRead }) {
  const [toasts, setToasts] = useState([])
  const nav = useNavigate()
  const seenIdsRef = useRef(new Set())
  const isInitialLoadRef = useRef(true)

  // Listen to custom window events for immediate notification popup
  useEffect(() => {
    const handleCustomNotification = (e) => {
      const notif = e.detail
      if (!notif) return
      const id = notif.id || `live-notif-${Date.now()}-${Math.floor(Math.random() * 1000)}`
      seenIdsRef.current.add(id)
      setToasts((prev) => {
        if (prev.some((t) => t.id === id)) {
          return prev
        }
        return [{ ...notif, id, createdAt: Date.now() }, ...prev].slice(0, 3)
      })
    }

    window.addEventListener('hse:notification', handleCustomNotification)
    return () => window.removeEventListener('hse:notification', handleCustomNotification)
  }, [])

  // Check newly polled alerts and trigger floating small container if unseen unread alert arrives
  useEffect(() => {
    if (!Array.isArray(alerts)) return

    if (isInitialLoadRef.current) {
      alerts.forEach((a) => {
        if (a.id) seenIdsRef.current.add(a.id)
      })
      isInitialLoadRef.current = false
      return
    }

    const newUnreadAlerts = alerts.filter(
      (a) => a.unread !== false && !seenIdsRef.current.has(a.id)
    )

    if (newUnreadAlerts.length > 0) {
      newUnreadAlerts.forEach((a) => {
        if (a.id) seenIdsRef.current.add(a.id)
      })

      setToasts((prev) => {
        const toAdd = newUnreadAlerts.filter((na) => !prev.some((p) => p.id === na.id))
        if (toAdd.length === 0) return prev
        const combined = [...toAdd.map((a) => ({ ...a, createdAt: Date.now() })), ...prev]
        return combined.slice(0, 3)
      })
    }
  }, [alerts])

  const dismiss = (id) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }

  const handleAction = (toast) => {
    dismiss(toast.id)
    onMarkRead?.(toast)
    if (toast.to) nav(toast.to)
  }

  if (toasts.length === 0) return null

  return (
    <aside aria-label="الإشعارات الحية" className="fixed top-20 end-5 sm:end-8 z-[990] flex flex-col gap-3 pointer-events-auto max-w-sm sm:max-w-md w-full no-print">
      {toasts.map((item) => (
        <LiveNotificationCard
          key={item.id}
          item={item}
          onDismiss={() => dismiss(item.id)}
          onAction={() => handleAction(item)}
          onMarkRead={() => {
            dismiss(item.id)
            onMarkRead?.(item)
          }}
        />
      ))}
    </aside>
  )
}

function NotificationCenter({ alerts = [], onMarkRead, onMarkAllRead }) {
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const wrap = useRef(null)

  const unreadCount = alerts.filter((a) => a.unread !== false).length

  useEffect(() => {
    if (!open) return
    const onDown = (e) => {
      if (!wrap.current?.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  const handleItemClick = (alert) => {
    setOpen(false)
    onMarkRead?.(alert)
    if (alert.to) nav(alert.to)
  }

  return (
    <div className="relative" ref={wrap}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        title="مركز الإشعارات والتنبيهات الآلية"
        className="relative flex items-center justify-center w-8 h-8 rounded bg-steel-3 border border-line hover:border-txt-3 transition-colors text-txt-2 hover:text-white"
      >
        <Icon name="bell" size={15} />
        {unreadCount > 0 && (
          <span
            key={unreadCount}
            className="absolute -top-1.5 -end-1.5 flex items-center justify-center min-w-[18px] h-[18px] px-1 bg-crit text-white text-[10.5px] font-bold font-mono num rounded-full shadow-lg border-2 border-steel-2 animate-bounce"
          >
            {unreadCount}
          </span>
        )}
      </button>

      {open && (
        <div className="absolute end-0 mt-2 w-80 sm:w-96 bg-steel-2 border border-line rounded-lg shadow-2xl z-50 overflow-hidden animate-fade">
          <div className="flex items-center justify-between px-3.5 py-2.5 bg-steel-3 border-b border-line">
            <div className="flex items-center gap-2">
              <Icon name="bell" size={14} className="text-warn" />
              <span className="text-xs font-bold text-txt-1">التنبيهات والإشعارات الآلية</span>
              {unreadCount > 0 && (
                <span className="px-1.5 py-0.5 bg-crit/20 text-crit text-2xs font-bold rounded-full font-mono">
                  {unreadCount} غير مقروء
                </span>
              )}
            </div>
            {unreadCount > 0 && (
              <button
                onClick={() => {
                  onMarkAllRead?.()
                }}
                className="text-2xs text-txt-3 hover:text-white transition-colors"
              >
                تحديد الكل كمقروء
              </button>
            )}
          </div>

          <div className="max-h-80 overflow-y-auto divide-y divide-line">
            {alerts.length === 0 ? (
              <div className="py-6 text-center text-xs text-txt-3">
                لا توجد إشعارات جديدة حالياً
              </div>
            ) : (
              alerts.map((item, idx) => (
                <div
                  key={item.id || idx}
                  onClick={() => handleItemClick(item)}
                  className={`p-3 text-start hover:bg-steel-3/70 transition-colors cursor-pointer flex gap-2.5 ${
                    item.unread !== false ? 'bg-steel-3/30' : 'opacity-70'
                  }`}
                >
                  <span
                    className="w-2 h-2 rounded-full shrink-0 mt-1.5"
                    style={{ backgroundColor: item.color || 'var(--warn)' }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="text-xs font-semibold text-txt-1 truncate">{item.title}</span>
                      <span className="text-2xs text-txt-3 font-mono shrink-0">{item.time || 'الآن'}</span>
                    </div>
                    <p className="text-2xs text-txt-2 mt-0.5 leading-relaxed line-clamp-2">
                      {item.body || item.message}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}
    </div>
  )
}

function UserChip() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const wrap = useRef(null)

  useEffect(() => {
    if (!open) return
    const onDown = (e) => {
      if (!wrap.current?.contains(e.target)) setOpen(false)
    }
    const onKey = (e) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [open])

  return (
    <div className="relative" ref={wrap}>
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-haspopup="menu"
        className="flex items-center gap-2.5 bg-steel-3 px-3 py-1.5 rounded border border-line hover:border-txt-3 transition-colors"
      >
        <span className="w-[26px] h-[26px] rounded-full bg-info flex items-center justify-center text-[11px] font-semibold text-white">
          {user?.initials || (user?.displayName || user?.name || user?.username || 'U')[0]}
        </span>
        <span className="text-start">
          <span className="block text-[12px] font-semibold leading-tight">{user?.displayName || user?.name || user?.username}</span>
          <span className="block text-2xs text-txt-3 leading-tight">{user?.roleAr || user?.roleLabel}</span>
        </span>
        <Icon name="chevron" size={13} className="text-txt-3 rotate-90" />
      </button>

      {open && (
        <div className="absolute end-0 mt-1.5 w-56 bg-steel-2 border border-line rounded-md shadow-xl z-50 overflow-hidden animate-fade">
          <div className="px-3.5 py-2.5 border-b border-line">
            <div className="text-xs text-txt-3 font-mono num">{user?.email}</div>
            <div className="text-2xs text-txt-3 mt-1 font-mono">ROLE · {user?.role}</div>
          </div>
          <button
            role="menuitem"
            className="w-full text-start px-3.5 py-2.5 text-[12.5px] flex items-center gap-2 hover:bg-steel-3 text-crit"
            onClick={() => {
              setOpen(false)
              logout()
              nav('/login', { replace: true })
            }}
          >
            <Icon name="logout" size={14} /> تسجيل الخروج
          </button>
          <button
            role="menuitem"
            className="w-full text-start px-3.5 py-2.5 text-[12.5px] flex items-center gap-2 hover:bg-steel-3"
            onClick={() => {
              setOpen(false)
              nav('/profile')
            }}
          >
            <Icon name="user" size={14} /> الملف الشخصي
          </button>
        </div>
      )}
    </div>
  )
}

/** Shown when a role reaches a page it isn't scoped for — by typed URL, an old
 *  bookmark, or a link from somewhere else. */
function NoAccess() {
  return (
    <div className="py-24 text-center">
      <Icon name="security" size={38} className="mx-auto text-txt-3 opacity-50 mb-4" />
      <h2 className="text-lg font-semibold">الصفحة دي مش ضمن صلاحياتك</h2>
      <p className="text-sm text-txt-2 mt-2 leading-7 max-w-md mx-auto">
        دورك الحالي مالوش وصول للشاشة دي. لو محتاجها لشغلك، كلّم إدارة السلامة والصحة المهنية.
      </p>
      <Link to="/" className="btn btn-pri inline-flex mt-6">
        العودة للوحة القيادة
      </Link>
    </div>
  )
}

export default function AppShell() {
  const now = useClock()
  const { role } = useCan()
  const { user } = useAuth()
  const { pathname } = useLocation()
  const { mode } = useTheme()

  // Poll live Railway / mock notifications and training schedule
  const rawAlerts = usePolling(() => notificationsApi.list(), 2500)
  const rawSchedule = usePolling(() => trainingApi.schedule(), 3000)
  const [localAlerts, setLocalAlerts] = useState([])
  const firedExpAlertsRef = useRef(new Set())
  const isInitialScheduleLoadedRef = useRef(false)

  useEffect(() => {
    if (Array.isArray(rawAlerts)) {
      setLocalAlerts(rawAlerts)
    }
  }, [rawAlerts])

  // Real-time Active Expiry Watcher: checks expiration timestamps down to the second
  useEffect(() => {
    if (!Array.isArray(rawSchedule)) return

    const nowMs = now.getTime()

    if (!isInitialScheduleLoadedRef.current) {
      // Mark historical expired items older than 60s as seen so they don't fire on initial load
      rawSchedule.forEach((cert) => {
        const certKey = String(cert.id || cert.certId || cert.evidenceRef)
        const expDate = cert.expiryDate || '2099-12-31'
        const expTime = cert.expiryTime || '23:59'
        const targetDt = new Date(`${expDate}T${expTime.length === 5 ? expTime + ':00' : expTime}`)
        if (!isNaN(targetDt.getTime()) && targetDt.getTime() < nowMs - 60000) {
          firedExpAlertsRef.current.add(certKey)
        }
      })
      isInitialScheduleLoadedRef.current = true
      return
    }

    rawSchedule.forEach((cert) => {
      const certKey = String(cert.id || cert.certId || cert.evidenceRef)
      if (!certKey || firedExpAlertsRef.current.has(certKey)) return

      const expDate = cert.expiryDate || cert.expires || '2099-12-31'
      let expTime = cert.expiryTime || ''
      if (!expTime && cert.evidenceRef && cert.evidenceRef.includes('@')) {
        expTime = cert.evidenceRef.split('@')[1].trim()
      }
      if (!expTime) expTime = '23:59'

      const targetDt = new Date(`${expDate}T${expTime.length === 5 ? expTime + ':00' : expTime}`)

      if (!isNaN(targetDt.getTime()) && targetDt.getTime() <= nowMs) {
        firedExpAlertsRef.current.add(certKey)

        const courseName = cert.course || cert.certificate || 'دورة تدريبية'
        const empName = cert.employee || 'موظف'
        const timeDisplay = expTime

        const expiryAlert = {
          id: 'NTF-EXP-' + certKey + '-' + Date.now(),
          notificationId: Date.now(),
          title: `🚨 تنبيه أتمتة السلامة: انتهاء صلاحية شهادة ${empName}`,
          body: `انتهت صلاحية شهادة تدريب الموظف ${empName} لدورة (${courseName}) في التوقيت المحدد (${timeDisplay}) — تم إطلاق تنبيه أتمتة السلامة (AUT-002) وتحديث مصفوفة الكفاءة لمنع إسناد الأعمال الخطرة.`,
          time: 'الآن (مباشر)',
          color: 'var(--crit)',
          type: 'AUTOMATION_CERTIFICATE_EXPIRY',
          to: '/training',
          unread: true,
        }

        window.dispatchEvent(new CustomEvent('hse:notification', { detail: expiryAlert }))
        window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
        window.dispatchEvent(new CustomEvent('hse:certificate-expired', { detail: cert }))
      }
    })
  }, [now, rawSchedule])

  // Real-time custom event listeners
  useEffect(() => {
    const handleCustomNotification = (e) => {
      const notif = e.detail
      if (!notif) return
      setLocalAlerts((prev) => {
        const id = notif.id || `NTF-${Date.now()}`
        if (prev.some((a) => a.id === id || (a.title === notif.title && a.time === notif.time))) {
          return prev
        }
        return [{ ...notif, id, unread: true }, ...prev]
      })
    }
    const handleChanged = () => {
      notificationsApi.list().then((res) => {
        if (Array.isArray(res)) setLocalAlerts(res)
      }).catch(() => {})
    }
    window.addEventListener('hse:notification', handleCustomNotification)
    window.addEventListener('hse:notifications-changed', handleChanged)
    return () => {
      window.removeEventListener('hse:notification', handleCustomNotification)
      window.removeEventListener('hse:notifications-changed', handleChanged)
    }
  }, [])

  const handleMarkRead = (alert) => {
    const targetId = alert.id
    setLocalAlerts((list) =>
      list.map((item) =>
        item.id === targetId || (alert.notificationId && item.notificationId === alert.notificationId && item.type === alert.type)
          ? { ...item, unread: false }
          : item
      )
    )
    if (targetId) {
      notificationsApi.markRead(targetId).catch(() => {})
    }
    window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
  }

  const handleMarkAllRead = async () => {
    setLocalAlerts((list) => list.map((item) => ({ ...item, unread: false })))
    await notificationsApi.markAllRead().catch(() => {})
    window.dispatchEvent(new CustomEvent('hse:notifications-changed'))
  }

  const visibleNav = NAV.filter((n) => canOpen(role, n.to, user?.permissions))
  // Only guard paths the app actually owns — anything else falls through to 404.
  const blocked = NAV.some((n) => n.to === pathname) && !canOpen(role, pathname, user?.permissions)

  return (
    <div className="min-h-screen flex flex-col bg-steel text-txt">
      <div className="hz-stripe no-print" />

      <header className="bg-steel-2 border-b border-line sticky top-0 z-[100] no-print">
        <div className="flex items-center justify-between gap-4 px-[22px] py-2.5 min-h-[64px]">
          {/* Right Side (RTL Start): Logo & Title */}
          <div className="flex items-center gap-3 shrink-0">
            <Wordmark isWhite={mode !== 'light'} height={36} />
            <span className="w-px h-8 bg-line" />
            <div>
              <h1 className="text-[14.5px] font-bold tracking-tight leading-tight">نظام إدارة السلامة والصحة المهنية</h1>
              <span className="block text-[11px] text-txt-3 font-mono num tracking-wide mt-0.5">
                CABLE ACCESSORIES — ESCA · HSE-MS v2.4 · ISO 45001
              </span>
            </div>
          </div>

          {/* Left Side (RTL End): Badges, Clock, Theme Switcher & User Profile */}
          <div className="flex items-center gap-3.5 font-mono num text-xs text-txt-2 shrink-0">
            {USE_MOCK && (
              <span
                className="hidden xl:flex items-center gap-1.5 px-2 py-1 rounded border border-warn/40 bg-warn/10 text-warn text-2xs"
                title="الواجهة تعمل على بيانات محاكاة — بدّل VITE_USE_MOCK=false للربط بـ Spring Boot"
              >
                <Icon name="integrations" size={12} /> MOCK API
              </span>
            )}
            <span className="hidden md:flex items-center gap-1.5">
              <i className="w-[7px] h-[7px] rounded-full bg-safe animate-blip" />
              النظام يعمل
            </span>
            <span className="hidden sm:block text-txt-3">{now.toTimeString().slice(0, 8)}</span>
            <NotificationCenter
              alerts={localAlerts}
              onMarkRead={handleMarkRead}
              onMarkAllRead={handleMarkAllRead}
            />
            <ThemeSwitcher />
            <UserChip />
          </div>
        </div>

        <nav className="flex gap-0.5 px-[22px] overflow-x-auto bg-steel-2">
          {visibleNav.map((n) => (
            <NavLink
              key={n.to}
              to={n.to}
              end={n.end}
              className={({ isActive }) =>
                `nav-tab ${isActive ? 'active' : ''}`
              }
            >
              <Icon name={n.icon} size={15} />
              {n.label}
              {n.badge ? (
                <span className="bg-crit text-white text-[10px] px-1.5 rounded-full font-mono num font-semibold">
                  {n.badge}
                </span>
              ) : null}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="flex-1 w-full max-w-[1600px] mx-auto p-[22px] animate-fade print:p-0 print:max-w-full">
        <ErrorBoundary resetKey={pathname}>{blocked ? <NoAccess /> : <Outlet />}</ErrorBoundary>
      </main>

      <footer className="border-t border-line bg-steel-2 px-[22px] py-4 mt-6 flex items-center justify-between gap-3.5 flex-wrap no-print">
        <div className="flex items-center gap-3.5">
          <Wordmark height={26} isWhite={mode !== 'light'} />
          <span className="text-xs text-txt-2">
            Elsewedy Cables — Cable Accessories (ESCA) · إدارة السلامة والصحة المهنية
          </span>
        </div>
        <span className="font-mono num text-2xs text-txt-3">ISO 45001 · Enterprise Safety Management</span>
      </footer>

      {/* Floating Live Notifications Container & AI Assistant */}
      <LiveNotificationToasts alerts={localAlerts} onMarkRead={handleMarkRead} />

      <div className="no-print">
        <AgentDock />
      </div>
    </div>
  )
}
