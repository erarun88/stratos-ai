import { useState, useEffect } from 'react'

interface InputData {
  type: string
  description: string
  key_fields: Record<string, any>
}

interface OutputData {
  type: string
  description: string
  key_fields: Record<string, any>
  confidence: number
}

interface ComponentTransformation {
  component: string
  component_type: string
  action: string
  status: string
  input: InputData
  output: OutputData
  duration_ms: number
  tokens_used: number
  cost: number
  error: string | null
}

interface BeforeAfterViewProps {
  requestId: string
}

export default function BeforeAfterView({ requestId }: BeforeAfterViewProps) {
  const [data, setData] = useState<ComponentTransformation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchBeforeAfter()
  }, [requestId])

  async function fetchBeforeAfter() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/before-after/${requestId}`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!response.ok) throw new Error('Failed to fetch before/after data')
      const result = await response.json()
      setData(result.transformations || [])
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-4 text-center text-slate-500">Loading transformations...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">Error: {error}</div>
  }

  if (data.length === 0) {
    return <div className="p-4 text-center text-slate-500">No transformation data available</div>
  }

  return (
    <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
      {data.map((transform, idx) => (
        <TransformationCard key={idx} transform={transform} index={idx} />
      ))}
    </div>
  )
}

function TransformationCard({ transform, index }: { transform: ComponentTransformation; index: number }) {
  const [expandInput, setExpandInput] = useState(false)
  const [expandOutput, setExpandOutput] = useState(false)

  const statusEmoji = {
    completed: '✅',
    failed: '❌',
    in_progress: '⏳',
    started: '⚪',
  }[transform.status] || '❓'

  return (
    <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
      {/* Header - Compact */}
      <div className="bg-slate-50 border-b border-slate-200 p-4">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-3">
            <span className="text-lg font-bold text-slate-400">#{index + 1}</span>
            <div>
              <h4 className="text-base font-bold text-slate-900">{transform.component}</h4>
              <p className="text-xs text-slate-500">{transform.action}</p>
            </div>
          </div>
          <span className="text-2xl">{statusEmoji}</span>
        </div>

        {/* Metrics - single row */}
        <div className="flex gap-4 text-xs">
          <span className="text-slate-600">⏱️ <span className="font-semibold">{transform.duration_ms.toFixed(1)}ms</span></span>
          <span className="text-slate-600">🔤 <span className="font-semibold">{transform.tokens_used}</span></span>
          <span className="text-slate-600">💰 <span className="font-semibold">${transform.cost.toFixed(4)}</span></span>
          {transform.error && <span className="text-red-600 font-semibold">Error</span>}
        </div>
      </div>

      {/* Content - Vertical layout */}
      <div className="p-4 space-y-4">
        {/* Input Section */}
        <div className="border border-blue-200 rounded-lg bg-blue-50 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xl">📥</span>
              <div>
                <h5 className="font-bold text-slate-900 text-sm">Input Data</h5>
                <p className="text-xs text-slate-600">{transform.input.type}</p>
              </div>
            </div>
            {Object.keys(transform.input.key_fields).length > 0 && (
              <button
                onClick={() => setExpandInput(!expandInput)}
                className="text-xs text-blue-600 hover:text-blue-700 font-medium"
              >
                {expandInput ? '▼ Hide' : '▶ Show'} Details
              </button>
            )}
          </div>

          <p className="text-sm text-slate-700 mb-2">{transform.input.description}</p>

          {expandInput && Object.keys(transform.input.key_fields).length > 0 && (
            <div className="mt-3 p-3 bg-white rounded border border-blue-100 max-h-[150px] overflow-y-auto">
              <div className="text-xs font-mono space-y-1">
                {Object.entries(transform.input.key_fields).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-blue-600 font-semibold flex-shrink-0">{key}:</span>
                    <span className="text-slate-700 break-words">{String(value).substring(0, 100)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Arrow - Processing */}
        <div className="flex items-center justify-center py-2">
          <div className="text-center">
            <div className="text-2xl mb-1">⚙️</div>
            <p className="text-xs text-slate-500 font-medium capitalize">{transform.action}</p>
          </div>
        </div>

        {/* Output Section */}
        <div className="border border-green-200 rounded-lg bg-green-50 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <span className="text-xl">📤</span>
              <div>
                <h5 className="font-bold text-slate-900 text-sm">Output Data</h5>
                <p className="text-xs text-slate-600">{transform.output.type}</p>
              </div>
            </div>
            {Object.keys(transform.output.key_fields).length > 0 && (
              <button
                onClick={() => setExpandOutput(!expandOutput)}
                className="text-xs text-green-600 hover:text-green-700 font-medium"
              >
                {expandOutput ? '▼ Hide' : '▶ Show'} Details
              </button>
            )}
          </div>

          <p className="text-sm text-slate-700 mb-3">{transform.output.description}</p>

          {/* Confidence Bar */}
          <div className="mb-3 p-2 bg-white rounded border border-green-100">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-semibold text-slate-600">Confidence</span>
              <span className="text-xs font-bold text-green-700">{(transform.output.confidence * 100).toFixed(0)}%</span>
            </div>
            <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
              <div
                className="h-full bg-green-500 transition-all"
                style={{ width: `${transform.output.confidence * 100}%` }}
              />
            </div>
          </div>

          {expandOutput && Object.keys(transform.output.key_fields).length > 0 && (
            <div className="mt-3 p-3 bg-white rounded border border-green-100 max-h-[150px] overflow-y-auto">
              <div className="text-xs font-mono space-y-1">
                {Object.entries(transform.output.key_fields).map(([key, value]) => (
                  <div key={key} className="flex gap-2">
                    <span className="text-green-600 font-semibold flex-shrink-0">{key}:</span>
                    <span className="text-slate-700 break-words">{String(value).substring(0, 100)}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
