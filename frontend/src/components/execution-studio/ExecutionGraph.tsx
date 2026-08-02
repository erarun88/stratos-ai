import { useState, useEffect, useMemo } from 'react'

interface SemanticEvent {
  event_id: string
  request_id: string
  parent_event_id: string | null
  purpose: string
  reason: string
  description: string
  component: string
  component_type: string
  component_role: string
  action: string
  input: {
    type: string
    description: string
    key_fields: Record<string, any>
  }
  output: {
    type: string
    description: string
    key_fields: Record<string, any>
    confidence: number
  }
  status: string
  duration_ms: number
  tokens_used: number
  cost: number
  decision?: {
    type: string
    description: string
    options_considered: number
    rationale: string
  }
  related_events: Array<{
    event_id: string
    relationship: string
    description: string
  }>
  dependencies: Array<{
    component: string
    reason: string
  }>
}

interface ExecutionGraphProps {
  requestId: string
}

export default function ExecutionGraph({ requestId }: ExecutionGraphProps) {
  const [events, setEvents] = useState<SemanticEvent[]>([])
  const [selectedEvent, setSelectedEvent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'narrative' | 'graph'>('narrative')

  useEffect(() => {
    fetchSemanticTrace()
  }, [requestId])

  async function fetchSemanticTrace() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/semantic/requests/${requestId}/trace`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!response.ok) throw new Error('Failed to fetch semantic trace')
      const data = await response.json()
      setEvents(data.events || [])
      if (data.events?.length > 0) {
        setSelectedEvent(data.events[0].event_id)
      }
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const selectedEventData = useMemo(
    () => events.find(e => e.event_id === selectedEvent),
    [events, selectedEvent]
  )

  const rootEvents = useMemo(
    () => events.filter(e => !e.parent_event_id),
    [events]
  )

  const getChildrenOf = (parentId: string) => {
    return events.filter(e => e.parent_event_id === parentId)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-300'
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-300'
      case 'in_progress':
        return 'bg-blue-100 text-blue-800 border-blue-300'
      case 'started':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300'
      default:
        return 'bg-slate-100 text-slate-800 border-slate-300'
    }
  }

  const getComponentTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      orchestrator: 'bg-purple-50 border-purple-200',
      specialist_agent: 'bg-blue-50 border-blue-200',
      tool: 'bg-green-50 border-green-200',
      inference: 'bg-orange-50 border-orange-200',
      validator: 'bg-red-50 border-red-200',
      workflow: 'bg-indigo-50 border-indigo-200',
      decision_point: 'bg-yellow-50 border-yellow-200',
    }
    return colors[type] || 'bg-slate-50 border-slate-200'
  }

  if (loading) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-center text-slate-500">Loading semantic trace...</p>
      </div>
    )
  }

  if (error || events.length === 0) {
    return (
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <p className="text-center text-slate-500">
          {error || 'No semantic events found'}
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* View Mode Toggle */}
      <div className="flex gap-2">
        <button
          onClick={() => setViewMode('narrative')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'narrative'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          📖 Execution Narrative
        </button>
        <button
          onClick={() => setViewMode('graph')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            viewMode === 'graph'
              ? 'bg-blue-600 text-white'
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          🔗 Dependency Graph
        </button>
      </div>

      {/* Narrative View */}
      {viewMode === 'narrative' && (
        <div className="grid grid-cols-3 gap-6">
          {/* Event List */}
          <div className="col-span-1 space-y-2 max-h-[70vh] overflow-y-auto">
            <h3 className="font-semibold text-slate-900 sticky top-0 bg-white pb-2">
              Execution Events ({events.length})
            </h3>
            {rootEvents.map(event => (
              <div key={event.event_id} className="space-y-1">
                <button
                  onClick={() => setSelectedEvent(event.event_id)}
                  className={`w-full text-left p-3 rounded-lg border-2 transition-all ${
                    selectedEvent === event.event_id
                      ? 'border-blue-500 bg-blue-50'
                      : `border-slate-200 ${getComponentTypeColor(event.component_type)}`
                  }`}
                >
                  <p className="font-semibold text-sm">{event.component}</p>
                  <p className="text-xs text-slate-600">{event.action}</p>
                  <p className="text-xs text-slate-500">{event.purpose}</p>
                </button>
                {getChildrenOf(event.event_id).map(child => (
                  <div key={child.event_id} className="ml-3 space-y-1">
                    <button
                      onClick={() => setSelectedEvent(child.event_id)}
                      className={`w-full text-left p-2 rounded border transition-all ${
                        selectedEvent === child.event_id
                          ? 'border-blue-400 bg-blue-50'
                          : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
                      }`}
                    >
                      <p className="text-sm font-medium">{child.component}</p>
                      <p className="text-xs text-slate-600">{child.action}</p>
                    </button>
                  </div>
                ))}
              </div>
            ))}
          </div>

          {/* Event Details */}
          <div className="col-span-2 space-y-4">
            {selectedEventData ? (
              <div className="rounded-lg border-2 border-blue-200 bg-white p-6 space-y-6">
                {/* Header */}
                <div className={`p-4 rounded-lg border-2 ${getStatusColor(selectedEventData.status)}`}>
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <h2 className="text-2xl font-bold">{selectedEventData.component}</h2>
                      <p className="text-lg text-slate-600">{selectedEventData.action}</p>
                    </div>
                    <span className="text-sm font-semibold px-3 py-1 rounded bg-white">
                      {selectedEventData.status.toUpperCase()}
                    </span>
                  </div>
                  <div className="space-y-1 text-sm">
                    <p><span className="font-semibold">Type:</span> {selectedEventData.component_type}</p>
                    {selectedEventData.component_role && (
                      <p><span className="font-semibold">Role:</span> {selectedEventData.component_role}</p>
                    )}
                  </div>
                </div>

                {/* Purpose & Reason */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <h3 className="font-semibold text-purple-900 mb-2">💡 Purpose</h3>
                    <p className="text-sm text-purple-800">{selectedEventData.purpose}</p>
                  </div>
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <h3 className="font-semibold text-blue-900 mb-2">🎯 Reason</h3>
                    <p className="text-sm text-blue-800">
                      {selectedEventData.reason || 'Part of request processing'}
                    </p>
                  </div>
                </div>

                {/* Description */}
                {selectedEventData.description && (
                  <div className="p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <h3 className="font-semibold text-slate-900 mb-2">📝 What Happened</h3>
                    <p className="text-sm text-slate-700">{selectedEventData.description}</p>
                  </div>
                )}

                {/* Input Summary */}
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <h3 className="font-semibold text-green-900 mb-2">📥 Input</h3>
                  <p className="text-sm text-green-800 mb-2">
                    <span className="font-medium">{selectedEventData.input.type}:</span> {selectedEventData.input.description}
                  </p>
                  {Object.keys(selectedEventData.input.key_fields).length > 0 && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-green-700 font-medium">Details</summary>
                      <pre className="mt-2 p-2 bg-white rounded border border-green-200 overflow-x-auto">
                        {JSON.stringify(selectedEventData.input.key_fields, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>

                {/* Output Summary */}
                <div className="p-4 bg-orange-50 rounded-lg border border-orange-200">
                  <h3 className="font-semibold text-orange-900 mb-2">📤 Output</h3>
                  <p className="text-sm text-orange-800 mb-1">
                    <span className="font-medium">{selectedEventData.output.type}:</span> {selectedEventData.output.description}
                  </p>
                  <div className="flex gap-3 text-xs text-orange-700 mb-2">
                    <span>Confidence: {(selectedEventData.output.confidence * 100).toFixed(0)}%</span>
                  </div>
                  {Object.keys(selectedEventData.output.key_fields).length > 0 && (
                    <details className="text-xs">
                      <summary className="cursor-pointer text-orange-700 font-medium">Details</summary>
                      <pre className="mt-2 p-2 bg-white rounded border border-orange-200 overflow-x-auto">
                        {JSON.stringify(selectedEventData.output.key_fields, null, 2)}
                      </pre>
                    </details>
                  )}
                </div>

                {/* Decision */}
                {selectedEventData.decision && (
                  <div className="p-4 bg-yellow-50 rounded-lg border border-yellow-200">
                    <h3 className="font-semibold text-yellow-900 mb-2">🤔 Decision</h3>
                    <p className="text-sm text-yellow-800 mb-2">
                      <span className="font-medium">{selectedEventData.decision.type}:</span> {selectedEventData.decision.description}
                    </p>
                    {selectedEventData.decision.rationale && (
                      <p className="text-xs text-yellow-700"><span className="font-medium">Why:</span> {selectedEventData.decision.rationale}</p>
                    )}
                    {selectedEventData.decision.options_considered > 0 && (
                      <p className="text-xs text-yellow-700">Options considered: {selectedEventData.decision.options_considered}</p>
                    )}
                  </div>
                )}

                {/* Dependencies */}
                {selectedEventData.dependencies.length > 0 && (
                  <div className="p-4 bg-red-50 rounded-lg border border-red-200">
                    <h3 className="font-semibold text-red-900 mb-2">🔗 Dependencies</h3>
                    <ul className="text-sm text-red-800 space-y-1">
                      {selectedEventData.dependencies.map((dep, i) => (
                        <li key={i} className="flex gap-2">
                          <span>•</span>
                          <span><span className="font-medium">{dep.component}:</span> {dep.reason}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Metrics */}
                <div className="p-4 bg-slate-50 rounded-lg border border-slate-200 grid grid-cols-4 gap-4 text-center">
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {selectedEventData.duration_ms.toFixed(1)}
                    </p>
                    <p className="text-xs text-slate-600">Duration (ms)</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {selectedEventData.tokens_used}
                    </p>
                    <p className="text-xs text-slate-600">Tokens</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      ${selectedEventData.cost.toFixed(4)}
                    </p>
                    <p className="text-xs text-slate-600">Cost</p>
                  </div>
                  <div>
                    <p className="text-2xl font-bold text-slate-900">
                      {getChildrenOf(selectedEventData.event_id).length}
                    </p>
                    <p className="text-xs text-slate-600">Children</p>
                  </div>
                </div>
              </div>
            ) : (
              <div className="p-8 text-center text-slate-500">
                Select an event to see details
              </div>
            )}
          </div>
        </div>
      )}

      {/* Graph View */}
      {viewMode === 'graph' && (
        <div className="p-6 bg-white rounded-lg border border-slate-200">
          <h3 className="font-semibold text-slate-900 mb-4">Execution Flow & Dependencies</h3>
          <div className="space-y-4">
            {events.map(event => (
              <div key={event.event_id} className="p-4 rounded-lg border-2 border-slate-200 hover:border-blue-300 bg-slate-50">
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-semibold text-slate-900">{event.component} :: {event.action}</h4>
                    <p className="text-sm text-slate-600">{event.purpose}</p>
                  </div>
                  <span className={`text-xs font-semibold px-2 py-1 rounded ${getStatusColor(event.status)}`}>
                    {event.status}
                  </span>
                </div>

                {/* Parents */}
                {event.parent_event_id && (
                  <div className="text-xs text-slate-600 mb-2">
                    ← Parent: {events.find(e => e.event_id === event.parent_event_id)?.component}
                  </div>
                )}

                {/* Related Events */}
                {event.related_events.length > 0 && (
                  <div className="text-xs text-slate-600 mb-2">
                    {event.related_events.map((rel, i) => (
                      <div key={i}>
                        → {rel.relationship}: {rel.description}
                      </div>
                    ))}
                  </div>
                )}

                {/* Dependencies */}
                {event.dependencies.length > 0 && (
                  <div className="text-xs text-red-600">
                    {event.dependencies.map((dep, i) => (
                      <div key={i}>
                        📌 Needs {dep.component}: {dep.reason}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
