export default function HistoryTable({ items, loading }) {
  if (loading) return <p className="text-slate-500">Loading history...</p>
  if (!items?.length) return <p className="text-slate-500">No translation history yet.</p>

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-slate-200">
        <thead className="bg-slate-50">
          <tr>
            <th className="px-4 py-2 text-left text-xs font-medium text-slate-600 uppercase">From → To</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-slate-600 uppercase">Original</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-slate-600 uppercase">Translation</th>
            <th className="px-4 py-2 text-left text-xs font-medium text-slate-600 uppercase">Time</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-slate-200">
          {items.map((item) => (
            <tr key={item.id || item.timestamp}>
              <td className="px-4 py-2 text-sm">{item.src_lang} → {item.target_lang}</td>
              <td className="px-4 py-2 text-sm max-w-xs truncate">{item.original_text}</td>
              <td className="px-4 py-2 text-sm max-w-xs truncate">{item.translated_text}</td>
              <td className="px-4 py-2 text-sm text-slate-500">{new Date(item.timestamp).toLocaleString()}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
