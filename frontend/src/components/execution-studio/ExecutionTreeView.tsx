import { useState, useMemo } from 'react'

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

interface EventNode extends ExecutionEvent {
  children: EventNode[]
  depth: number
  isExpanded: boolean
}

interface ExecutionTreeViewProps {
  events: ExecutionEvent[]
}

export default function ExecutionTreeView({ events }: ExecutionTreeViewProps) {
  const [expandedNodes, setExpandedNodes] = useState<Set<string>>(new Set())

  // Build tree structure
  const tree = useMemo(() => {
    const eventMap = new Map<string, ExecutionEvent>(
      events.map(e => [e.event_id, e])
    )

    const childrenMap = new Map<string | null, ExecutionEvent[]>()
    events.forEach(event => {
      const parentId = event.parent_event_id
      if (!childrenMap.has(parentId)) {
        childrenMap.set(parentId, [])
      }
      childrenMap.get(parentId)!.push(event)
    })

    // Sort children by timestamp
    childrenMap.forEach(children => {
      children.sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime())
    })

    // Build tree recursively
    const buildTree = (parentId: string | null, depth: number): EventNode[] => {
      const children = childrenMap.get(parentId) || []
      return children.map(event => ({
        ...event,
        children: buildTree(event.event_id, depth + 1),
        depth,
        isExpanded: expandedNodes.has(event.event_id) || depth <= 1, // Auto-expand first 2 levels
      }))
    }

    return buildTree(null, 0)
  }, [events, expandedNodes])

  const toggleNode = (eventId: string) => {
    const newExpanded = new Set(expandedNodes)
    if (newExpanded.has(eventId)) {
      newExpanded.delete(eventId)
    } else {
      newExpanded.add(eventId)
    }
    setExpandedNodes(newExpanded)
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

  const renderTreeNode = (node: EventNode, parentCount: number = 1) => {
    const hasChildren = node.children.length > 0
    const isExpanded = expandedNodes.has(node.event_id) || node.depth <= 1

    return (
      <div key={node.event_id} className="mb-1">
        {/* Event Node */}
        <div
          className={`
            flex items-start gap-2 p-3 rounded-lg border transition-colors cursor-pointer
            ${getStatusColor(node.status)}
            hover:shadow-md
          `}
          onClick={() => hasChildren && toggleNode(node.event_id)}
        >
          {/* Expand/Collapse Toggle */}
          <div className="flex-shrink-0 w-5 text-center">
            {hasChildren ? (
              <span className="text-xs font-bold">
                {isExpanded ? '▼' : '▶'}
              </span>
            ) : (
              <span className="text-xs opacity-0">•</span>
            )}
          </div>

          {/* Status Icon */}
          <div className={`
            flex-shrink-0 h-6 w-6 rounded-full flex items-center justify-center text-xs font-bold
            ${getStatusColor(node.status)}
          `}>
            {getStatusIcon(node.status)}
          </div>

          {/* Event Details */}
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <span className="font-semibold text-sm">{node.component}</span>
              <span className="text-xs opacity-75">{node.action}</span>
              {node.children.length > 0 && (
                <span className="text-xs opacity-50 ml-auto">
                  {node.children.length} child{node.children.length !== 1 ? 'ren' : ''}
                </span>
              )}
            </div>

            {/* Metrics */}
            <div className="flex gap-3 text-xs opacity-75 mt-1">
              {node.duration_ms > 0 && (
                <span>{node.duration_ms.toFixed(1)}ms</span>
              )}
              {node.tokens_used > 0 && (
                <span>{node.tokens_used} tokens</span>
              )}
              {node.cost > 0 && (
                <span>${node.cost.toFixed(4)}</span>
              )}
              <span className="ml-auto">
                {new Date(node.timestamp).toLocaleTimeString()}
              </span>
            </div>
          </div>
        </div>

        {/* Metadata Row */}
        {(node.error || Object.keys(node.metadata).length > 0) && isExpanded && (
          <div className="ml-6 mt-2 mb-2 space-y-2">
            {node.error && (
              <div className="p-2 bg-red-50 border border-red-200 rounded text-xs text-red-800">
                <p className="font-semibold mb-1">Error</p>
                <p className="font-mono">{node.error}</p>
              </div>
            )}

            {Object.keys(node.metadata).length > 0 && (
              <details className="p-2 bg-slate-50 border border-slate-200 rounded text-xs">
                <summary className="font-semibold cursor-pointer">Metadata ({Object.keys(node.metadata).length} items)</summary>
                <pre className="mt-2 overflow-x-auto text-xs bg-white p-2 rounded border border-slate-200">
                  {JSON.stringify(node.metadata, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}

        {/* Child Events */}
        {hasChildren && isExpanded && (
          <div className="ml-6 mt-2 pl-3 border-l-2 border-slate-300">
            {node.children.map(child => renderTreeNode(child, parentCount + 1))}
          </div>
        )}
      </div>
    )
  }

  // Render parallel execution lanes (events at depth 0)
  const parallelLanes = tree.reduce((lanes: Map<string, EventNode[]>, node) => {
    const component = node.component
    if (!lanes.has(component)) {
      lanes.set(component, [])
    }
    lanes.get(component)!.push(node)
    return lanes
  }, new Map())

  return (
    <div className="rounded-lg border border-slate-200 bg-white overflow-hidden">
      {/* Header */}
      <div className="border-b border-slate-200 px-6 py-4 bg-slate-50">
        <h2 className="text-lg font-semibold text-slate-900">Execution Trace Tree</h2>
        <p className="text-sm text-slate-600 mt-1">
          {events.length} total events • {tree.length} top-level nodes • {parallelLanes.size} parallel component lanes
        </p>
      </div>

      {/* Legend */}
      <div className="border-b border-slate-200 px-6 py-3 bg-slate-50 flex gap-4 flex-wrap text-xs">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-green-100 border border-green-300"></div>
          <span>Completed</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-blue-100 border border-blue-300"></div>
          <span>In Progress</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-yellow-100 border border-yellow-300"></div>
          <span>Started</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 rounded-full bg-red-100 border border-red-300"></div>
          <span>Failed</span>
        </div>
      </div>

      {/* Tree Content */}
      <div className="p-6 space-y-2 overflow-auto max-h-[70vh]">
        {tree.length === 0 ? (
          <p className="text-center text-slate-500 py-8">No events found</p>
        ) : (
          <>
            {/* Parallel Execution Lanes View */}
            {parallelLanes.size > 1 && (
              <details className="mb-6 p-3 bg-blue-50 border border-blue-200 rounded">
                <summary className="font-semibold text-sm cursor-pointer text-blue-900">
                  Parallel Execution Lanes ({parallelLanes.size} components)
                </summary>
                <div className="mt-3 space-y-2">
                  {Array.from(parallelLanes.entries()).map(([component, nodes]) => (
                    <div key={component} className="p-2 bg-white rounded border border-blue-100">
                      <p className="font-semibold text-xs text-slate-900">{component}</p>
                      <div className="flex gap-1 mt-1 flex-wrap">
                        {nodes.map(node => (
                          <div
                            key={node.event_id}
                            className={`px-2 py-1 rounded text-xs font-medium border ${getStatusColor(node.status)}`}
                            title={`${node.action} - ${node.duration_ms.toFixed(1)}ms`}
                          >
                            {node.action}
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            )}

            {/* Full Tree View */}
            <div>
              {tree.map(node => renderTreeNode(node))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
