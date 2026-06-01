export default function TextInputBox({ value, onChange, placeholder = 'Enter text...', readOnly = false, rows = 4 }) {
  return (
    <textarea
      value={value}
      onChange={(e) => onChange(e.target.value)}
      placeholder={placeholder}
      readOnly={readOnly}
      rows={rows}
      className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-amber-500 focus:border-amber-500 resize-y min-h-[100px]"
    />
  )
}
