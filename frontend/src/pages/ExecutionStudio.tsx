import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ExecutionTimeline from '../components/execution-studio/ExecutionTimeline'
import ExecutionMetrics from '../components/execution-studio/ExecutionMetrics'
import ExecutionGraph from '../components/execution-studio/ExecutionGraph'
import ArchitectureView from '../components/execution-studio/ArchitectureView'
import RecentRequests from '../components/execution-studio/RecentRequests'

export default function ExecutionStudio() {
  const [searchParams] = useSearchParams()
  const [requests, setRequests] = useState<string[]>([])
  const [selectedRequest, setSelectedRequest] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Get request_id from URL params
  const requestIdParam = searchParams.get('request_id')

  // Fetch recent requests
  useEffect(() => {
    fetchRecentRequests()
  }, [])

  // Set selected request
  useEffect(() => {
    if (requestIdParam) {
      setSelectedRequest(requestIdParam)
    } else if (requests.length > 0) {
      setSelectedRequest(requests[0])
    }
  }, [requests, requestIdParam])

  async function fetchRecentRequests() {
    try {
      setLoading(true)
      const response = await fetch('/api/execution-studio/requests', {
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) throw new Error('Failed to fetch requests')
      const data = await response.json()
      setRequests(data.requests || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  async function downloadEventLog() {
    if (!selectedRequest) return
    try {
      const response = await fetch(`/api/execution-studio/requests/${selectedRequest}/download`)
      if (!response.ok) throw new Error('Failed to download')

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `execution_${selectedRequest}.json`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  async function clearHistory() {
    if (!window.confirm('Delete all events older than 7 days? This cannot be undone.')) {
      return
    }
    try {
      const response = await fetch('/api/execution-studio/history?days=7', {
        method: 'DELETE',
      })
      if (!response.ok) throw new Error('Failed to clear history')
      const data = await response.json()
      alert(`✓ Cleared ${data.deleted_count} events older than 7 days`)
      fetchRecentRequests()
    } catch (err) {
      alert('Failed to clear history: ' + (err instanceof Error ? err.message : 'Unknown error'))
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-slate-900">🧠 AI Execution Studio</h1>
          <p className="mt-1 text-sm text-slate-600">
            Watch every step of your AI request in real-time
          </p>
        </div>
        <div className="flex gap-2">
          {selectedRequest && (
            <>
              <button
                onClick={downloadEventLog}
                className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
                title="Download event log as JSON"
              >
                ⬇️ Download Log
              </button>
              <button
                onClick={clearHistory}
                className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700"
                title="Delete events older than 7 days"
              >
                🗑️ Clear History
              </button>
            </>
          )}
          <button
            onClick={fetchRecentRequests}
            className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      {/* Recent Requests - Horizontal Bar */}
      <RecentRequests
        requests={requests}
        selectedRequest={selectedRequest}
        onSelectRequest={setSelectedRequest}
        loading={loading}
        error={error}
      />

      {/* Main Content - Full Width */}
      <div className="space-y-6">
        {selectedRequest ? (
          <>
            {/* Metrics */}
            <ExecutionMetrics requestId={selectedRequest} />

            {/* Architecture View */}
            <ArchitectureView requestId={selectedRequest} />

            {/* Semantic Execution Graph */}
            <ExecutionGraph requestId={selectedRequest} />

            {/* Timeline */}
            <ExecutionTimeline requestId={selectedRequest} />
          </>
        ) : (
          <div className="rounded-lg border border-slate-200 bg-slate-50 p-12 text-center">
            <p className="text-slate-600">
              {loading ? 'Loading requests...' : 'No requests found. Try asking a question in AI Chat.'}
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
