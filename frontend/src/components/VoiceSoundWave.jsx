import React from 'react'

/**
 * Animated sound wave indicator showing speaking / listening audio levels.
 */
export default function VoiceSoundWave({ isListening = false, isSpeaking = false, size = 'md' }) {
  if (!isListening && !isSpeaking) return null

  const barCount = 5
  const color = isListening ? 'var(--cr, #ef4444)' : 'var(--p, #008851)'

  return (
    <div
      className="voice-soundwave-container"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '3px',
        height: size === 'sm' ? '16px' : '22px',
        padding: '0 4px',
      }}
      title={isListening ? 'جارٍ الاستماع...' : 'المساعد يتحدث الآن...'}
    >
      {[...Array(barCount)].map((_, i) => (
        <span
          key={i}
          className="soundwave-bar"
          style={{
            display: 'inline-block',
            width: size === 'sm' ? '2px' : '3px',
            backgroundColor: color,
            borderRadius: '999px',
            animation: `soundwave-pulse 0.8s ease-in-out infinite alternate`,
            animationDelay: `${i * 0.15}s`,
            minHeight: '4px',
            height: isListening ? `${10 + (i % 3) * 6}px` : `${8 + ((i + 1) % 3) * 5}px`,
          }}
        />
      ))}
    </div>
  )
}
