import { useState, useEffect, useRef, useCallback } from 'react'

/**
 * Strips markdown, emojis, code blocks, and table artifacts to produce clean spoken text.
 */
export function cleanTextForSpeech(mdText = '') {
  if (!mdText) return ''
  let text = String(mdText)

  // Remove code blocks
  text = text.replace(/```[\s\S]*?```/g, '')
  // Remove inline code
  text = text.replace(/`([^`]+)`/g, '$1')
  // Remove Markdown links [text](url) -> text
  text = text.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
  // Remove markdown headers
  text = text.replace(/^#+\s+/gm, '')
  // Remove bold/italic symbols
  text = text.replace(/[*_~]{1,3}/g, '')
  // Remove blockquotes
  text = text.replace(/^>\s+/gm, '')
  // Remove table separator lines and pipes
  text = text.replace(/\|[-:\s|]+\|/g, ' ')
  text = text.replace(/\|/g, ' ')
  // Remove bullet symbols
  text = text.replace(/^[-*+]\s+/gm, '')
  // Remove excessive whitespace
  text = text.replace(/\s+/g, ' ').trim()

  return text
}

/**
 * Enterprise hook providing two-way Voice Assistant capabilities:
 * - Speech-to-Text (STT) via Web Speech API (Arabic/English)
 * - Text-to-Speech (TTS) via Web Speech Synthesis with natural voice selection
 */
export function useVoiceAssistant({
  onTranscript,
  onSpeechEnd,
  defaultLang = 'ar-EG',
} = {}) {
  const [isListening, setIsListening] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [activeSpeakingId, setActiveSpeakingId] = useState(null)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [autoSpeak, setAutoSpeak] = useState(() => {
    try {
      return localStorage.getItem('esca_hse_auto_speak') === 'true'
    } catch {
      return false
    }
  })
  const [selectedVoice, setSelectedVoice] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])
  const [error, setError] = useState(null)

  const recognitionRef = useRef(null)
  const synthRef = useRef(typeof window !== 'undefined' ? window.speechSynthesis : null)
  const utteranceRef = useRef(null)

  // Check browser support
  const hasSTT = typeof window !== 'undefined' && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window)
  const hasTTS = typeof window !== 'undefined' && 'speechSynthesis' in window

  // Load and cache voices
  useEffect(() => {
    if (!hasTTS || !synthRef.current) return

    const loadVoices = () => {
      const voices = synthRef.current.getVoices() || []
      setAvailableVoices(voices)

      // Find the best Arabic voice
      const arabicVoice = voices.find((v) => v.lang.startsWith('ar') || v.lang.includes('EG') || v.lang.includes('SA'))
      if (arabicVoice) {
        setSelectedVoice(arabicVoice)
      } else {
        const defaultV = voices.find((v) => v.default) || voices[0]
        setSelectedVoice(defaultV || null)
      }
    }

    loadVoices()
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = loadVoices
    }
  }, [hasTTS])

  // Save autoSpeak preference
  const toggleAutoSpeak = useCallback(() => {
    setAutoSpeak((prev) => {
      const next = !prev
      try {
        localStorage.setItem('esca_hse_auto_speak', String(next))
      } catch {}
      return next
    })
  }, [])

  // Initialize SpeechRecognition
  const initRecognition = useCallback(() => {
    if (!hasSTT) return null
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognizer = new SpeechRecognition()
    recognizer.continuous = false
    recognizer.interimResults = true
    recognizer.lang = defaultLang
    recognizer.maxAlternatives = 1

    recognizer.onstart = () => {
      setIsListening(true)
      setError(null)
    }

    recognizer.onresult = (event) => {
      let finalStr = ''
      let interimStr = ''

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalStr += event.results[i][0].transcript
        } else {
          interimStr += event.results[i][0].transcript
        }
      }

      if (interimStr) {
        setInterimTranscript(interimStr)
      }

      if (finalStr) {
        setTranscript(finalStr)
        setInterimTranscript('')
        if (onTranscript) {
          onTranscript(finalStr)
        }
      }
    }

    recognizer.onerror = (event) => {
      console.warn('[VoiceAssistant] STT error:', event.error)
      setError(event.error)
      setIsListening(false)
      setInterimTranscript('')
    }

    recognizer.onend = () => {
      setIsListening(false)
      setInterimTranscript('')
      if (onSpeechEnd) {
        onSpeechEnd()
      }
    }

    return recognizer
  }, [hasSTT, defaultLang, onTranscript, onSpeechEnd])

  const startListening = useCallback(() => {
    if (!hasSTT) {
      setError('متصفحك لا يدعم التعرف على الصوت (Web Speech API).')
      return
    }

    // Stop speaking before listening to avoid echo
    if (synthRef.current && synthRef.current.speaking) {
      synthRef.current.cancel()
      setIsSpeaking(false)
      setActiveSpeakingId(null)
    }

    try {
      if (recognitionRef.current) {
        recognitionRef.current.abort()
      }
      recognitionRef.current = initRecognition()
      recognitionRef.current?.start()
    } catch (err) {
      console.warn('[VoiceAssistant] startListening error:', err)
      setError('تعذر تشغيل الميكروفون.')
      setIsListening(false)
    }
  }, [hasSTT, initRecognition])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
    }
    setIsListening(false)
  }, [])

  const toggleListening = useCallback(() => {
    if (isListening) {
      stopListening()
    } else {
      startListening()
    }
  }, [isListening, startListening, stopListening])

  // Text-To-Speech
  const speak = useCallback(
    (text, messageId = null) => {
      if (!hasTTS || !synthRef.current) return
      const clean = cleanTextForSpeech(text)
      if (!clean) return

      // If currently speaking this exact message, stop it
      if (isSpeaking && activeSpeakingId === messageId && messageId !== null) {
        stopSpeaking()
        return
      }

      stopSpeaking()

      try {
        const utterance = new SpeechSynthesisUtterance(clean)
        utterance.lang = defaultLang
        utterance.rate = 1.0
        utterance.pitch = 1.0

        if (selectedVoice) {
          utterance.voice = selectedVoice
        }

        utterance.onstart = () => {
          setIsSpeaking(true)
          setActiveSpeakingId(messageId)
        }

        utterance.onend = () => {
          setIsSpeaking(false)
          setActiveSpeakingId(null)
        }

        utterance.onerror = (e) => {
          console.warn('[VoiceAssistant] TTS error:', e)
          setIsSpeaking(false)
          setActiveSpeakingId(null)
        }

        utteranceRef.current = utterance
        synthRef.current.speak(utterance)
      } catch (err) {
        console.warn('[VoiceAssistant] TTS error:', err)
        setIsSpeaking(false)
        setActiveSpeakingId(null)
      }
    },
    [hasTTS, defaultLang, selectedVoice, isSpeaking, activeSpeakingId]
  )

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel()
    }
    setIsSpeaking(false)
    setActiveSpeakingId(null)
  }, [])

  return {
    hasSTT,
    hasTTS,
    isListening,
    isSpeaking,
    activeSpeakingId,
    transcript,
    interimTranscript,
    autoSpeak,
    toggleAutoSpeak,
    startListening,
    stopListening,
    toggleListening,
    speak,
    stopSpeaking,
    availableVoices,
    selectedVoice,
    setSelectedVoice,
    error,
  }
}
