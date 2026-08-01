import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import ExecutionTimeline from '../components/execution-studio/ExecutionTimeline'
import ExecutionMetrics from '../components/execution-studio/ExecutionMetrics'
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
        <button
          onClick={fetchRecentRequests}
          className="rounded-lg bg-purple-600 px-4 py-2 text-sm font-medium text-white hover:bg-purple-700"
        >
          Refresh
        </button>
      </div>

      {/* Main Content */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-4">
        {/* Sidebar - Recent Requests */}
        <div className="lg:col-span-1">
          <RecentRequests
            requests={requests}
            selectedRequest={selectedRequest}
            onSelectRequest={setSelectedRequest}
            loading={loading}
            error={error}
          />
        </div>

        {/* Main Area */}
        <div className="space-y-6 lg:col-span-3">
          {selectedRequest ? (
            <>
              {/* Metrics */}
              <ExecutionMetrics requestId={selectedRequest} />

              {/* Timeline */}
              <ExecutionTimeline requestId={selectedRequest} />
            </>
          ) : (
            <div className="rounded-lg border border-slate-200 bg-slate-50 p-8 text-center">
              <p className="text-slate-600">
                {loading ? 'Loading requests...' : 'No requests found. Try asking a question in AI Chat.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
