import { useState, useEffect } from 'react'

interface MemoryDecision {
  statement: string
  action: 'ignore' | 'store' | 'update' | 'merge' | 'delete'
  confidence: number
  rationale: string
  memory_id?: string
}

interface MemoryTrace {
  retrieval_count: number
  retrieval_ms: number
  retrieval_query?: string
  ranked_memories: Array<{
    title: string
    score: number
  }>
  ranking_ms: number
  injected_tokens: number
  injection_ms: number
  decision_ms: number
  decisions: MemoryDecision[]
  total_ms: number
}

interface MemoryLaneProps {
  requestId: string
}

export default function MemoryLane({ requestId }: MemoryLaneProps) {
  const [trace, setTrace] = useState<MemoryTrace | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMemoryTrace()
  }, [requestId])

  async function fetchMemoryTrace() {
    try {
      setLoading(true)
      // For now, mock the data since backend doesn't emit memory trace yet
      // In Phase 2 integration, this will query actual execution trace
      setTrace(null) // Will be populated when integrated
    } catch {
      // Error handling for future phase
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-4 text-center text-slate-500">Loading memory trace...</div>
  }

  if (!trace) {
    return (
      <div className="p-6 text-center text-slate-500">
        <p className="mb-2">Memory lane visualization will appear here during execution</p>
        <p className="text-xs">
          Shows retrieval, ranking, injection, and decision engine decisions
        </p>
      </div>
    )
  }

  return (
    <div className="space-y-6 max-h-[70vh] overflow-y-auto pr-2">
      {/* Retrieval Stage */}
      <div className="border-l-4 border-purple-400 pl-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-bold text-slate-900 flex items-center gap-2">
            <span>📥</span>
            <span>Memory Retrieval</span>
            <span className="text-xs text-slate-500">({trace.retrieval_ms}ms)</span>
          </h4>
        </div>

        <div className="space-y-2 text-sm">
          {trace.retrieval_query && (
            <div className="p-2 bg-slate-50 rounded">
              <p className="text-xs text-slate-600">Query:</p>
              <p className="font-mono text-sm">"{trace.retrieval_query}"</p>
            </div>
          )}
          <p className="text-slate-600">
            Found <span className="font-bold text-slate-900">{trace.retrieval_count}</span> relevant
            memories
          </p>
        </div>
      </div>

      {/* Ranking Stage */}
      <div className="border-l-4 border-amber-400 pl-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-bold text-slate-900 flex items-center gap-2">
            <span>⭐</span>
            <span>Memory Ranking</span>
            <span className="text-xs text-slate-500">({trace.ranking_ms}ms)</span>
          </h4>
        </div>

        <div className="space-y-2">
          {trace.ranked_memories.map((mem, i) => (
            <div key={i} className="flex items-center justify-between p-2 bg-slate-50 rounded">
              <div className="text-sm">
                <span className="text-slate-600 mr-2">#{i + 1}</span>
                <span className="font-medium text-slate-900">{mem.title}</span>
              </div>
              <div className="text-xs font-mono text-slate-500">{(mem.score * 100).toFixed(0)}%</div>
            </div>
          ))}
        </div>
      </div>

      {/* Context Injection Stage */}
      <div className="border-l-4 border-blue-400 pl-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-bold text-slate-900 flex items-center gap-2">
            <span>💉</span>
            <span>Context Injection</span>
            <span className="text-xs text-slate-500">({trace.injection_ms}ms)</span>
          </h4>
        </div>

        <p className="text-sm text-slate-700">
          Injected <span className="font-bold">{trace.injected_tokens}</span> tokens into LLM context
        </p>
      </div>

      {/* Memory Decisions */}
      <div className="border-l-4 border-green-400 pl-4">
        <div className="flex items-center justify-between mb-2">
          <h4 className="font-bold text-slate-900 flex items-center gap-2">
            <span>🧠</span>
            <span>Memory Decisions</span>
            <span className="text-xs text-slate-500">({trace.decision_ms}ms)</span>
          </h4>
        </div>

        <div className="space-y-3">
          {trace.decisions.map((decision, i) => (
            <div key={i} className="p-3 bg-slate-50 rounded border border-slate-200">
              <div className="mb-2">
                <p className="text-sm font-mono text-slate-700">"{decision.statement}"</p>
              </div>

              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="px-2 py-1 rounded bg-white border border-slate-200 text-xs font-bold">
                    {decision.action.toUpperCase()}
                  </span>
                  <span className="text-xs text-slate-600">
                    Confidence: <span className="font-bold">{(decision.confidence * 100).toFixed(0)}%</span>
                  </span>
                </div>
              </div>

              <p className="mt-2 text-xs text-slate-600 italic">{decision.rationale}</p>

              {decision.memory_id && (
                <p className="mt-2 text-xs text-slate-500">Memory: {decision.memory_id.slice(0, 12)}...</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-bold text-slate-900">Total Memory Time</p>
            <p className="text-xs text-slate-600">{trace.total_ms}ms</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-slate-600">
              {((trace.total_ms / 10000) * 100).toFixed(1)}% of request*
            </p>
            <p className="text-xs text-slate-500 mt-1">*estimated</p>
          </div>
        </div>
      </div>
    </div>
  )
}
