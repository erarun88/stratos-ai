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
      <div className="rounded-lg border border-red-200 bg-red-50 p-3">
        <p className="text-xs text-red-800">Error: {error}</p>
      </div>
    )
  }

  return (
    <div className="rounded-lg border border-slate-200 bg-white p-3">
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-sm font-bold text-slate-900">📋 Recent Requests</h3>
        <span className="text-xs text-slate-500">{requests.length} requests</span>
      </div>

      {loading ? (
        <div className="text-center text-xs text-slate-500 py-2">Loading...</div>
      ) : requests.length === 0 ? (
        <div className="text-center text-xs text-slate-500 py-2">No requests found</div>
      ) : (
        <div className="flex gap-2 overflow-x-auto pb-2">
          {requests.map((requestId) => (
            <button
              key={requestId}
              onClick={() => onSelectRequest(requestId)}
              className={`flex-shrink-0 px-3 py-1.5 rounded text-xs font-mono transition-all whitespace-nowrap ${
                selectedRequest === requestId
                  ? 'bg-purple-600 text-white shadow-md'
                  : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
              }`}
            >
              {requestId.slice(0, 8)}...
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
