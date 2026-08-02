import { useState, useEffect } from 'react'

interface ComponentLearning {
  component: string
  purpose: string
  description: string
  design_pattern: string
  workflow_steps: string[]
  when_to_use: string[]
  when_not_to_use: string[]
  performance_tips: string[]
  common_mistakes: string[]
  related_components: string[]
}

interface LearnModeProps {
  componentName: string
}

export default function LearnMode({ componentName }: LearnModeProps) {
  const [learning, setLearning] = useState<ComponentLearning | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchLearning()
  }, [componentName])

  async function fetchLearning() {
    try {
      setLoading(true)
      const response = await fetch(
        `/api/execution-studio/learn/components/${componentName}`,
        { headers: { 'Content-Type': 'application/json' } }
      )
      if (!response.ok) throw new Error('Failed to fetch learning content')
      const data = await response.json()
      setLearning(data)
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="p-4 text-center text-slate-500">Loading...</div>
  }

  if (error || !learning) {
    return <div className="p-4 text-center text-red-500">Error loading content</div>
  }

  return (
    <div className="space-y-6 max-h-[70vh] overflow-y-auto">
      {/* Purpose */}
      <div>
        <h3 className="font-bold text-slate-900 mb-2">💡 Purpose</h3>
        <p className="text-sm text-slate-700">{learning.purpose}</p>
      </div>

      {/* Description */}
      <div>
        <h3 className="font-bold text-slate-900 mb-2">📝 What It Does</h3>
        <p className="text-sm text-slate-700">{learning.description}</p>
      </div>

      {/* Design Pattern */}
      <div className="p-3 bg-purple-50 rounded-lg border border-purple-200">
        <h3 className="font-bold text-purple-900 mb-2">🏗️ Design Pattern</h3>
        <p className="text-sm text-purple-800">{learning.design_pattern}</p>
      </div>

      {/* Workflow */}
      <div>
        <h3 className="font-bold text-slate-900 mb-2">⚙️ How It Works</h3>
        <ol className="space-y-2">
          {learning.workflow_steps.map((step, i) => (
            <li key={i} className="text-sm text-slate-700 flex gap-2">
              <span className="font-semibold text-slate-500">{i + 1}.</span>
              <span>{step}</span>
            </li>
          ))}
        </ol>
      </div>

      {/* When to Use */}
      <div className="p-3 bg-green-50 rounded-lg border border-green-200">
        <h3 className="font-bold text-green-900 mb-2">✅ When to Use</h3>
        <ul className="space-y-1">
          {learning.when_to_use.map((item, i) => (
            <li key={i} className="text-sm text-green-800 flex gap-2">
              <span>•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* When NOT to Use */}
      <div className="p-3 bg-red-50 rounded-lg border border-red-200">
        <h3 className="font-bold text-red-900 mb-2">❌ When NOT to Use</h3>
        <ul className="space-y-1">
          {learning.when_not_to_use.map((item, i) => (
            <li key={i} className="text-sm text-red-800 flex gap-2">
              <span>•</span>
              <span>{item}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Performance Tips */}
      <div className="p-3 bg-blue-50 rounded-lg border border-blue-200">
        <h3 className="font-bold text-blue-900 mb-2">⚡ Performance Tips</h3>
        <ul className="space-y-1">
          {learning.performance_tips.map((tip, i) => (
            <li key={i} className="text-sm text-blue-800 flex gap-2">
              <span>💫</span>
              <span>{tip}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Common Mistakes */}
      <div className="p-3 bg-yellow-50 rounded-lg border border-yellow-200">
        <h3 className="font-bold text-yellow-900 mb-2">⚠️ Common Mistakes</h3>
        <ul className="space-y-1">
          {learning.common_mistakes.map((mistake, i) => (
            <li key={i} className="text-sm text-yellow-800 flex gap-2">
              <span>🚫</span>
              <span>{mistake}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Related Components */}
      {learning.related_components.length > 0 && (
        <div>
          <h3 className="font-bold text-slate-900 mb-2">🔗 Related Components</h3>
          <div className="flex flex-wrap gap-2">
            {learning.related_components.map((comp, i) => (
              <span
                key={i}
                className="px-2 py-1 bg-slate-100 text-slate-700 rounded text-xs font-medium"
              >
                {comp}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
