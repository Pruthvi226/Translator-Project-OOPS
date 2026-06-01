import { useState, useRef } from 'react'
import { LanguageSelector, TextInputBox, TranslationOutput, VoiceRecorder, AudioPlayer } from '../components'
import { translateApi, textToSpeechApi, speechToTextApi, getTTSFileUrl } from '../services/api'
import LANGUAGES from '../services/languages'

export default function SpeechTranslator() {
  const [inputText, setInputText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [srcLang, setSrcLang] = useState('auto')
  const [targetLang, setTargetLang] = useState('en')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)
  const mediaRecorderRef = useRef(null)
  const chunksRef = useRef([])

  const handleTranscript = (text) => {
    setInputText((prev) => prev + (prev ? ' ' : '') + text)
  }

  const handleTranslate = async () => {
    if (!inputText.trim()) return
    setError(null)
    setLoading(true)
    try {
      const { data } = await translateApi({
        text: inputText.trim(),
        src_lang: srcLang,
        target_lang: targetLang,
      })
      setTranslatedText(data.translated_text)
    } catch (e) {
      setError(e.response?.data?.detail || 'Translation failed')
    } finally {
      setLoading(false)
    }
  }

  const handleReadAloud = async () => {
    const text = translatedText.trim()
    if (!text) return
    setError(null)
    try {
      const { data } = await textToSpeechApi({ text, lang: targetLang })
      const fileId = data.audio_url?.split('/').pop()
      setAudioUrl(fileId ? getTTSFileUrl(fileId) : data.audio_url)
    } catch (e) {
      setError(e.response?.data?.detail || 'TTS failed')
    }
  }

  const speechLocale = srcLang === 'auto' ? 'en' : (LANGUAGES[srcLang] ? srcLang : 'en')

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Speech Translator</h1>
      <p className="text-slate-600">Use voice input, then translate and hear the result.</p>
      <TextInputBox value={inputText} onChange={setInputText} placeholder="Speak or type..." />
      <VoiceRecorder onTranscript={handleTranscript} language={speechLocale} />
      <div className="grid grid-cols-2 gap-4">
        <LanguageSelector value={srcLang} onChange={setSrcLang} includeAuto label="Source" />
        <LanguageSelector value={targetLang} onChange={setTargetLang} label="Target" />
      </div>
      <button
        onClick={handleTranslate}
        disabled={loading || !inputText.trim()}
        className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium disabled:opacity-50"
      >
        {loading ? 'Translating...' : 'Translate'}
      </button>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1">Translation</label>
        <TranslationOutput value={translatedText} />
      </div>
      <button
        onClick={handleReadAloud}
        disabled={!translatedText.trim()}
        className="px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg disabled:opacity-50"
      >
        🔊 Read aloud
      </button>
      {audioUrl && <AudioPlayer audioUrlOrFileId={audioUrl} />}
    </div>
  )
}
