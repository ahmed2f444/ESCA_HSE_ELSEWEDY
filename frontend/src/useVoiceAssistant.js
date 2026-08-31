import { useState, useEffect, useRef, useCallback } from 'react'
import { assistant } from './api/endpoints.js'

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
 * Detects whether a string is primarily Arabic or English.
 */
export function detectLanguage(text = '') {
  if (!text) return 'ar-EG'
  const arabicRegex = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]/g
  const latinRegex = /[a-zA-Z]/g

  const arabicMatches = text.match(arabicRegex) || []
  const latinMatches = text.match(latinRegex) || []

  if (arabicMatches.length >= latinMatches.length) {
    return 'ar-EG'
  }
  return 'en-US'
}

export const VOICE_LANGUAGES = [
  { id: 'auto', label: 'تلقائي ذكي (مختلط عربي + English)', short: '🌐 تلقائي (AI)', flag: '🌐', speechLang: 'ar-EG' },
  { id: 'ar-EG', label: 'العربية (اللهجة المصرية)', short: '🇪🇬 مصري', flag: '🇪🇬', speechLang: 'ar-EG' },
  { id: 'ar-SA', label: 'العربية (الفصحى والخليج)', short: '🇸🇦 خليجي/فصحى', flag: '🇸🇦', speechLang: 'ar-SA' },
  { id: 'en-US', label: 'English (US / Global)', short: '🇬🇧 English', flag: '🇬🇧', speechLang: 'en-US' },
]

/**
 * Enterprise hook providing Multilingual & Multi-Dialect Voice capabilities:
 * - Speech-to-Text (STT) via Whisper Neural Cloud + Web Speech API fallback
 * - Natural Code-Switching (Mixed Arabic + English) support
 * - Text-to-Speech (TTS) with dynamic language-aware voice routing
 */
export function useVoiceAssistant({
  onTranscript,
  onSpeechEnd,
  defaultLang = 'auto',
} = {}) {
  const [langMode, setLangMode] = useState(() => {
    try {
      return localStorage.getItem('esca_hse_voice_lang') || defaultLang
    } catch {
      return defaultLang
    }
  })

  const [isListening, setIsListening] = useState(false)
  const [isTranscribing, setIsTranscribing] = useState(false)
  const [isSpeaking, setIsSpeaking] = useState(false)
  const [activeSpeakingId, setActiveSpeakingId] = useState(null)
  const [transcript, setTranscript] = useState('')
  const [interimTranscript, setInterimTranscript] = useState('')
  const [error, setError] = useState(null)

  const [autoSpeak, setAutoSpeak] = useState(() => {
    try {
      return localStorage.getItem('esca_hse_auto_speak') === 'true'
    } catch {
      return false
    }
  })

  const [selectedVoice, setSelectedVoice] = useState(null)
  const [availableVoices, setAvailableVoices] = useState([])

  const recognitionRef = useRef(null)
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)
  const synthRef = useRef(typeof window !== 'undefined' ? window.speechSynthesis : null)
  const utteranceRef = useRef(null)

  // Browser support checks
  const hasSTT = typeof window !== 'undefined' && (
    'SpeechRecognition' in window ||
    'webkitSpeechRecognition' in window ||
    (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function')
  )
  const hasTTS = typeof window !== 'undefined' && 'speechSynthesis' in window

  // Save language preference
  const changeLangMode = useCallback((newLang) => {
    setLangMode(newLang)
    try {
      localStorage.setItem('esca_hse_voice_lang', newLang)
    } catch {}
  }, [])

  // Load and cache voices for TTS
  useEffect(() => {
    if (!hasTTS || !synthRef.current) return

    const loadVoices = () => {
      const voices = synthRef.current.getVoices() || []
      setAvailableVoices(voices)

      const arabicVoice = voices.find((v) => v.lang.startsWith('ar') || v.lang.includes('EG') || v.lang.includes('SA'))
      const englishVoice = voices.find((v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.default))
      const fallbackVoice = voices.find((v) => v.default) || voices[0]

      setSelectedVoice(arabicVoice || englishVoice || fallbackVoice || null)
    }

    loadVoices()
    if (synthRef.current.onvoiceschanged !== undefined) {
      synthRef.current.onvoiceschanged = loadVoices
    }
  }, [hasTTS])

  // Toggle auto-speak
  const toggleAutoSpeak = useCallback(() => {
    setAutoSpeak((prev) => {
      const next = !prev
      try {
        localStorage.setItem('esca_hse_auto_speak', String(next))
      } catch {}
      return next
    })
  }, [])

  // Text-To-Speech with dynamic language detection
  const speak = useCallback(
    (text, messageId = null) => {
      if (!hasTTS || !synthRef.current) return
      const clean = cleanTextForSpeech(text)
      if (!clean) return

      if (isSpeaking && activeSpeakingId === messageId && messageId !== null) {
        stopSpeaking()
        return
      }

      stopSpeaking()

      try {
        const detectedLang = detectLanguage(clean)
        const utterance = new SpeechSynthesisUtterance(clean)
        utterance.lang = detectedLang
        utterance.rate = 1.05
        utterance.pitch = 1.0

        // Find appropriate voice for detected language
        if (availableVoices.length > 0) {
          if (detectedLang.startsWith('ar')) {
            const arVoice = availableVoices.find((v) => v.lang.startsWith('ar'))
            if (arVoice) utterance.voice = arVoice
          } else {
            const enVoice = availableVoices.find((v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.lang.includes('US')))
            if (enVoice) utterance.voice = enVoice
          }
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
    [hasTTS, availableVoices, isSpeaking, activeSpeakingId]
  )

  const stopSpeaking = useCallback(() => {
    if (synthRef.current) {
      synthRef.current.cancel()
    }
    setIsSpeaking(false)
    setActiveSpeakingId(null)
  }, [])

  // Start MediaRecorder for Whisper AI
  const startWhisperRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      audioChunksRef.current = []

      const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
        ? 'audio/webm;codecs=opus'
        : MediaRecorder.isTypeSupported('audio/webm')
        ? 'audio/webm'
        : 'audio/ogg'

      const mediaRecorder = new MediaRecorder(stream, { mimeType })
      mediaRecorderRef.current = mediaRecorder

      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: mimeType })
        // Clean up tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach((track) => track.stop())
          streamRef.current = null
        }

        if (audioBlob.size > 2000) {
          setIsTranscribing(true)
          try {
            const data = await assistant.transcribe(audioBlob, langMode)
            if (data && data.text) {
              setTranscript(data.text)
              if (onTranscript) onTranscript(data.text)
            }
          } catch (err) {
            console.warn('[VoiceAssistant] Whisper API fallback to WebSpeech or error:', err)
          } finally {
            setIsTranscribing(false)
          }
        }
        setIsListening(false)
        if (onSpeechEnd) onSpeechEnd()
      }

      mediaRecorder.start(250)
      setIsListening(true)
      setError(null)
    } catch (err) {
      console.warn('[VoiceAssistant] Microphone access failed:', err)
      setError('تعذر الوصول إلى الميكروفون. يرجى التأكد من منح الإذن.')
      setIsListening(false)
    }
  }, [langMode, onTranscript, onSpeechEnd])

  // Fallback to Web Speech API when explicitly chosen or mediaRecorder not available
  const startWebSpeech = useCallback(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition
    if (!SpeechRecognition) return

    const recognizer = new SpeechRecognition()
    recognizer.continuous = false
    recognizer.interimResults = true
    recognizer.lang = langMode === 'auto' ? 'ar-EG' : langMode
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
      if (interimStr) setInterimTranscript(interimStr)
      if (finalStr) {
        setTranscript(finalStr)
        setInterimTranscript('')
        if (onTranscript) onTranscript(finalStr)
      }
    }

    recognizer.onerror = (event) => {
      console.warn('[VoiceAssistant] WebSpeech error:', event.error)
      setIsListening(false)
      setInterimTranscript('')
    }

    recognizer.onend = () => {
      setIsListening(false)
      setInterimTranscript('')
      if (onSpeechEnd) onSpeechEnd()
    }

    recognitionRef.current = recognizer
    recognizer.start()
  }, [langMode, onTranscript, onSpeechEnd])

  // Unified start listening
  const startListening = useCallback(() => {
    if (!hasSTT) {
      setError('متصفحك لا يدعم التعرف على الصوت.')
      return
    }

    // Stop speaking first
    stopSpeaking()

    if (navigator.mediaDevices && typeof navigator.mediaDevices.getUserMedia === 'function') {
      startWhisperRecording()
    } else {
      startWebSpeech()
    }
  }, [hasSTT, stopSpeaking, startWhisperRecording, startWebSpeech])

  // Unified stop listening
  const stopListening = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
    }
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

  return {
    hasSTT,
    hasTTS,
    isListening,
    isTranscribing,
    isSpeaking,
    activeSpeakingId,
    transcript,
    interimTranscript,
    langMode,
    changeLangMode,
    availableLanguages: VOICE_LANGUAGES,
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
