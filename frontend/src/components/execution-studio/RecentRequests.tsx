interface RecentRequestsProps {
  requests: string[]
  selectedRequest: string | null
  onSelectRequest: (requestId: string) => void
  loading: boolean
  error: string | null
}

export default function RecentRequests({
  requests,
  selectedRequest,
  onSelectRequest,
  loading,
  error,
}: RecentRequestsProps) {
  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-xs text-red-800">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white">
      <div className="border-b border-slate-200 px-6 py-4">
        <h3 className="font-semibold text-slate-900">Recent Requests</h3>
        <p className="mt-1 text-xs text-slate-600">{requests.length} found</p>
      </div>

      <div className="max-h-96 overflow-y-auto divide-y divide-slate-200">
        {loading ? (
          <div className="px-6 py-4 text-center text-sm text-slate-500">
            Loading...
          </div>
        ) : requests.length === 0 ? (
          <div className="px-6 py-4 text-center text-sm text-slate-500">
            No requests found
          </div>
        ) : (
          requests.map((requestId) => (
            <button
              key={requestId}
              onClick={() => onSelectRequest(requestId)}
              className={`w-full px-6 py-3 text-left text-xs transition-colors ${
                selectedRequest === requestId
                  ? 'bg-purple-50 text-purple-900'
                  : 'hover:bg-slate-50 text-slate-600'
              }`}
            >
              <div className="font-mono text-xs">{requestId.slice(0, 12)}...</div>
              <div className="mt-1 text-xs text-slate-500">
                {new Date().toLocaleTimeString()}
              </div>
            </button>
          ))
        )}
      </div>
    </div>
  )
}
