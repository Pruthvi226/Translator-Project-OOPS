import { useState, useRef, useCallback } from 'react'

export default function VoiceRecorder({ onTranscript, language = 'en', disabled }) {
  const [isListening, setIsListening] = useState(false)
  const [error, setError] = useState(null)
  const recognitionRef = useRef(null)

  const startListening = useCallback(() => {
    setError(null)
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Speech recognition is not supported in this browser.')
      return
    }
    const Recognition = window.SpeechRecognition || window.webkitSpeechRecognition
    const recognition = new Recognition()
    recognition.lang = language === 'zh-cn' ? 'zh-CN' : language === 'zh-tw' ? 'zh-TW' : `${language}-${language.toUpperCase()}`
    recognition.continuous = false
    recognition.interimResults = false
    recognition.onresult = (e) => {
      const transcript = e.results[0][0].transcript
      onTranscript(transcript)
    }
    recognition.onerror = (e) => setError(e.error || 'Recognition error')
    recognition.onend = () => setIsListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setIsListening(true)
  }, [language, onTranscript])

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop()
      recognitionRef.current = null
    }
    setIsListening(false)
  }, [])

  return (
    <div className="flex flex-col items-center gap-2">
      <button
        type="button"
        onClick={isListening ? stopListening : startListening}
        disabled={disabled}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition ${
          isListening
            ? 'bg-red-500 hover:bg-red-600 text-white'
            : 'bg-slate-700 hover:bg-slate-800 text-white'
        } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        {isListening ? (
          <>🔴 Listening...</>
        ) : (
          <>🎤 Voice Input</>
        )}
      </button>
      {error && <p className="text-sm text-red-600">{error}</p>}
    </div>
  )
}
