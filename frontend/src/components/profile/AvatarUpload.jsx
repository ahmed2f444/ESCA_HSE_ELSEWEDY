import { useState, useRef, useEffect } from 'react'
import Icon from '../Icon.jsx'
import ImageCropModal from './ImageCropModal.jsx'
import { resolveAvatarUrl } from '../../api/endpoints.js'

/**
 * Executive Profile Avatar Component
 * Double-bezel nested container with interactive crop modal, initials fallback, live preview, and photo management.
 */
export default function AvatarUpload({
  avatarPath,
  fullName = '',
  username = '',
  onUpload,
  onRemove,
  disabled = false,
}) {
  const fileInputRef = useRef(null)
  const [imgError, setImgError] = useState(false)
  const [isHovered, setIsHovered] = useState(false)
  const [cropSrc, setCropSrc] = useState(null)
  const [localPreview, setLocalPreview] = useState(() => {
    try {
      const storedUser = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      return storedUser.avatarPath || localStorage.getItem('esca.hse.avatar') || null
    } catch {
      return null
    }
  })

  const displayName = fullName.trim() || username.trim() || 'مستخدم'
  const initials = displayName.length > 0 ? displayName.slice(0, 1).toUpperCase() : '👤'

  useEffect(() => {
    setImgError(false)
    if (avatarPath) {
      setLocalPreview(avatarPath)
    }
  }, [avatarPath])

  function handlePick() {
    if (disabled) return
    fileInputRef.current?.click()
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      const reader = new FileReader()
      reader.onload = () => {
        setCropSrc(reader.result)
      }
      reader.readAsDataURL(file)
    }
    e.target.value = ''
  }

  function handleCropConfirm(croppedFile, previewUrl) {
    setImgError(false)
    setLocalPreview(previewUrl)
    setCropSrc(null)
    onUpload(croppedFile, previewUrl)
  }

  function handleCropCancel() {
    setCropSrc(null)
  }

  function handleRemove() {
    setLocalPreview(null)
    setImgError(false)
    try {
      localStorage.removeItem('esca.hse.avatar')
      const stored = JSON.parse(localStorage.getItem('esca.hse.user') || '{}')
      delete stored.avatarPath
      localStorage.setItem('esca.hse.user', JSON.stringify(stored))
    } catch {}
    onRemove()
  }

  const resolvedUrl = resolveAvatarUrl(avatarPath)
  const effectiveSrc = localPreview || resolvedUrl
  const hasAvatar = Boolean(effectiveSrc && !imgError)

  return (
    <div className="flex flex-col items-center justify-center mb-6">
      {/* Outer Shell (Double-Bezel) */}
      <div
        className="relative group p-1.5 rounded-full bg-steel-3/70 border border-line/80 shadow-lg transition-all duration-300 hover:border-hi/40 hover:shadow-[0_0_25px_rgba(var(--c-hi)/0.25)]"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Inner Core: Avatar Circle */}
        <div
          onClick={handlePick}
          className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full overflow-hidden flex items-center justify-center cursor-pointer bg-steel-2 select-none border border-line/40 transition-transform duration-300 active:scale-[0.98]"
          title="انقر لتغيير أو اقتصاص الصورة الشخصية"
        >
          {hasAvatar ? (
            <img
              key={effectiveSrc}
              src={effectiveSrc}
              alt=""
              onError={() => {
                // If local preview is set, don't immediately fallback to error unless both fail
                if (!localPreview) setImgError(true)
              }}
              className="w-full h-full object-cover object-center block transition-transform duration-500 group-hover:scale-105"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-hi/25 via-steel-3 to-steel-2 text-txt font-bold text-3xl sm:text-4xl font-mono select-none">
              <span className="drop-shadow-sm text-hi2">{initials}</span>
            </div>
          )}

          {/* Hover Overlay with Camera Icon */}
          <div
            className={`absolute inset-0 bg-steel/70 backdrop-blur-xs flex flex-col items-center justify-center gap-1 text-txt-1 transition-opacity duration-200 ${
              isHovered ? 'opacity-100' : 'opacity-0 pointer-events-none'
            }`}
          >
            <div className="p-2 rounded-full bg-steel-2 border border-line shadow-md text-hi">
              <Icon name="camera" size={20} />
            </div>
            <span className="text-[11px] font-semibold text-txt-2">اقتصاص وتعديل</span>
          </div>
        </div>

        {/* Floating Quick Edit Trigger Button */}
        <button
          type="button"
          onClick={handlePick}
          disabled={disabled}
          className="absolute bottom-1 end-1 w-8 h-8 rounded-full bg-hi text-hi-txt border-2 border-steel-2 shadow-md flex items-center justify-center transition-all duration-200 hover:scale-110 hover:bg-hi2 active:scale-95 cursor-pointer z-10"
          title="رفع واقتصاص صورة جديدة"
        >
          <Icon name="edit" size={14} />
        </button>

        {/* Active HSE Status Pulse */}
        <span
          className="absolute top-1 start-1 flex h-3.5 w-3.5"
          title="حساب نشط ومعتمد"
        >
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-safe opacity-75" />
          <span className="relative inline-flex rounded-full h-3.5 w-3.5 bg-safe border-2 border-steel-2" />
        </span>
      </div>

      {/* Hidden File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/png, image/jpeg, image/webp"
        className="hidden"
        onChange={handleFileChange}
      />

      {/* Action Buttons Row */}
      <div className="flex items-center gap-3 mt-3.5">
        <button
          type="button"
          onClick={handlePick}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-steel-3 hover:bg-steel-3/80 text-txt border border-line/60 hover:border-line transition-all duration-200 cursor-pointer shadow-xs active:scale-95"
        >
          <Icon name="upload" size={13} className="text-hi2" />
          <span>تحديث واقتصاص</span>
        </button>

        {hasAvatar && (
          <button
            type="button"
            onClick={handleRemove}
            disabled={disabled}
            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-crit/10 hover:bg-crit/20 text-crit border border-crit/30 transition-all duration-200 cursor-pointer active:scale-95"
          >
            <Icon name="trash" size={13} />
            <span>إزالة</span>
          </button>
        )}
      </div>
      <span className="text-[11px] text-txt-3 mt-1.5">يدعم JPG و PNG مع إمكانية القص والتكبير والتدوير</span>

      {/* Interactive Crop & Edit Modal */}
      {cropSrc && (
        <ImageCropModal
          imageSrc={cropSrc}
          onConfirm={handleCropConfirm}
          onCancel={handleCropCancel}
        />
      )}
    </div>
  )
}


