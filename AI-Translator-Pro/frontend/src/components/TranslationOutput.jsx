export default function TranslationOutput({ value, explanation }) {
  return (
    <div className="space-y-2">
      <textarea
        value={value}
        readOnly
        rows={4}
        className="w-full px-4 py-3 border border-slate-200 bg-slate-50 rounded-lg resize-y"
      />
      {explanation && (
        <p className="text-sm text-slate-600 bg-amber-50 border border-amber-200 rounded-lg p-3">
          <span className="font-medium">Explanation:</span> {explanation}
        </p>
      )}
    </div>
  )
}
