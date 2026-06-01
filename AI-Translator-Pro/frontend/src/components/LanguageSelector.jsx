import LANGUAGES from '../services/languages'

export default function LanguageSelector({ value, onChange, includeAuto = false, label = 'Language' }) {
  const options = Object.entries(LANGUAGES).map(([code, name]) => (
    <option key={code} value={code}>{name}</option>
  ))

  return (
    <div className="flex flex-col gap-1">
      <label className="text-sm font-medium text-slate-600">{label}</label>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500"
      >
        {includeAuto && <option value="auto">Auto Detect</option>}
        {options}
      </select>
    </div>
  )
}
