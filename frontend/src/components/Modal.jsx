import { useEffect } from 'react'
import { createPortal } from 'react-dom'
import Icon from './Icon.jsx'

export default function Modal({ open, onClose, title, width = 620, footer, children }) {
  useEffect(() => {
    if (!open) return
    const onKey = (e) => e.key === 'Escape' && onClose?.()
    document.addEventListener('keydown', onKey)
    // Stop the console behind the dialog from scrolling under it.
    const prev = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = prev
    }
  }, [open, onClose])

  if (!open) return null

  return createPortal(
    <div
      className="fixed inset-0 z-[900] flex items-center justify-center p-5"
      style={{ background: 'rgba(6,10,14,.82)', backdropFilter: 'blur(3px)' }}
      onMouseDown={(e) => e.target === e.currentTarget && onClose?.()}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="bg-steel-2 border border-line rounded-lg w-full max-h-[88vh] overflow-y-auto animate-pop"
        style={{ maxWidth: width }}
      >
        <div className="sticky top-0 z-10 bg-steel-2 px-5 py-3.5 border-b border-line flex items-center justify-between gap-3">
          <h3 className="text-[15px] font-semibold">{title}</h3>
          <button className="text-txt-3 hover:text-crit p-1 -m-1" onClick={onClose} aria-label="إغلاق">
            <Icon name="close" size={18} />
          </button>
        </div>
        <div className="p-5">{children}</div>
        {footer && (
          <div className="px-5 py-3.5 border-t border-line flex gap-2.5" style={{ background: 'rgba(0,0,0,.15)' }}>
            {footer}
          </div>
        )}
      </div>
    </div>,
    document.body
  )
}
