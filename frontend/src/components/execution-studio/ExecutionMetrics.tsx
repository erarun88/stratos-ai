import { useState, useEffect } from 'react'

interface Metrics {
  request_id: string
  total_duration_ms: number
  total_tokens: number
  total_cost: number
  component_count: number
  event_count: number
  agent_count: number
  tool_count: number
  errors: number
}

interface ExecutionMetricsProps {
  requestId: string
}

export default function ExecutionMetrics({ requestId }: ExecutionMetricsProps) {
  const [metrics, setMetrics] = useState<Metrics | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchMetrics()
  }, [requestId])

  async function fetchMetrics() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/requests/${requestId}/metrics`,
        {
          headers: { 'Content-Type': 'application/json' },
        }
      )
      if (!response.ok) throw new Error('Failed to fetch metrics')
      const data = await response.json()
      setMetrics(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-200" />
        ))}
      </div>
    )
  }

  if (error || !metrics) {
    return (
      <div className="rounded-lg border border-red-200 bg-red-50 p-4">
        <p className="text-sm text-red-800">Error loading metrics: {error}</p>
      </div>
    )
  }

  const metricCards = [
    {
      label: 'Duration',
      value: `${metrics.total_duration_ms.toFixed(0)}ms`,
      icon: '⏱️',
    },
    {
      label: 'Tokens',
      value: metrics.total_tokens.toLocaleString(),
      icon: '📝',
    },
    {
      label: 'Cost',
      value: `$${metrics.total_cost.toFixed(4)}`,
      icon: '💰',
    },
    {
      label: 'Events',
      value: metrics.event_count.toString(),
      icon: '📊',
    },
    {
      label: 'Agents',
      value: metrics.agent_count.toString(),
      icon: '🤖',
    },
    {
      label: 'Tools',
      value: metrics.tool_count.toString(),
      icon: '🔧',
    },
    {
      label: 'Components',
      value: metrics.component_count.toString(),
      icon: '⚙️',
    },
    {
      label: 'Errors',
      value: metrics.errors.toString(),
      icon: '⚠️',
      highlight: metrics.errors > 0,
    },
  ]

  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
      {metricCards.map((card) => (
        <div
          key={card.label}
          className={`rounded-lg border p-4 ${
            card.highlight
              ? 'border-red-200 bg-red-50'
              : 'border-slate-200 bg-white'
          }`}
        >
          <div className="flex items-center justify-between">
            <div>
              <p className="text-xs font-medium text-slate-600">{card.label}</p>
              <p
                className={`mt-1 text-2xl font-bold ${
                  card.highlight ? 'text-red-800' : 'text-slate-900'
                }`}
              >
                {card.value}
              </p>
            </div>
            <div className="text-2xl">{card.icon}</div>
          </div>
        </div>
      ))}
    </div>
  )
}
