import { useState, useEffect } from 'react'
import ExecutionTreeView from './ExecutionTreeView'

interface ExecutionEvent {
  event_id: string
  request_id: string
  parent_event_id: string | null
  timestamp: string
  component: string
  action: string
  status: string
  duration_ms: number
  tokens_used: number
  cost: number
  metadata: Record<string, any>
  error?: string
}

interface ExecutionTimelineProps {
  requestId: string
}

export default function ExecutionTimeline({ requestId }: ExecutionTimelineProps) {
  const [events, setEvents] = useState<ExecutionEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'tree' | 'timeline'>('tree')

  useEffect(() => {
    fetchEvents()
  }, [requestId])

  async function fetchEvents() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/requests/${requestId}/events`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      )
      if (!response.ok) throw new Error('Failed to fetch events')
      const data = await response.json()
      setEvents(data.events || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-center text-slate-500">Loading events...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-6">
        <p className="text-red-800">Error: {error}</p>
      </div>
    )
  }

  if (events.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-center text-slate-500">No events found</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* View Mode Selector */}
      <div className="flex gap-2">
        <button
          onClick={() => setViewMode('tree')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'tree'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          🌳 Execution Tree
        </button>
        <button
          onClick={() => setViewMode('timeline')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'timeline'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          ⏱️ Timeline
        </button>
      </div>

      {/* Tree View */}
      {viewMode === 'tree' && <ExecutionTreeView events={events} />}

      {/* Timeline View (original) */}
      {viewMode === 'timeline' && (
        <div className="rounded-lg border border-slate-200 bg-white">
          <div className="border-b border-slate-200 px-6 py-4">
            <h2 className="text-lg font-semibold text-slate-900">Execution Timeline</h2>
            <p className="text-sm text-slate-600">{events.length} events</p>
          </div>
          <TimelineList events={events} />
        </div>
      )}
    </div>
  )
}

function TimelineList({ events }: { events: ExecutionEvent[] }) {
  const [expandedEvent, setExpandedEvent] = useState<string | null>(null)

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800'
      case 'started':
        return 'bg-yellow-100 text-yellow-800'
      default:
        return 'bg-slate-100 text-slate-800'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return '✓'
      case 'failed':
        return '✕'
      case 'in_progress':
        return '⟳'
      case 'started':
        return '○'
      default:
        return '○'
    }
  }

  return (
    <div className="divide-y divide-slate-200">
      {events.map((event, index) => (
        <div key={event.event_id} className="p-6">
          <div
            className="flex cursor-pointer items-center gap-4"
            onClick={() =>
              setExpandedEvent(
                expandedEvent === event.event_id ? null : event.event_id
              )
            }
          >
            <div className="flex flex-col items-center">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${getStatusColor(
                  event.status
                )}`}
              >
                {getStatusIcon(event.status)}
              </div>
              {index < events.length - 1 && (
                <div className="h-8 w-0.5 bg-slate-200" />
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-slate-900">
                  {event.component}
                </span>
                <span className="text-sm text-slate-600">
                  {event.action}
                </span>
                <span
                  className={`inline-block rounded px-2 py-0.5 text-xs font-medium ${getStatusColor(
                    event.status
                  )}`}
                >
                  {event.status}
                </span>
              </div>
              <div className="mt-1 text-xs text-slate-500">
                {event.duration_ms > 0 && (
                  <span>{event.duration_ms.toFixed(0)}ms</span>
                )}
                {event.tokens_used > 0 && (
                  <span className="ml-3">{event.tokens_used} tokens</span>
                )}
                {event.cost > 0 && (
                  <span className="ml-3">${event.cost.toFixed(4)}</span>
                )}
              </div>
            </div>

            <div className="text-slate-400">
              {expandedEvent === event.event_id ? '▼' : '▶'}
            </div>
          </div>

          {expandedEvent === event.event_id && (
            <div className="mt-4 border-t border-slate-200 pt-4">
              {event.error && (
                <div className="mb-4 rounded-lg bg-red-50 p-3">
                  <p className="text-xs font-semibold text-red-800">Error</p>
                  <p className="mt-1 text-xs text-red-700">{event.error}</p>
                </div>
              )}

              <div className="space-y-2">
                <div className="text-xs">
                  <span className="font-semibold text-slate-900">Time</span>
                  <p className="text-slate-600">
                    {new Date(event.timestamp).toLocaleTimeString()}
                  </p>
                </div>

                {Object.keys(event.metadata).length > 0 && (
                  <div className="text-xs">
                    <span className="font-semibold text-slate-900">
                      Metadata
                    </span>
                    <pre className="mt-1 overflow-x-auto rounded bg-slate-50 p-2 text-xs text-slate-600">
                      {JSON.stringify(event.metadata, null, 2)}
                    </pre>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
