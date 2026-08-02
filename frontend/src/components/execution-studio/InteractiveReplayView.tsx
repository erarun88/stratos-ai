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

interface InteractiveReplayViewProps {
  requestId: string
  onComponentHighlight?: (componentName: string | null) => void
}

export default function InteractiveReplayView({ requestId, onComponentHighlight }: InteractiveReplayViewProps) {
  const [data, setData] = useState<ComponentTransformation[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentStep, setCurrentStep] = useState(0)
  const [isPlaying, setIsPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [expandDetails, setExpandDetails] = useState(false)

  useEffect(() => {
    fetchData()
  }, [requestId])

  useEffect(() => {
    if (data.length > 0 && onComponentHighlight) {
      onComponentHighlight(data[currentStep]?.component || null)
    }
  }, [currentStep, data, onComponentHighlight])

  useEffect(() => {
    if (!isPlaying || data.length === 0) return

    const interval = setInterval(() => {
      setCurrentStep(prev => {
        if (prev >= data.length - 1) {
          setIsPlaying(false)
          return prev
        }
        return prev + 1
      })
    }, 1000 / speed)

    return () => clearInterval(interval)
  }, [isPlaying, speed, data.length])

  async function fetchData() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/before-after/${requestId}`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!response.ok) throw new Error('Failed to fetch data')
      const result = await response.json()
      setData(result.transformations || [])
      setCurrentStep(0)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-4 text-center text-slate-500">Loading replay...</div>
  }

  if (error) {
    return <div className="p-4 text-center text-red-500">Error: {error}</div>
  }

  if (data.length === 0) {
    return <div className="p-4 text-center text-slate-500">No execution data available</div>
  }

  const current = data[currentStep]
  const progress = ((currentStep + 1) / data.length) * 100

  return (
    <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-2">
      {/* Controls Section */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4 space-y-4">
        {/* Play Controls */}
        <div className="flex items-center gap-3">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="px-4 py-2 rounded-lg bg-blue-600 text-white hover:bg-blue-700 font-medium flex items-center gap-2"
          >
            {isPlaying ? '⏸️ Pause' : '▶️ Play'}
          </button>

          <button
            onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
            disabled={currentStep === 0}
            className="px-3 py-2 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ⏮️ Prev
          </button>

          <button
            onClick={() => setCurrentStep(Math.min(data.length - 1, currentStep + 1))}
            disabled={currentStep === data.length - 1}
            className="px-3 py-2 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next ⏭️
          </button>

          <button
            onClick={() => setCurrentStep(0)}
            className="px-3 py-2 rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300"
          >
            ↻ Reset
          </button>

          <div className="flex-1"></div>

          {/* Speed Control */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-slate-600 font-medium">Speed:</label>
            <select
              value={speed}
              onChange={(e) => setSpeed(parseFloat(e.target.value))}
              className="px-2 py-1 rounded border border-slate-300 text-sm bg-white"
            >
              <option value={0.5}>0.5x</option>
              <option value={1}>1x</option>
              <option value={2}>2x</option>
              <option value={4}>4x</option>
            </select>
          </div>
        </div>

        {/* Progress Info */}
        <div className="text-sm text-slate-600">
          Step <span className="font-bold text-slate-900">{currentStep + 1}</span> of{' '}
          <span className="font-bold text-slate-900">{data.length}</span>
        </div>

        {/* Timeline Scrubber */}
        <div className="space-y-2">
          <div className="flex items-center gap-3">
            <input
              type="range"
              min="0"
              max={data.length - 1}
              value={currentStep}
              onChange={(e) => {
                setIsPlaying(false)
                setCurrentStep(parseInt(e.target.value))
              }}
              className="flex-1 h-2 bg-slate-300 rounded-lg appearance-none cursor-pointer accent-blue-600"
            />
          </div>

          {/* Progress Bar */}
          <div className="w-full h-1 bg-slate-300 rounded-full overflow-hidden">
            <div
              className="h-full bg-blue-600 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      </div>

      {/* Current Step Display */}
      <div className="border border-slate-200 rounded-lg bg-white overflow-hidden">
        {/* Header */}
        <div className="bg-blue-50 border-b border-slate-200 p-4">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-3">
              <span className="text-2xl font-bold text-blue-600">#</span>
              <div>
                <h3 className="text-lg font-bold text-slate-900">{current.component}</h3>
                <p className="text-sm text-slate-600">{current.action}</p>
              </div>
            </div>
            <span className="text-3xl">
              {current.status === 'completed'
                ? '✅'
                : current.status === 'failed'
                  ? '❌'
                  : current.status === 'in_progress'
                    ? '⏳'
                    : '⚪'}
            </span>
          </div>

          <div className="flex gap-6 text-sm">
            <span>⏱️ {current.duration_ms.toFixed(1)}ms</span>
            <span>🔤 {current.tokens_used} tokens</span>
            <span>💰 ${current.cost.toFixed(4)}</span>
          </div>
        </div>

        {/* Content */}
        <div className="p-4 space-y-4">
          {/* Input */}
          <div className="border border-blue-200 rounded-lg bg-blue-50 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl">📥</span>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Input</h4>
                  <p className="text-xs text-slate-600">{current.input.type}</p>
                </div>
              </div>
              {Object.keys(current.input.key_fields).length > 0 && (
                <button
                  onClick={() => setExpandDetails(!expandDetails)}
                  className="text-xs text-blue-600 hover:text-blue-700 font-medium"
                >
                  {expandDetails ? '▼ Hide' : '▶ Show'}
                </button>
              )}
            </div>

            <p className="text-sm text-slate-700">{current.input.description}</p>

            {expandDetails && Object.keys(current.input.key_fields).length > 0 && (
              <div className="mt-3 p-3 bg-white rounded border border-blue-100 max-h-[120px] overflow-y-auto">
                <div className="text-xs font-mono space-y-1">
                  {Object.entries(current.input.key_fields).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="text-blue-600 font-semibold flex-shrink-0">{key}:</span>
                      <span className="text-slate-700 break-words">{String(value).substring(0, 80)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Processing Arrow */}
          <div className="flex justify-center py-2">
            <span className="text-2xl">⚙️</span>
          </div>

          {/* Output */}
          <div className="border border-green-200 rounded-lg bg-green-50 p-4">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-2">
                <span className="text-xl">📤</span>
                <div>
                  <h4 className="font-bold text-slate-900 text-sm">Output</h4>
                  <p className="text-xs text-slate-600">{current.output.type}</p>
                </div>
              </div>
              {Object.keys(current.output.key_fields).length > 0 && (
                <button
                  onClick={() => setExpandDetails(!expandDetails)}
                  className="text-xs text-green-600 hover:text-green-700 font-medium"
                >
                  {expandDetails ? '▼ Hide' : '▶ Show'}
                </button>
              )}
            </div>

            <p className="text-sm text-slate-700 mb-3">{current.output.description}</p>

            {/* Confidence */}
            <div className="mb-3 p-2 bg-white rounded border border-green-100">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs font-semibold text-slate-600">Confidence</span>
                <span className="text-xs font-bold text-green-700">{(current.output.confidence * 100).toFixed(0)}%</span>
              </div>
              <div className="w-full h-2 bg-slate-200 rounded-full overflow-hidden">
                <div
                  className="h-full bg-green-500"
                  style={{ width: `${current.output.confidence * 100}%` }}
                />
              </div>
            </div>

            {expandDetails && Object.keys(current.output.key_fields).length > 0 && (
              <div className="mt-3 p-3 bg-white rounded border border-green-100 max-h-[120px] overflow-y-auto">
                <div className="text-xs font-mono space-y-1">
                  {Object.entries(current.output.key_fields).map(([key, value]) => (
                    <div key={key} className="flex gap-2">
                      <span className="text-green-600 font-semibold flex-shrink-0">{key}:</span>
                      <span className="text-slate-700 break-words">{String(value).substring(0, 80)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Timeline Preview */}
      <div className="bg-slate-50 border border-slate-200 rounded-lg p-4">
        <h4 className="text-sm font-bold text-slate-900 mb-3">📋 Execution Timeline</h4>
        <div className="space-y-1 max-h-[200px] overflow-y-auto">
          {data.map((step, idx) => (
            <button
              key={idx}
              onClick={() => {
                setIsPlaying(false)
                setCurrentStep(idx)
              }}
              className={`w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                idx === currentStep
                  ? 'bg-blue-600 text-white font-semibold'
                  : 'hover:bg-slate-200 text-slate-700'
              }`}
            >
              <span className="mr-2">{idx === currentStep ? '▶' : '•'}</span>
              {step.component} • {step.action}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
