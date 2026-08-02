import { useState, useEffect } from 'react'
import LearnMode from './LearnMode'
import BeforeAfterView from './BeforeAfterView'
import InteractiveReplayView from './InteractiveReplayView'

interface Component {
  id: string
  display_name: string
  type: string
  icon: string
  color: string
  status: string
  duration_ms: number
  position: [number, number]
  metrics: {
    tokens: number
    cost: number
    errors: number
  }
}

interface Connection {
  from: string
  to: string
  type: string
  flow_type: string
}

interface ArchitectureDiagram {
  components: Component[]
  connections: Connection[]
  statistics: {
    total_duration_ms: number
    total_tokens: number
    total_cost: number
    components_active: number
    total_components: number
    errors: number
  }
}

interface ArchitectureViewProps {
  requestId: string
}

export default function ArchitectureView({ requestId }: ArchitectureViewProps) {
  const [diagram, setDiagram] = useState<ArchitectureDiagram | null>(null)
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [viewMode, setViewMode] = useState<'details' | 'learn' | 'before-after' | 'replay'>('details')
  const [highlightedComponent, setHighlightedComponent] = useState<string | null>(null)

  useEffect(() => {
    fetchArchitecture()
  }, [requestId])

  async function fetchArchitecture() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/architecture/${requestId}/diagram`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!response.ok) throw new Error('Failed to fetch architecture')
      const data = await response.json()
      setDiagram(data)
      if (data.components?.length > 0) {
        setSelectedComponent(data.components[0].id)
      }
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string): string => {
    switch (status) {
      case 'completed': return '#10b981'  // green
      case 'failed': return '#ef4444'     // red
      case 'in_progress': return '#3b82f6' // blue
      default: return '#9ca3af'           // gray
    }
  }

  if (loading) {
    return <div className="p-6 text-center text-slate-500">Loading architecture...</div>
  }
  if (error) {
    return <div className="p-6 text-center text-red-500">Error: {error}</div>
  }
  if (!diagram) {
    return <div className="p-6 text-center text-slate-500">No architecture data</div>
  }

  const selectedComp = diagram.components.find(c => c.id === selectedComponent)

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-slate-200 bg-white p-6">
        <h2 className="text-2xl font-bold text-slate-900">🏗️ System Architecture</h2>
        <p className="text-sm text-slate-600 mt-1">Live component diagram and metrics</p>
      </div>

      {/* Statistics Grid */}
      <div className="grid grid-cols-5 gap-3">
        <StatCard
          label="Duration"
          value={`${diagram.statistics.total_duration_ms.toFixed(0)}ms`}
          icon="⏱️"
          color="blue"
        />
        <StatCard
          label="Tokens"
          value={diagram.statistics.total_tokens}
          icon="🔤"
          color="purple"
        />
        <StatCard
          label="Cost"
          value={`$${diagram.statistics.total_cost.toFixed(4)}`}
          icon="💰"
          color="green"
        />
        <StatCard
          label="Components"
          value={diagram.statistics.total_components}
          icon="⚙️"
          color="orange"
        />
        <StatCard
          label="Errors"
          value={diagram.statistics.errors}
          icon={diagram.statistics.errors > 0 ? "🔴" : "✅"}
          color={diagram.statistics.errors > 0 ? "red" : "green"}
        />
      </div>

      {/* Diagram and Details */}
      <div className="grid grid-cols-5 gap-6">
        {/* Diagram */}
        <div className="col-span-3">
          <div className="bg-white rounded-lg border border-slate-200 p-4 min-h-[450px]">
            <svg width="100%" height="400" viewBox="0 0 900 500" className="border border-slate-100 rounded">
              {/* Draw connections */}
              {diagram.connections.map((conn, i) => {
                const fromComp = diagram.components.find(c => c.id === conn.from)
                const toComp = diagram.components.find(c => c.id === conn.to)
                if (!fromComp || !toComp) return null

                const fromX = (fromComp.position[0] / 100) * 800 + 50
                const fromY = (fromComp.position[1] / 100) * 400 + 20
                const toX = (toComp.position[0] / 100) * 800 + 50
                const toY = (toComp.position[1] / 100) * 400 + 20

                return (
                  <g key={i}>
                    <line
                      x1={fromX}
                      y1={fromY}
                      x2={toX}
                      y2={toY}
                      stroke="#cbd5e1"
                      strokeWidth="2"
                      markerEnd="url(#arrowhead)"
                    />
                  </g>
                )
              })}

              {/* Draw components */}
              {diagram.components.map((comp) => {
                const x = (comp.position[0] / 100) * 800
                const y = (comp.position[1] / 100) * 400
                const isSelected = selectedComponent === comp.id
                const isHighlighted = highlightedComponent === comp.id
                const statusColor = getStatusColor(comp.status)

                return (
                  <g
                    key={comp.id}
                    onClick={() => setSelectedComponent(comp.id)}
                    style={{ cursor: 'pointer' }}
                  >
                    {/* Card background */}
                    <rect
                      x={x}
                      y={y}
                      width="90"
                      height="70"
                      fill={isHighlighted ? '#fef3c7' : isSelected ? '#f3e8ff' : '#f8fafc'}
                      stroke={isHighlighted ? '#fbbf24' : isSelected ? '#a78bfa' : statusColor}
                      strokeWidth={isHighlighted ? 4 : isSelected ? 3 : 2}
                      rx="6"
                    />

                    {/* Icon */}
                    <text x={x + 45} y={y + 22} textAnchor="middle" fontSize="20">
                      {comp.icon}
                    </text>

                    {/* Name */}
                    <text
                      x={x + 45}
                      y={y + 42}
                      textAnchor="middle"
                      fontSize="11"
                      fontWeight="bold"
                      fill="#0f172a"
                    >
                      {comp.display_name}
                    </text>

                    {/* Duration */}
                    <text x={x + 45} y={y + 58} textAnchor="middle" fontSize="9" fill="#64748b">
                      {comp.duration_ms.toFixed(0)}ms
                    </text>
                  </g>
                )
              })}

              {/* Arrow marker */}
              <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="10" refX="5" refY="5" orient="auto">
                  <polygon points="0 0, 10 5, 0 10" fill="#cbd5e1" />
                </marker>
              </defs>
            </svg>

            {/* Legend */}
            <div className="mt-6 flex gap-8 text-sm">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#10b981' }}></div>
                <span>Completed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#3b82f6' }}></div>
                <span>In Progress</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#ef4444' }}></div>
                <span>Failed</span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 rounded" style={{ backgroundColor: '#9ca3af' }}></div>
                <span>Unknown</span>
              </div>
            </div>
          </div>
        </div>

        {/* Component Details / Learn Mode */}
        <div className="col-span-2">
          {selectedComp ? (
            <div className="bg-white rounded-lg border border-slate-200 p-4 sticky top-4">
              <div className="flex items-center gap-2 pb-3 border-b border-slate-200 mb-3">
                <span className="text-2xl">{selectedComp.icon}</span>
                <div>
                  <h3 className="text-base font-bold text-slate-900">{selectedComp.display_name}</h3>
                  <p className="text-xs text-slate-600 capitalize">{selectedComp.type}</p>
                </div>
              </div>

              {/* View Mode Tabs */}
              <div className="flex gap-1 mb-3 border-b border-slate-200 overflow-x-auto">
                <button
                  onClick={() => setViewMode('details')}
                  className={`px-2 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                    viewMode === 'details'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  📊 Details
                </button>
                <button
                  onClick={() => setViewMode('learn')}
                  className={`px-2 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                    viewMode === 'learn'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  📚 Learn
                </button>
                <button
                  onClick={() => setViewMode('before-after')}
                  className={`px-2 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                    viewMode === 'before-after'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  🔄 B/A
                </button>
                <button
                  onClick={() => setViewMode('replay')}
                  className={`px-2 py-1.5 text-xs font-medium whitespace-nowrap transition-colors ${
                    viewMode === 'replay'
                      ? 'text-blue-600 border-b-2 border-blue-600'
                      : 'text-slate-600 hover:text-slate-900'
                  }`}
                >
                  ▶️ Replay
                </button>
              </div>

              {/* Details View */}
              {viewMode === 'details' && (
                <div className="space-y-2 max-h-[70vh] overflow-y-auto text-sm">
                  {/* Status */}
                  <div className="p-2 rounded" style={{ backgroundColor: getStatusColor(selectedComp.status) + '20', borderLeft: `3px solid ${getStatusColor(selectedComp.status)}` }}>
                    <p className="text-xs font-semibold text-slate-900">Status</p>
                    <p className="text-sm font-bold capitalize" style={{ color: getStatusColor(selectedComp.status) }}>
                      {selectedComp.status}
                    </p>
                  </div>

                  {/* Metrics */}
                  <div className="space-y-1.5 text-xs">
                    <div>
                      <p className="text-slate-600 font-semibold">Duration</p>
                      <p className="font-bold text-slate-900">{selectedComp.duration_ms.toFixed(1)}ms</p>
                    </div>

                    <div>
                      <p className="text-slate-600 font-semibold">Tokens</p>
                      <p className="font-bold text-slate-900">{selectedComp.metrics.tokens}</p>
                    </div>

                    <div>
                      <p className="text-slate-600 font-semibold">Cost</p>
                      <p className="font-bold text-slate-900">${selectedComp.metrics.cost.toFixed(4)}</p>
                    </div>

                    {selectedComp.metrics.errors > 0 && (
                      <div className="p-2 bg-red-50 rounded border border-red-200">
                        <p className="text-red-900 font-semibold">Errors: {selectedComp.metrics.errors}</p>
                      </div>
                    )}
                  </div>

                  {/* Children count */}
                  <div className="pt-2 border-t border-slate-200 text-xs text-slate-600">
                    {diagram.connections.filter(c => c.from === selectedComp.id).length} downstream
                  </div>
                </div>
              )}

              {/* Learn View */}
              {viewMode === 'learn' && (
                <LearnMode componentName={selectedComp.id} />
              )}

              {/* Before/After View */}
              {viewMode === 'before-after' && (
                <BeforeAfterView requestId={requestId} />
              )}

              {/* Interactive Replay View */}
              {viewMode === 'replay' && (
                <InteractiveReplayView
                  requestId={requestId}
                  onComponentHighlight={setHighlightedComponent}
                />
              )}
            </div>
          ) : (
            <div className="bg-slate-50 rounded-lg p-6 text-center text-slate-500">
              Click a component to see details
            </div>
          )}
        </div>
      </div>

      {/* Components List */}
      <div className="rounded-lg border border-slate-200 bg-white p-4">
        <h3 className="text-sm font-bold text-slate-900 mb-3">📋 Components</h3>
        <div className="grid grid-cols-3 gap-2">
          {diagram.components.map(comp => (
            <button
              key={comp.id}
              onClick={() => setSelectedComponent(comp.id)}
              className={`p-2 rounded border text-left transition-all text-xs ${
                selectedComponent === comp.id
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-slate-200 bg-slate-50 hover:bg-slate-100'
              }`}
            >
              <div className="flex items-center gap-1 mb-1">
                <span className="text-lg">{comp.icon}</span>
                <span className="font-semibold text-slate-900 text-xs">{comp.display_name}</span>
              </div>
              <div className="flex gap-2 text-xs text-slate-600">
                <span>{comp.duration_ms.toFixed(0)}ms</span>
                <span>{comp.metrics.tokens}tk</span>
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}

function StatCard({
  label,
  value,
  icon,
  color,
}: {
  label: string
  value: any
  icon: string
  color: string
}) {
  const bgColors: Record<string, string> = {
    blue: 'bg-blue-50 border-blue-200',
    purple: 'bg-purple-50 border-purple-200',
    green: 'bg-green-50 border-green-200',
    orange: 'bg-orange-50 border-orange-200',
    red: 'bg-red-50 border-red-200',
  }

  const textColors: Record<string, string> = {
    blue: 'text-blue-900',
    purple: 'text-purple-900',
    green: 'text-green-900',
    orange: 'text-orange-900',
    red: 'text-red-900',
  }

  return (
    <div className={`rounded-lg border p-2 text-center ${bgColors[color]}`}>
      <div className="text-xl mb-1">{icon}</div>
      <div className={`text-lg font-bold ${textColors[color]}`}>{value}</div>
      <div className={`text-xs ${textColors[color]} opacity-75`}>{label}</div>
    </div>
  )
}
