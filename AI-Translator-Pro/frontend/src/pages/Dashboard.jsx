import { useState, useEffect } from 'react'
import { HistoryTable } from '../components'
import { historyApi } from '../services/api'

export default function Dashboard() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    historyApi({ skip: 0, limit: 100 })
      .then(({ data }) => { if (!cancelled) setItems(data.items || []) })
      .catch((e) => { if (!cancelled) setError(e.response?.data?.detail || 'Failed to load history') })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [])

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Translation History</h1>
      {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
      <HistoryTable items={items} loading={loading} />
    </div>
  )
}
