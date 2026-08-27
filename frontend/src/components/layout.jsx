import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation, useNavigate } from 'react-router-dom'
import Icon from './Icon.jsx'
import AgentDock from './AgentDock.jsx'
import ErrorBoundary from './ErrorBoundary.jsx'
import { useAuth, useCan, useClock } from '../hooks.jsx'
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

import logoImg from '../assets/logo.png'

/** Official Elsewedy Cables Vector Wordmark with bright white text and red swoosh */
export function Wordmark({ scale = 1, className = '', height = 48, width, centered = false, isWhite = true }) {
  return (
    <div
      className={`inline-flex flex-col select-none ${centered ? 'items-center text-center mx-auto' : 'items-start'} ${className}`}
      style={{
        transform: scale !== 1 ? `scale(${scale})` : undefined,
        transformOrigin: centered ? 'center center' : 'right center'
      }}
    >
      <svg
        viewBox="0 0 460 100"
        className="w-auto h-auto max-w-full drop-shadow-md"
        style={{
          height: height ? `${height}px` : undefined,
          width: width ? `${width}px` : undefined,
        }}
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* ELSEWEDY bold uppercase text */}
        <text
          x="230"
          y="44"
          textAnchor="middle"
          fill={isWhite ? "#FFFFFF" : "#111827"}
          fontFamily="system-ui, -apple-system, 'Segoe UI', Roboto, 'Inter', Arial, sans-serif"
          fontWeight="900"
          fontSize="42"
          letterSpacing="12"
        >
          ELSEWEDY
        </text>

        {/* CABLES spaced uppercase text */}
        <text
          x="230"
          y="72"
          textAnchor="middle"
          fill={isWhite ? "#FFFFFF" : "#1F2937"}
          fontFamily="system-ui, -apple-system, 'Segoe UI', Roboto, 'Inter', Arial, sans-serif"
          fontWeight="700"
          fontSize="21"
          letterSpacing="22"
        >
          CABLES
        </text>

        {/* Dynamic Red Swoosh Arc */}
        <path
          d="M 25 82 C 130 106, 330 106, 435 82 C 330 94, 130 94, 25 82 Z"
          fill="#ED1C24"
        />
      </svg>
    </div>
  )
}







function UserChip() {
  const { user, logout } = useAuth()
  const [open, setOpen] = useState(false)
  const nav = useNavigate()
  const wrap = useRef(null)

  /**
   * Close on a click outside or on Escape.
   *
   * This used to close on the toggle's `blur` after a short timer, which raced
   * the click it was supposed to allow: mousedown blurs the toggle, and if the
   * button is held longer than the timer the menu unmounts before `click`
   * fires — so logout silently did nothing. Anchoring on the container instead
   * of focus removes the timing dependency entirely.
   */
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
        <Icon name="caret" size={13} className="text-txt-3" />
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

  const visibleNav = NAV.filter((n) => canOpen(role, n.to, user?.permissions))
  // Only guard paths the app actually owns — anything else falls through to 404.
  const blocked = NAV.some((n) => n.to === pathname) && !canOpen(role, pathname, user?.permissions)

  return (
    <div className="min-h-screen flex flex-col">
      <div className="hz-stripe no-print" />

      <header className="bg-steel-2 border-b border-line sticky top-0 z-[100] no-print">
        <div className="flex items-center justify-between gap-4 flex-wrap px-[22px] py-3">
          <div className="flex items-center">
            <Wordmark />
            <span className="w-px h-10 bg-line mx-4" />
            <div>
              <h1 className="text-base font-semibold tracking-tight">نظام إدارة السلامة والصحة المهنية</h1>
              <span className="block text-xs text-txt-3 font-mono num tracking-wide mt-px">
                CABLE ACCESSORIES — ESCA · HSE-MS v2.4 · ISO 45001
              </span>
            </div>
          </div>

          <div className="flex items-center gap-5 font-mono num text-xs text-txt-2">
            {USE_MOCK && (
              <span
                className="hidden lg:flex items-center gap-1.5 px-2 py-1 rounded border text-2xs"
                style={{ borderColor: 'rgba(240,144,48,.4)', background: 'rgba(240,144,48,.1)', color: '#F09030' }}
                title="الواجهة تعمل على بيانات محاكاة — بدّل VITE_USE_MOCK=false للربط بـ Spring Boot"
              >
                <Icon name="integrations" size={12} /> MOCK API
              </span>
            )}
            <span className="hidden md:flex items-center gap-1.5">
              <i className="w-[7px] h-[7px] rounded-full bg-safe animate-blip" />
              النظام يعمل
            </span>
            <span className="hidden sm:block">{now.toTimeString().slice(0, 8)}</span>
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
                [
                  'px-4 py-2.5 text-[13px] font-medium whitespace-nowrap flex items-center gap-2 border-b-[3px] transition-colors duration-150',
                  isActive
                    ? 'text-white border-hi bg-hi/[.18]'
                    : 'text-txt-2 border-transparent hover:text-txt hover:bg-hi/10',
                ].join(' ')
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
        <div className="flex items-center gap-2.5">
          <Wordmark scale={0.62} />
          <span className="text-xs text-txt-2 -ms-11">
            Elsewedy Cables — Cable Accessories (ESCA) · إدارة السلامة والصحة المهنية
          </span>
        </div>
        <span className="font-mono num text-2xs text-txt-3">ISO 45001 · Enterprise Safety Management</span>
      </footer>

      <div className="no-print">
        <AgentDock />
      </div>
    </div>
  )
}
