import { useState } from 'react'
import { LanguageSelector, TextInputBox, TranslationOutput, VoiceRecorder, AudioPlayer } from '../components'
import { translateApi, textToSpeechApi, getTTSFileUrl } from '../services/api'
import LANGUAGES from '../services/languages'

export default function Translator() {
  const [inputText, setInputText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [explanation, setExplanation] = useState(null)
  const [srcLang, setSrcLang] = useState('auto')
  const [targetLang, setTargetLang] = useState('en')
  const [correctGrammar, setCorrectGrammar] = useState(false)
  const [learningMode, setLearningMode] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [audioUrl, setAudioUrl] = useState(null)

  const handleTranslate = async () => {
    if (!inputText.trim()) return
    setError(null)
    setLoading(true)
    try {
      const { data } = await translateApi({
        text: inputText.trim(),
        src_lang: srcLang,
        target_lang: targetLang,
        correct_grammar: correctGrammar,
        learning_mode: learningMode,
      })
      setTranslatedText(data.translated_text)
      setExplanation(data.explanation || null)
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

  const swapLanguages = () => {
    setSrcLang(targetLang)
    setTargetLang(srcLang === 'auto' ? 'en' : srcLang)
    setInputText(translatedText)
    setTranslatedText(inputText)
  }

  const speechLang = srcLang === 'auto' ? 'en' : srcLang
  const speechLocale = LANGUAGES[speechLang] ? speechLang : 'en'

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Text Translator</h1>
      <TextInputBox value={inputText} onChange={setInputText} placeholder="Type or paste text..." />
      <VoiceRecorder
        onTranscript={(t) => setInputText((prev) => prev + (prev ? ' ' : '') + t)}
        language={speechLocale}
      />
      <div className="grid grid-cols-2 gap-4">
        <LanguageSelector value={srcLang} onChange={setSrcLang} includeAuto label="Source" />
        <LanguageSelector value={targetLang} onChange={setTargetLang} label="Target" />
      </div>
      <div className="flex items-center gap-4 flex-wrap">
        <button
          onClick={swapLanguages}
          className="px-3 py-1.5 border border-slate-300 rounded-lg hover:bg-slate-50"
        >
          ⇄ Swap
        </button>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={correctGrammar} onChange={(e) => setCorrectGrammar(e.target.checked)} />
          <span className="text-sm">Correct grammar</span>
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={learningMode} onChange={(e) => setLearningMode(e.target.checked)} />
          <span className="text-sm">Learning mode</span>
        </label>
      </div>
      <div className="flex gap-2">
        <button
          onClick={handleTranslate}
          disabled={loading || !inputText.trim()}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium disabled:opacity-50"
        >
          {loading ? 'Translating...' : 'Translate'}
        </button>
        <button
          onClick={handleReadAloud}
          disabled={!translatedText.trim()}
          className="px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-lg disabled:opacity-50"
        >
          🔊 Read aloud
        </button>
      </div>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      <div>
        <label className="block text-sm font-medium text-slate-600 mb-1">Translation</label>
        <TranslationOutput value={translatedText} explanation={explanation} />
      </div>
      {audioUrl && <AudioPlayer audioUrlOrFileId={audioUrl} />}
    </div>
  )
}
