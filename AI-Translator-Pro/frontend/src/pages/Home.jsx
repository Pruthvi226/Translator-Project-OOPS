import { Link } from 'react-router-dom'

export default function Home() {
  return (
    <div className="max-w-3xl mx-auto py-8">
      <h1 className="text-3xl font-bold text-slate-900 mb-2">AI Translator Pro</h1>
      <p className="text-slate-600 mb-8">
        Production-quality translation with speech, image OCR, grammar correction, and language learning.
      </p>
      <div className="grid sm:grid-cols-2 gap-4">
        <Link
          to="/translator"
          className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-amber-300 transition"
        >
          <h2 className="font-semibold text-lg mb-1">Text Translator</h2>
          <p className="text-sm text-slate-500">Translate text with auto-detect and grammar correction.</p>
        </Link>
        <Link
          to="/speech"
          className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-amber-300 transition"
        >
          <h2 className="font-semibold text-lg mb-1">Speech Translator</h2>
          <p className="text-sm text-slate-500">Speak and get real-time translation and TTS.</p>
        </Link>
        <Link
          to="/image"
          className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-amber-300 transition"
        >
          <h2 className="font-semibold text-lg mb-1">Image Translator</h2>
          <p className="text-sm text-slate-500">Upload an image; we extract and translate text (OCR).</p>
        </Link>
        <Link
          to="/dashboard"
          className="p-6 bg-white border border-slate-200 rounded-xl shadow-sm hover:shadow-md hover:border-amber-300 transition"
        >
          <h2 className="font-semibold text-lg mb-1">Dashboard</h2>
          <p className="text-sm text-slate-500">View your translation history (login required).</p>
        </Link>
      </div>
    </div>
  )
}
