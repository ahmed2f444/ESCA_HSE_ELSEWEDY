import { useState } from 'react'
import Icon from '../Icon.jsx'

/**
 * Modern Double-Bezel Profile Field Component
 * Supports inline editing, copy-to-clipboard, status badges, and accessible controls.
 */
export default function ProfileField({
  label,
  value,
  icon,
  editable = true,
  masked = false,
  unlocked = false,
  onUnlock,
  onChange,
  onCancel,
  placeholder = '',
  hint = '',
  badge = '',
  fullWidth = false,
  numeric = false,
  maxLength,
  type = 'text',
}) {
  const [copied, setCopied] = useState(false)

  function handleCopy() {
    if (!value) return
    navigator.clipboard.writeText(String(value))
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const displayValue = masked ? (value ? '••••••••••••' : '—') : (value || '—')

  return (
    <div className={`flex flex-col gap-1.5 ${fullWidth ? 'w-full' : ''}`}>
      {/* Label and Badge Header */}
      <div className="flex items-center justify-between gap-2 px-1">
        <label className="flex items-center gap-1.5 text-xs font-bold text-txt-2">
          {icon && <Icon name={icon} size={14} className="text-txt-3" />}
          <span>{label}</span>
        </label>
        {badge ? (
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-steel-3/90 text-txt-2 border border-line/60 flex items-center gap-1">
            <Icon name="lock" size={10} className="text-warn/80" />
            <span>{badge}</span>
          </span>
        ) : !editable ? (
          <span className="text-[10px] font-medium px-2 py-0.5 rounded-full bg-steel-3/70 text-txt-3 border border-line/50 flex items-center gap-1 font-mono">
            <Icon name="lock" size={10} className="text-txt-3" />
            <span>نظامي (قراءة فقط)</span>
          </span>
        ) : null}
      </div>

      {/* Field Value / Input Container (Double-Bezel Nested Card) */}
      <div
        className={`group relative rounded-xl border transition-all duration-200 ${
          unlocked
            ? 'bg-steel-2 border-hi/60 ring-2 ring-hi/20 shadow-md'
            : editable
            ? 'bg-steel-3/50 hover:bg-steel-3/80 border-line/70 hover:border-line text-txt'
            : 'bg-steel-3/30 border-line/40 text-txt-2'
        }`}
      >
        <div className="flex items-center justify-between gap-3 px-3.5 py-2.5 min-h-[44px]">
          {unlocked ? (
            <input
              type={type}
              value={value || ''}
              placeholder={placeholder}
              inputMode={numeric ? 'numeric' : undefined}
              pattern={numeric ? '[0-9]*' : undefined}
              maxLength={maxLength}
              autoFocus
              onChange={(e) => onChange(numeric ? e.target.value.replace(/\D/g, '') : e.target.value)}
              className="w-full bg-transparent text-txt text-sm font-medium outline-none border-none p-0 focus:ring-0 placeholder:text-txt-3/50"
            />
          ) : (
            <span
              className={`text-sm font-medium truncate select-text ${
                !value ? 'text-txt-3 italic' : 'text-txt'
              } ${masked ? 'font-mono tracking-widest text-txt-3' : ''}`}
            >
              {displayValue}
            </span>
          )}

          {/* Action Trigger Buttons */}
          <div className="flex items-center gap-1.5 shrink-0">
            {unlocked ? (
              onCancel && (
                <button
                  type="button"
                  onClick={onCancel}
                  className="p-1 rounded-md text-txt-3 hover:text-crit hover:bg-crit/10 transition-colors"
                  title="إلغاء التعديل"
                >
                  <Icon name="x" size={15} />
                </button>
              )
            ) : editable ? (
              <button
                type="button"
                onClick={onUnlock}
                className="p-1.5 rounded-lg text-txt-3 hover:text-hi2 hover:bg-steel-2/90 transition-all duration-150 active:scale-90 border border-transparent hover:border-line/50"
                title="تعديل هذا الحقل"
              >
                <Icon name="edit" size={14} />
              </button>
            ) : (
              <div className="flex items-center gap-1">
                {value && (
                  <button
                    type="button"
                    onClick={handleCopy}
                    className="p-1.5 rounded-lg text-txt-3 hover:text-txt hover:bg-steel-2 transition-colors opacity-0 group-hover:opacity-100 focus:opacity-100"
                    title="نسخ القيمة"
                  >
                    <Icon name={copied ? 'check' : 'copy'} size={13} className={copied ? 'text-safe' : ''} />
                  </button>
                )}
                <span
                  className="p-1 text-txt-3/50 group-hover:text-txt-3/80 transition-colors cursor-help"
                  title="بيانات معتمدة من الموارد البشرية وإدارة السلامة — غير قابلة للتعديل المباشر"
                >
                  <Icon name="lock" size={13} />
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {hint && <span className="text-[11px] text-txt-3 px-1">{hint}</span>}
    </div>
  )
}

