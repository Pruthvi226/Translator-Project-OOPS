import { useState } from 'react'
import { LanguageSelector, TranslationOutput } from '../components'
import { imageTranslateApi } from '../services/api'

export default function ImageTranslator() {
  const [file, setFile] = useState(null)
  const [targetLang, setTargetLang] = useState('en')
  const [extractedText, setExtractedText] = useState('')
  const [translatedText, setTranslatedText] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!file) return
    setError(null)
    setLoading(true)
    try {
      const form = new FormData()
      form.append('file', file)
      form.append('target_lang', targetLang)
      const { data } = await imageTranslateApi(form)
      setExtractedText(data.extracted_text)
      setTranslatedText(data.translated_text)
    } catch (e) {
      setError(e.response?.data?.detail || 'Image translation failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-2xl font-bold">Image Translator</h1>
      <p className="text-slate-600">Upload an image; we extract text (OCR) and translate it.</p>
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-1">Image</label>
          <input
            type="file"
            accept="image/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:bg-amber-50 file:text-amber-800"
          />
        </div>
        <LanguageSelector value={targetLang} onChange={setTargetLang} label="Target language" />
        <button
          type="submit"
          disabled={loading || !file}
          className="px-4 py-2 bg-amber-500 hover:bg-amber-600 text-white rounded-lg font-medium disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Extract & Translate'}
        </button>
      </form>
      {error && <p className="text-red-600 text-sm">{error}</p>}
      {extractedText !== undefined && (
        <div className="space-y-2">
          <label className="block text-sm font-medium text-slate-600">Extracted text</label>
          <textarea readOnly value={extractedText} rows={3} className="w-full px-4 py-3 border border-slate-200 bg-slate-50 rounded-lg" />
        </div>
      )}
      {translatedText && (
        <div>
          <label className="block text-sm font-medium text-slate-600 mb-1">Translation</label>
          <TranslationOutput value={translatedText} />
        </div>
      )}
    </div>
  )
}
