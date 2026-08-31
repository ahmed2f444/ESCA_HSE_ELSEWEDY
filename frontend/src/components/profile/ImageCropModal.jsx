import { useEffect, useRef, useState } from 'react'
import Icon from '../Icon.jsx'

/**
 * Interactive Profile Image Cropper & Editor
 * Allows drag-to-pan, smooth zoom, 90-degree rotation, flip horizontal, and high-res circular export.
 */
export default function ImageCropModal({
  imageSrc,
  onConfirm,
  onCancel,
}) {
  const canvasRef = useRef(null)
  const [imageObj, setImageObj] = useState(null)
  const [scale, setScale] = useState(1)
  const [minScale, setMinScale] = useState(1)
  const [position, setPosition] = useState({ x: 0, y: 0 })
  const [rotation, setRotation] = useState(0) // 0, 90, 180, 270
  const [flipX, setFlipX] = useState(false)
  const [isDragging, setIsDragging] = useState(false)
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 })
  const [processing, setProcessing] = useState(false)

  const VIEW_SIZE = 320 // Size of interactive crop canvas in CSS pixels
  const EXPORT_SIZE = 512 // High-res export resolution

  // Load image object
  useEffect(() => {
    if (!imageSrc) return
    const img = new Image()
    img.crossOrigin = 'anonymous'
    img.onload = () => {
      setImageObj(img)
      // Compute minimum scale so image fully covers the circular aperture
      const minDimension = Math.min(img.width, img.height)
      const baseScale = VIEW_SIZE / minDimension
      setMinScale(baseScale)
      setScale(baseScale)
      setPosition({ x: 0, y: 0 })
      setRotation(0)
      setFlipX(false)
    }
    img.src = imageSrc
  }, [imageSrc])

  // Draw interactive preview canvas
  useEffect(() => {
    if (!imageObj || !canvasRef.current) return
    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    canvas.width = VIEW_SIZE * window.devicePixelRatio
    canvas.height = VIEW_SIZE * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    // Clear
    ctx.clearRect(0, 0, VIEW_SIZE, VIEW_SIZE)

    // Save state
    ctx.save()

    // Translate to center
    ctx.translate(VIEW_SIZE / 2 + position.x, VIEW_SIZE / 2 + position.y)
    ctx.rotate((rotation * Math.PI) / 180)
    ctx.scale(flipX ? -scale : scale, scale)

    // Draw image centered
    ctx.imageSmoothingEnabled = true
    ctx.imageSmoothingQuality = 'high'
    ctx.drawImage(
      imageObj,
      -imageObj.width / 2,
      -imageObj.height / 2,
      imageObj.width,
      imageObj.height
    )

    ctx.restore()
  }, [imageObj, scale, position, rotation, flipX])

  // Mouse & Touch Pan Handling
  const handlePointerDown = (e) => {
    setIsDragging(true)
    const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0
    const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0
    setDragStart({ x: clientX - position.x, y: clientY - position.y })
  }

  const handlePointerMove = (e) => {
    if (!isDragging) return
    const clientX = e.clientX || (e.touches && e.touches[0].clientX) || 0
    const clientY = e.clientY || (e.touches && e.touches[0].clientY) || 0
    setPosition({
      x: clientX - dragStart.x,
      y: clientY - dragStart.y,
    })
  }

  const handlePointerUp = () => {
    setIsDragging(false)
  }

  // Wheel zoom
  const handleWheel = (e) => {
    e.preventDefault()
    const delta = e.deltaY < 0 ? 0.08 : -0.08
    setScale((prev) => Math.min(Math.max(prev + delta, minScale * 0.5), minScale * 4))
  }

  const handleRotate = () => {
    setRotation((r) => (r + 90) % 360)
  }

  const handleFlip = () => {
    setFlipX((f) => !f)
  }

  const handleReset = () => {
    if (!imageObj) return
    const minDimension = Math.min(imageObj.width, imageObj.height)
    const baseScale = VIEW_SIZE / minDimension
    setScale(baseScale)
    setPosition({ x: 0, y: 0 })
    setRotation(0)
    setFlipX(false)
  }

  // Final Crop & Export
  const handleCropAndApply = async () => {
    if (!imageObj) return
    setProcessing(true)

    try {
      const exportCanvas = document.createElement('canvas')
      exportCanvas.width = EXPORT_SIZE
      exportCanvas.height = EXPORT_SIZE
      const ctx = exportCanvas.getContext('2d')

      // Scale multiplier from VIEW_SIZE to EXPORT_SIZE
      const ratio = EXPORT_SIZE / VIEW_SIZE

      ctx.imageSmoothingEnabled = true
      ctx.imageSmoothingQuality = 'high'

      // Transform context
      ctx.translate(
        EXPORT_SIZE / 2 + position.x * ratio,
        EXPORT_SIZE / 2 + position.y * ratio
      )
      ctx.rotate((rotation * Math.PI) / 180)
      ctx.scale(flipX ? -scale * ratio : scale * ratio, scale * ratio)

      // Draw full image
      ctx.drawImage(
        imageObj,
        -imageObj.width / 2,
        -imageObj.height / 2,
        imageObj.width,
        imageObj.height
      )

      // Convert to Blob & File
      exportCanvas.toBlob(
        (blob) => {
          if (!blob) {
            setProcessing(false)
            return
          }
          const croppedFile = new File([blob], 'avatar-cropped.png', { type: 'image/png' })
          const croppedPreviewUrl = exportCanvas.toDataURL('image/png')
          onConfirm(croppedFile, croppedPreviewUrl)
          setProcessing(false)
        },
        'image/png',
        0.95
      )
    } catch (err) {
      setProcessing(false)
    }
  }

  return (
    <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/75 backdrop-blur-md animate-fade">
      <div className="relative w-full max-w-md bg-steel-2 rounded-2xl border border-line shadow-2xl overflow-hidden flex flex-col animate-pop">
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3.5 border-b border-line bg-steel-3/60">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-hi/15 text-hi">
              <Icon name="edit" size={15} />
            </div>
            <div>
              <h3 className="text-sm font-bold text-txt">تعديل واقتصاص الصورة الشخصية</h3>
              <p className="text-[11px] text-txt-3">اضبط موضع وحجم الصورة لتناسب إطار الملف الشخصي</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onCancel}
            disabled={processing}
            className="text-txt-3 hover:text-txt p-1.5 rounded-lg hover:bg-steel-3 transition-colors"
          >
            <Icon name="x" size={16} />
          </button>
        </div>

        {/* Interactive Viewport Area */}
        <div className="relative p-6 flex flex-col items-center justify-center bg-steel-3/30 select-none overflow-hidden">
          {/* Crop Container */}
          <div
            className="relative w-[320px] h-[320px] rounded-2xl bg-steel-3 border border-line/70 overflow-hidden cursor-grab active:cursor-grabbing shadow-inner flex items-center justify-center"
            onMouseDown={handlePointerDown}
            onMouseMove={handlePointerMove}
            onMouseUp={handlePointerUp}
            onMouseLeave={handlePointerUp}
            onTouchStart={handlePointerDown}
            onTouchMove={handlePointerMove}
            onTouchEnd={handlePointerUp}
            onWheel={handleWheel}
          >
            {/* The Drawing Canvas */}
            <canvas
              ref={canvasRef}
              style={{ width: VIEW_SIZE, height: VIEW_SIZE }}
              className="block pointer-events-none"
            />

            {/* Circular Darkened Overlay Mask */}
            <div className="absolute inset-0 pointer-events-none flex items-center justify-center">
              {/* Outer darkened shadow ring */}
              <div
                className="w-64 h-64 rounded-full border-2 border-white/90 shadow-[0_0_0_9999px_rgba(0,0,0,0.55)] relative flex items-center justify-center"
              >
                {/* Rule of thirds grid lines inside circle */}
                <div className="absolute inset-0 grid grid-cols-3 grid-rows-3 opacity-20 pointer-events-none">
                  <div className="border-e border-b border-white" />
                  <div className="border-e border-b border-white" />
                  <div className="border-b border-white" />
                  <div className="border-e border-b border-white" />
                  <div className="border-e border-b border-white" />
                  <div className="border-b border-white" />
                  <div className="border-e border-white" />
                  <div className="border-e border-white" />
                  <div />
                </div>
              </div>
            </div>

            {/* Hint Chip */}
            <div className="absolute bottom-2 inset-x-0 flex justify-center pointer-events-none">
              <span className="text-[10px] bg-black/60 text-white/90 px-2.5 py-0.5 rounded-full backdrop-blur-sm">
                اسحب للتحريك · مرر للتقريب
              </span>
            </div>
          </div>

          {/* Quick Adjustment Controls Toolbar */}
          <div className="w-full max-w-[320px] mt-4 space-y-3">
            {/* Zoom Slider */}
            <div className="flex items-center gap-3 bg-steel-3/70 p-2.5 rounded-xl border border-line/60">
              <button
                type="button"
                onClick={() => setScale((s) => Math.max(s - 0.1, minScale * 0.5))}
                className="p-1 rounded text-txt-3 hover:text-txt hover:bg-steel-2 text-xs font-bold font-mono"
                title="تصغير"
              >
                －
              </button>
              <input
                type="range"
                min={minScale * 0.5}
                max={minScale * 4}
                step={0.01}
                value={scale}
                onChange={(e) => setScale(parseFloat(e.target.value))}
                className="flex-1 accent-hi cursor-pointer h-1.5 bg-steel-2 rounded-lg"
              />
              <button
                type="button"
                onClick={() => setScale((s) => Math.min(s + 0.1, minScale * 4))}
                className="p-1 rounded text-txt-3 hover:text-txt hover:bg-steel-2 text-xs font-bold font-mono"
                title="تكبير"
              >
                ＋
              </button>
              <span className="text-2xs font-mono text-txt-3 w-10 text-center shrink-0">
                {Math.round((scale / minScale) * 100)}%
              </span>
            </div>

            {/* Transform Action Buttons */}
            <div className="flex items-center justify-between gap-2">
              <button
                type="button"
                onClick={handleRotate}
                className="flex-1 py-1.5 px-2 rounded-lg bg-steel-3 hover:bg-steel-3/80 text-txt-2 hover:text-txt text-xs font-medium border border-line/60 flex items-center justify-center gap-1.5 transition-colors"
                title="تدوير الصورة 90 درجة"
              >
                <span>تدوير 90°</span>
              </button>

              <button
                type="button"
                onClick={handleFlip}
                className="flex-1 py-1.5 px-2 rounded-lg bg-steel-3 hover:bg-steel-3/80 text-txt-2 hover:text-txt text-xs font-medium border border-line/60 flex items-center justify-center gap-1.5 transition-colors"
                title="عكس أفقي"
              >
                <span>انعكاس ⇄</span>
              </button>

              <button
                type="button"
                onClick={handleReset}
                className="py-1.5 px-2.5 rounded-lg bg-steel-3 hover:bg-steel-3/80 text-txt-3 hover:text-txt text-xs font-medium border border-line/60 transition-colors"
                title="إعادة ضبط الموضع والحجم"
              >
                إعادة ضبط
              </button>
            </div>
          </div>
        </div>

        {/* Footer Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 px-5 py-3.5 border-t border-line bg-steel-3/40">
          <button
            type="button"
            onClick={onCancel}
            disabled={processing}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-txt-3 hover:text-txt hover:bg-steel-3 transition-colors"
          >
            إلغاء
          </button>
          <button
            type="button"
            onClick={handleCropAndApply}
            disabled={processing || !imageObj}
            className="px-5 py-2 rounded-xl bg-hi hover:bg-hi2 text-hi-txt text-xs font-bold shadow-md transition-all active:scale-95 disabled:opacity-50 flex items-center gap-1.5"
          >
            {processing ? (
              <>
                <div className="w-3.5 h-3.5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                <span>...جارٍ المعالجة</span>
              </>
            ) : (
              <>
                <Icon name="check" size={14} />
                <span>تأكيد واقتصاص الصورة</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
