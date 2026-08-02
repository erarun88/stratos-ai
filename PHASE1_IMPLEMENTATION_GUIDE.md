# Phase 1 Implementation Guide: Advanced Learning System

## Overview

Phase 1 focuses on the 4 core features that deliver the most value:
1. **Architecture View** - Live system diagram
2. **Learn Mode** - Component sidebar with explanations
3. **Before/After** - Data transformation visualization
4. **Interactive Replay** - Timeline with stepping

## Feature 1: Architecture View (START HERE)

### What to Build

A live visual diagram showing:
- All components in the execution (with status indicators)
- Data flow between components
- Real-time metrics (tokens, cost, duration)
- Clickable to drill down

### Backend Changes

#### 1. Add Component Metadata

```python
# backend/app/execution_studio/component_registry.py (NEW)

@dataclass
class ComponentMetadata:
    """Metadata about a component for visualization."""
    component: str
    display_name: str
    component_type: str  # "orchestrator", "agent", "tool", etc.
    icon: str           # emoji or icon name
    description: str    # One-line explanation
    color: str         # For visualization (#hex or name)
    layer: int         # UI layer (0=entry, 1=routing, 2=execution)
    position: tuple    # (x, y) for diagram layout

COMPONENT_REGISTRY = {
    "ChatEndpoint": ComponentMetadata(
        component="ChatEndpoint",
        display_name="Chat Entry",
        component_type="orchestrator",
        icon="💬",
        description="HTTP API endpoint for chat requests",
        color="purple",
        layer=0,
        position=(50, 10),
    ),
    "SupervisorAgent": ComponentMetadata(
        component="SupervisorAgent",
        display_name="Supervisor",
        component_type="orchestrator",
        icon="🎯",
        description="Routes queries to specialist agents",
        color="blue",
        layer=1,
        position=(50, 30),
    ),
    "ProjectAgent": ComponentMetadata(
        component="ProjectAgent",
        display_name="Project Expert",
        component_type="specialist_agent",
        icon="📊",
        description="Handles project management queries",
        color="green",
        layer=2,
        position=(25, 50),
    ),
    # ... more components
}
```

#### 2. Add Architecture API Endpoint

```python
# In backend/app/routers/execution_studio_api.py

@router.get("/architecture/{request_id}/diagram")
async def get_architecture_diagram(request_id: str) -> dict:
    """Get architecture diagram for a request.
    
    Returns:
    {
        "components": [
            {
                "id": "ChatEndpoint",
                "display_name": "Chat Entry",
                "type": "orchestrator",
                "icon": "💬",
                "status": "completed",
                "duration_ms": 342,
                "position": [50, 10],
                "metrics": {
                    "tokens": 2340,
                    "cost": 0.047,
                    "errors": 0
                }
            }
        ],
        "connections": [
            {
                "from": "ChatEndpoint",
                "to": "SupervisorAgent",
                "type": "parent-child",
                "flow_type": "direct"
            }
        ],
        "statistics": {
            "total_duration_ms": 342,
            "total_tokens": 2340,
            "total_cost": 0.047,
            "components_active": 8,
            "critical_path_ms": 342
        }
    }
    """
    try:
        semantic_store = get_semantic_event_store()
        events = semantic_store.get_request_trace(request_id)
        
        if not events:
            raise HTTPException(status_code=404, detail="Request not found")
        
        # Build component status map
        components = {}
        connections = []
        
        for event in events:
            # Get component metadata
            metadata = COMPONENT_REGISTRY.get(
                event.component,
                ComponentMetadata(
                    component=event.component,
                    display_name=event.component,
                    component_type=event.component_type.value,
                    icon="⚙️",
                    description="Component",
                    color="gray",
                    layer=2,
                    position=(50, 50),
                )
            )
            
            # Create or update component
            component_id = event.component
            if component_id not in components:
                components[component_id] = {
                    "id": event.component,
                    "display_name": metadata.display_name,
                    "type": event.component_type.value,
                    "icon": metadata.icon,
                    "color": metadata.color,
                    "position": list(metadata.position),
                    "status": event.status.value,
                    "duration_ms": event.duration_ms,
                    "metrics": {
                        "tokens": 0,
                        "cost": 0.0,
                        "errors": 0,
                    }
                }
            
            # Aggregate metrics
            components[component_id]["metrics"]["tokens"] += event.tokens_used
            components[component_id]["metrics"]["cost"] += event.cost
            if event.status.value == "failed":
                components[component_id]["metrics"]["errors"] += 1
            
            # Add parent-child connection
            if event.parent_event_id:
                parent_event = next(
                    (e for e in events if str(e.event_id) == event.parent_event_id),
                    None
                )
                if parent_event:
                    connections.append({
                        "from": parent_event.component,
                        "to": event.component,
                        "type": "parent-child",
                        "flow_type": "direct",
                    })
        
        # Calculate statistics
        total_duration = max(e.duration_ms for e in events) if events else 0
        total_tokens = sum(e.tokens_used for e in events)
        total_cost = sum(e.cost for e in events)
        active_components = sum(1 for c in components.values() if c["status"] == "completed")
        errors = sum(c["metrics"]["errors"] for c in components.values())
        
        return {
            "components": list(components.values()),
            "connections": connections,
            "statistics": {
                "total_duration_ms": total_duration,
                "total_tokens": total_tokens,
                "total_cost": total_cost,
                "components_active": active_components,
                "total_components": len(components),
                "errors": errors,
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get architecture diagram: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
```

### Frontend Component

```tsx
// frontend/src/components/execution-studio/ArchitectureView.tsx

import { useState, useEffect, useMemo } from 'react'

interface Component {
  id: string
  display_name: string
  type: string
  icon: string
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

interface ArchitectureViewProps {
  requestId: string
}

export default function ArchitectureView({ requestId }: ArchitectureViewProps) {
  const [diagram, setDiagram] = useState(null)
  const [selectedComponent, setSelectedComponent] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
      setError(null)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981'  // green
      case 'failed': return '#ef4444'     // red
      case 'in_progress': return '#3b82f6' // blue
      default: return '#9ca3af'           // gray
    }
  }

  if (loading) return <div className="p-6 text-center text-slate-500">Loading architecture...</div>
  if (error) return <div className="p-6 text-center text-red-500">{error}</div>

  return (
    <div className="space-y-6">
      {/* Statistics */}
      <div className="grid grid-cols-5 gap-4">
        <StatCard
          label="Duration"
          value={`${diagram.statistics.total_duration_ms.toFixed(0)}ms`}
          icon="⏱️"
        />
        <StatCard
          label="Tokens"
          value={diagram.statistics.total_tokens}
          icon="🔤"
        />
        <StatCard
          label="Cost"
          value={`$${diagram.statistics.total_cost.toFixed(4)}`}
          icon="💰"
        />
        <StatCard
          label="Components"
          value={diagram.statistics.total_components}
          icon="⚙️"
        />
        <StatCard
          label="Errors"
          value={diagram.statistics.errors}
          icon={diagram.statistics.errors > 0 ? "🔴" : "✅"}
        />
      </div>

      {/* Architecture Diagram */}
      <div className="bg-white rounded-lg border border-slate-200 p-6 min-h-[500px]">
        <svg width="100%" height="500" className="border border-slate-100 rounded">
          {/* Draw connections first (so they appear under components) */}
          {diagram.connections.map((conn: Connection, i: number) => {
            const fromComp = diagram.components.find((c: Component) => c.id === conn.from)
            const toComp = diagram.components.find((c: Component) => c.id === conn.to)
            if (!fromComp || !toComp) return null

            const fromX = (fromComp.position[0] / 100) * 800
            const fromY = (fromComp.position[1] / 100) * 400 + 60
            const toX = (toComp.position[0] / 100) * 800
            const toY = (toComp.position[1] / 100) * 400 + 60

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
          {diagram.components.map((comp: Component) => {
            const x = (comp.position[0] / 100) * 800 - 40
            const y = (comp.position[1] / 100) * 400
            const isSelected = selectedComponent === comp.id

            return (
              <g
                key={comp.id}
                onClick={() => setSelectedComponent(comp.id)}
                style={{ cursor: 'pointer' }}
              >
                <rect
                  x={x}
                  y={y}
                  width="80"
                  height="60"
                  fill={isSelected ? '#efe6ff' : '#f8fafc'}
                  stroke={isSelected ? '#a78bfa' : getStatusColor(comp.status)}
                  strokeWidth={isSelected ? "3" : "2"}
                  rx="4"
                />
                <text x={x + 40} y={y + 15} textAnchor="middle" fontSize="20">
                  {comp.icon}
                </text>
                <text
                  x={x + 40}
                  y={y + 40}
                  textAnchor="middle"
                  fontSize="12"
                  fontWeight="bold"
                >
                  {comp.display_name}
                </text>
                <text x={x + 40} y={y + 52} textAnchor="middle" fontSize="10" fill="#666">
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
        </div>
      </div>

      {/* Component Details */}
      {selectedComponent && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
          {diagram.components.find((c: Component) => c.id === selectedComponent) && (
            <ComponentDetails
              component={diagram.components.find((c: Component) => c.id === selectedComponent)}
            />
          )}
        </div>
      )}
    </div>
  )
}

function StatCard({ label, value, icon }: { label: string; value: any; icon: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-4 text-center border border-slate-200">
      <div className="text-2xl mb-2">{icon}</div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-xs text-slate-600 mt-1">{label}</div>
    </div>
  )
}

function ComponentDetails({ component }: { component: Component }) {
  return (
    <div>
      <div className="flex items-center gap-3 mb-4">
        <span className="text-3xl">{component.icon}</span>
        <div>
          <h3 className="text-xl font-bold text-slate-900">{component.display_name}</h3>
          <p className="text-sm text-slate-600">{component.type}</p>
        </div>
      </div>

      <div className="grid grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-slate-600">Duration</p>
          <p className="text-lg font-bold text-slate-900">{component.duration_ms.toFixed(1)}ms</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Tokens</p>
          <p className="text-lg font-bold text-slate-900">{component.metrics.tokens}</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Cost</p>
          <p className="text-lg font-bold text-slate-900">${component.metrics.cost.toFixed(4)}</p>
        </div>
        <div>
          <p className="text-xs text-slate-600">Status</p>
          <p className="text-lg font-bold capitalize" style={{ color: getStatusColor(component.status) }}>
            {component.status}
          </p>
        </div>
      </div>
    </div>
  )
}
```

### Add to ExecutionStudio Page

```tsx
// In frontend/src/pages/ExecutionStudio.tsx

import ArchitectureView from '../components/execution-studio/ArchitectureView'

// In the main content section:
{selectedRequest ? (
  <>
    <ExecutionMetrics requestId={selectedRequest} />
    <ArchitectureView requestId={selectedRequest} />  {/* NEW */}
    <ExecutionGraph requestId={selectedRequest} />
    <ExecutionTimeline requestId={selectedRequest} />
  </>
) : null}
```

---

## Testing Phase 1

### 1. Start Servers
```bash
cd /workspaces/stratos-ai/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal:
cd /workspaces/stratos-ai/frontend
npm run dev
```

### 2. Test Flow
1. Go to http://localhost:5173/execution-studio
2. Ask a chat question
3. Go back to Execution Studio
4. See Architecture View showing:
   - All components with icons
   - Connections between them
   - Statistics (tokens, cost, duration)
5. Click a component to see details

---

## Phase 1 Summary

**What you get:**
- ✅ Visual understanding of system architecture
- ✅ Real-time metrics per component
- ✅ Click to explore details
- ✅ Foundation for Learn Mode (add descriptions)

**Effort:** ~4-6 hours  
**Impact:** ~80% users will find this valuable

**Next steps after Phase 1:**
- Add Learn Mode sidebar (explanations)
- Add Before/After data visualization
- Add Interactive Replay timeline

This is the foundation that makes everything else click!
