import { useEffect, useRef, useState } from 'react'
import { useTheme } from '../theme.jsx'

/* ------------------------------------------------------------------
   Theme Switcher — header popover with dedicated Custom Mode & Tinting.
   Follows the same close-on-outside-click pattern as UserChip.
------------------------------------------------------------------- */

const MODE_OPTIONS = [
  { value: 'standard',   label: 'قياسي',             icon: 'monitor' },
  { value: 'dark',       label: 'ليلي',              icon: 'moon' },
  { value: 'light',      label: 'نهاري',             icon: 'sun' },
  { value: 'colorblind', label: 'عمى ألوان',         icon: 'eye' },
  { value: 'custom',     label: 'مخصص',              icon: 'palette' },
]

/** Curated vibrant color presets for 1-click full-theme transformations */
const ACCENT_PRESETS = [
  { name: 'أحمر السويدي', hex: '#9E1B32' },
  { name: 'أزرق ملكي',   hex: '#1D4ED8' },
  { name: 'بنفسجي داكن', hex: '#7C3AED' },
  { name: 'أخضر زمردي',  hex: '#059669' },
  { name: 'عنبر ذهبي',   hex: '#D97706' },
  { name: 'سماوي بحري',  hex: '#0284C7' },
]

function StandardIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
      <line x1="8" y1="21" x2="16" y2="21" />
      <line x1="12" y1="17" x2="12" y2="21" />
    </svg>
  )
}
function MoonIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
    </svg>
  )
}
function SunIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="5" />
      <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
      <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
      <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
      <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
    </svg>
  )
}
function EyeIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  )
}
function PaletteIcon({ size = 15 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="13.5" cy="6.5" r="0.5" fill="currentColor" /><circle cx="17.5" cy="10.5" r="0.5" fill="currentColor" />
      <circle cx="8.5" cy="7.5" r="0.5" fill="currentColor" /><circle cx="6.5" cy="12" r="0.5" fill="currentColor" />
      <path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2z" />
    </svg>
  )
}
function ChevronDownIcon({ size = 11, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <polyline points="6 9 12 15 18 9" />
    </svg>
  )
}
function PenIcon({ size = 14, className = '' }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z" />
    </svg>
  )
}
function ResetIcon({ size = 12 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
    </svg>
  )
}

const ICON_MAP = { standard: StandardIcon, dark: MoonIcon, light: SunIcon, colorblind: EyeIcon, custom: PaletteIcon }

const ARABIC_BRAND_FONT = {
  fontFamily: '"IBM Plex Sans Arabic", "Segoe UI", Tahoma, sans-serif',
  letterSpacing: 'normal',
}

export default function ThemeSwitcher() {
  const { mode, setMode, accent, setAccentColor, resetAccent } = useTheme()
  const [open, setOpen] = useState(false)
  const wrap = useRef(null)

  // Close on outside click or Escape
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

  const TriggerIcon = ICON_MAP[mode] || MoonIcon

  const handleReset = (e) => {
    e.preventDefault()
    e.stopPropagation()
    resetAccent()
  }

  const handleColorChange = (hex) => {
    setAccentColor(hex)
  }

  return (
    <div className="relative select-none text-txt font-sans" ref={wrap} style={ARABIC_BRAND_FONT}>
      {/* Trigger button */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-expanded={open}
        aria-label="تخصيص وتلوين المظهر"
        title="تخصيص وتلوين المظهر"
        style={ARABIC_BRAND_FONT}
        className="flex items-center gap-1.5 px-3 py-1.5 min-h-[36px] bg-steel-3 rounded border border-line hover:border-hi text-txt transition-all hover:scale-105 font-sans"
      >
        <TriggerIcon size={15} />
        <span className="text-[12px] font-bold leading-none select-none">
          المظهر
        </span>
        <ChevronDownIcon
          size={12}
          className={`text-txt-3 transition-transform duration-200 ${open ? 'rotate-180 text-hi' : ''}`}
        />
      </button>

      {/* Popover */}
      {open && (
        <div
          style={ARABIC_BRAND_FONT}
          className="absolute end-0 mt-2 w-[340px] bg-steel-2 border border-line rounded-lg shadow-2xl z-50 overflow-hidden animate-pop font-sans"
        >
          {/* Header */}
          <div className="px-4 py-3 border-b border-line flex items-center justify-between bg-steel-3/40">
            <div className="flex items-center gap-2">
              <PaletteIcon size={15} />
              <span className="text-[13px] font-bold text-txt">تخصيص المظهر وتلوين النظام</span>
            </div>
            {(mode === 'custom' || accent || mode !== 'standard') && (
              <button
                onClick={(e) => {
                  e.preventDefault()
                  e.stopPropagation()
                  setMode('standard')
                  resetAccent()
                }}
                className="flex items-center gap-1 text-[11.5px] font-bold text-txt-3 hover:text-hi transition-colors"
                title="استعادة المظهر القياسي"
                style={ARABIC_BRAND_FONT}
              >
                <ResetIcon size={11} />
                <span>الافتراضي</span>
              </button>
            )}
          </div>

          {/* Mode options */}
          <div className="p-3">
            <div className="text-[12px] font-bold text-txt mb-2 px-1">النمط العام:</div>
            <div className="grid grid-cols-5 gap-1.5">
              {MODE_OPTIONS.map((opt) => {
                const active = mode === opt.value
                const OptIcon = ICON_MAP[opt.value] || StandardIcon
                return (
                  <button
                    key={opt.value}
                    onClick={() => setMode(opt.value)}
                    style={ARABIC_BRAND_FONT}
                    className={[
                      'flex flex-col items-center justify-center gap-1.5 py-2 px-1 rounded-md text-[11px] font-bold transition-all font-sans',
                      active
                        ? 'bg-hi text-white font-bold shadow-sm'
                        : 'bg-steel-3 text-txt-2 hover:text-txt hover:bg-steel border border-line/60',
                    ].join(' ')}
                  >
                    <OptIcon size={14} />
                    <span className="whitespace-nowrap truncate max-w-full font-bold">{opt.label}</span>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Divider */}
          <div className="border-t border-line" />

          {/* Color Presets & Custom Picker */}
          <div className="p-3 bg-steel-3/20">
            <div className="mb-2 px-1">
              <span className="text-[12px] font-bold text-txt">لون النظام:</span>
            </div>

            {/* Presets grid */}
            <div className="grid grid-cols-6 gap-2 mb-3">
              {ACCENT_PRESETS.map((p) => {
                const selected = mode === 'custom' && (accent?.toUpperCase() === p.hex.toUpperCase() || (!accent && p.hex === '#9E1B32'))
                return (
                  <button
                    key={p.hex}
                    onClick={() => handleColorChange(p.hex)}
                    title={p.name}
                    className={[
                      'w-8 h-8 rounded-full transition-transform hover:scale-110 flex items-center justify-center relative shadow-sm cursor-pointer',
                      selected ? 'ring-2 ring-txt ring-offset-2 ring-offset-steel-2 scale-105' : 'opacity-85 hover:opacity-100',
                    ].join(' ')}
                    style={{ background: p.hex }}
                  >
                    {selected && <span className="text-white text-xs font-bold">✓</span>}
                  </button>
                )
              })}
            </div>

            {/* Custom Color Input */}
            <div className="flex items-center gap-2.5 bg-steel-3 p-2 rounded-md border border-line">
              <label
                className="relative w-8 h-8 rounded overflow-hidden cursor-pointer shrink-0 border border-line hover:border-hi transition-all hover:scale-105 flex items-center justify-center shadow-sm"
                title="اختر لونًا مخصصًا"
                style={{ background: accent || '#9E1B32' }}
              >
                <input
                  type="color"
                  value={accent || '#9E1B32'}
                  onChange={(e) => handleColorChange(e.target.value)}
                  className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                />
                <PenIcon size={14} className="text-white drop-shadow pointer-events-none" />
              </label>
              <div className="text-[12px] font-bold text-txt flex-1 leading-tight select-none font-sans">
                اختر لونًا مخصصًا
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
