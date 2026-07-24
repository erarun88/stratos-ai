import { useEffect, useState } from 'react'
import { getEngineers } from '../api/engineers'
import type { Engineer } from '../types/engineer'
import StatusBadge from '../components/engineers/StatusBadge'

export default function Engineers() {
  const [engineers, setEngineers] = useState<Engineer[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    getEngineers()
      .then((data) => {
        if (!cancelled) setEngineers(data)
      })
      .catch(() => {
        if (!cancelled) {
          setError('Could not load engineers. Is the backend running at http://localhost:8000?')
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  function showComingSoon(action: string) {
    setNotice(`${action} is not implemented yet — UI only.`)
  }

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">Engineers</h1>
          <p className="mt-1 text-sm text-slate-500">
            Everyone currently staffed across StratOS AI projects.
          </p>
        </div>

        <button
          type="button"
          onClick={() => showComingSoon('Add Engineer')}
          className="inline-flex items-center gap-1.5 rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white shadow-sm transition-colors hover:bg-slate-700"
        >
          <span className="text-base leading-none">+</span>
          Add Engineer
        </button>
      </div>

      {notice && (
        <div className="mt-4 flex items-center justify-between rounded-md border border-indigo-200 bg-indigo-50 px-4 py-2 text-sm text-indigo-700">
          {notice}
          <button
            type="button"
            onClick={() => setNotice(null)}
            className="ml-4 text-indigo-500 hover:text-indigo-700"
            aria-label="Dismiss"
          >
            &times;
          </button>
        </div>
      )}

      <div className="mt-6 overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm">
        {loading ? (
          <div className="p-8 text-center text-sm text-slate-500">Loading engineers…</div>
        ) : error ? (
          <div className="p-8 text-center text-sm text-red-600">{error}</div>
        ) : engineers.length === 0 ? (
          <div className="p-8 text-center text-sm text-slate-500">No engineers found.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead className="bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Name</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Email</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Role</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
                  <th className="px-4 py-3 text-left font-medium text-slate-500">Project ID</th>
                  <th className="px-4 py-3 text-right font-medium text-slate-500">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {engineers.map((engineer) => (
                  <tr key={engineer.id} className="hover:bg-slate-50">
                    <td className="px-4 py-3 font-medium text-slate-900">{engineer.name}</td>
                    <td className="px-4 py-3 text-slate-600">{engineer.email}</td>
                    <td className="px-4 py-3 text-slate-600">{engineer.role}</td>
                    <td className="px-4 py-3">
                      <StatusBadge status={engineer.status} />
                    </td>
                    <td className="px-4 py-3 text-slate-600">{engineer.project_id}</td>
                    <td className="px-4 py-3">
                      <div className="flex justify-end gap-2">
                        <button
                          type="button"
                          onClick={() => showComingSoon('Edit engineer')}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={() => showComingSoon('Change status')}
                          className="rounded-md border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                        >
                          Change Status
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
