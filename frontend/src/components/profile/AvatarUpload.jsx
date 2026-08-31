import { useRef } from 'react'

/**
 * Profile picture block, matching the hand-drawn sketch:
 * circular placeholder with a small edit icon overlapping its corner.
 * Avatar is the ONLY field that supports delete (per the spec's
 * field-level permissions — avatar_path is nullable, everything else isn't).
 */
export default function AvatarUpload({ avatarPath, onUpload, onRemove }) {
  const fileInputRef = useRef(null)

  function handlePick() {
    fileInputRef.current?.click()
  }

  function handleFileChange(e) {
    const file = e.target.files?.[0]
    if (file) {
      const previewUrl = URL.createObjectURL(file)
      onUpload(file, previewUrl)
    }
    e.target.value = '' // allow re-selecting the same file later
  }

  return (
    <div className="avatar-block">
      <div className="avatar-frame">
        {avatarPath ? (
          <img src={avatarPath} alt="الصورة الشخصية" />
        ) : (
          <span style={{ fontSize: 32 }}>👤</span>
        )}
      </div>

      <button type="button" className="avatar-edit-btn" onClick={handlePick} title="تغيير الصورة">
        ✎
      </button>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/png, image/jpeg"
        style={{ display: 'none' }}
        onChange={handleFileChange}
      />

      <button type="button" className="avatar-remove-btn" onClick={onRemove}>
        إزالة الصورة
      </button>
    </div>
  )
}
