# AI Execution Studio - Architectural Design Document

## Executive Summary

**AI Execution Studio** is an event-driven visualization platform that makes the Enterprise AI system transparent and educational. It captures every execution event, visualizes the request flow, and teaches how AI systems work internally.

**Key Principle**: Components publish events; UI renders events. No hardcoding, no component-specific logic in frontend.

---

## Current Architecture Analysis

### Existing System (Phases A-E)

```
User Query
    ↓
Supervisor Agent
    ├─→ ProjectAgent
    ├─→ RiskAgent
    ├─→ ScheduleAgent
    └─→ DocumentAgent (parallel)
    ↓
[Optional] Task Planner → Task Executor
    ↓
[Phase D] Reflection Agent
    ↓
[Phase E] Approval Framework
    ↓
Response
```

### Current Limitations

❌ No visibility into execution flow
❌ No component-level metrics (tokens, latency, cost)
❌ No decision tracing (why was this agent selected?)
❌ No replay capability
❌ No educational explanations
❌ Hardcoded for specific agents/components
❌ Cannot show future components (Memory, MCP, Evaluation, etc.)

### Integration Points to Leverage

✅ `SupervisorAgent` - routes queries
✅ `TaskPlanner/Executor` - decomposes requests
✅ `ReflectionAgent` - improves responses
✅ `ApprovalManager` - gates actions
✅ `ToolManager` - executes tools
✅ `LLMClient` - calls models
✅ `Guardrails` - validates outputs
✅ All agents inherit from `Agent` base class

---

## Proposed Architecture

### Layer 1: Event Framework (Backend)

```
Component Layer
    ↓
[Event Publisher]  ← Every component publishes here
    ↓
Event Bus (in-memory pub/sub)
    ↓
Event Store (PostgreSQL)
    ↓
Execution Trace Service (Query API)
    ↓
WebSocket Stream (Real-time to frontend)
```

### Layer 2: Event Model

Every event has:
```python
class ExecutionEvent:
    request_id: str              # Trace ID
    parent_event_id: str         # For nesting
    timestamp: datetime
    component: str               # "SupervisorAgent", "ProjectAgent", etc.
    action: str                  # "route_query", "agent_selected", "tool_called", etc.
    status: str                  # "started", "in_progress", "completed", "failed"
    duration_ms: float
    metadata: Dict               # Component-specific data
    tokens_used: int             # LLM tokens
    cost: float                  # $ cost
    latency_ms: float
    error: Optional[str]
```

### Layer 3: Component Integration

**Tracing Middleware Pattern**:

```python
# Every component wraps its logic
async def traced_execution(component, action, metadata):
    event_id = generate_id()
    
    # Emit "started" event
    bus.publish(Event(
        component=component,
        action=action,
        status="started",
        event_id=event_id,
        metadata=metadata
    ))
    
    try:
        result = await actual_logic()
        
        # Emit "completed" event
        bus.publish(Event(
            event_id=event_id,
            status="completed",
            duration_ms=elapsed,
            metadata={"result": result}
        ))
        return result
    except Exception as e:
        # Emit "failed" event
        bus.publish(Event(
            event_id=event_id,
            status="failed",
            error=str(e)
        ))
        raise
```

### Layer 4: Backward Compatibility

✅ **Zero Breaking Changes**:
- Tracing is additive (wraps existing logic)
- Event publishing is asynchronous and non-blocking
- If event bus fails, system continues
- Existing code paths unaffected

---

## Design Principles

### 1. Event-Driven (not callback-driven)
- Components publish events
- UI subscribes to events
- Loose coupling

### 2. Generic (not hardcoded)
```python
# ❌ BAD - Hardcoded for ProjectAgent
if component == "ProjectAgent":
    render_project_agent_ui()

# ✅ GOOD - Generic based on events
render_generic_component(event.component, event.metadata)
```

### 3. Self-Describing Events
```python
{
    "component": "ReflectionAgent",
    "action": "detect_hallucinations",
    "status": "completed",
    "metadata": {
        "hallucination_risk": 0.7,
        "citation_gaps": ["No citation for budget"],
        "improvements_applied": 1
    }
    # Frontend doesn't need to know what ReflectionAgent is
    # It just renders the event data
}
```

### 4. Learning-First Design
Every event includes:
- Why did this happen?
- What problem does it solve?
- Could the system work without it?
- Design pattern used
- Trade-offs

---

## New Components Required

### Backend

```
backend/app/
├── execution_studio/
│   ├── __init__.py
│   ├── event_bus.py              # Central pub/sub
│   ├── event_model.py            # Event dataclass
│   ├── event_store.py            # PostgreSQL persistence
│   ├── execution_trace_service.py # Query API
│   ├── tracer.py                 # Decorator/wrapper for components
│   ├── websocket_server.py       # Real-time streaming
│   └── learning_explanations.py   # Educational content
│
└── routers/
    └── execution_studio.py        # HTTP API endpoints
```

### Database

```sql
CREATE TABLE execution_events (
    id UUID PRIMARY KEY,
    request_id UUID NOT NULL,
    parent_event_id UUID,
    timestamp DATETIME,
    component VARCHAR(255),
    action VARCHAR(255),
    status VARCHAR(50),
    duration_ms FLOAT,
    tokens_used INT,
    cost FLOAT,
    latency_ms FLOAT,
    metadata JSONB,
    error TEXT,
    created_at DATETIME DEFAULT NOW()
);

CREATE INDEX idx_request_id ON execution_events(request_id);
CREATE INDEX idx_component ON execution_events(component);
CREATE INDEX idx_timestamp ON execution_events(timestamp);
```

### Frontend

```
frontend/src/
├── pages/
│   └── ExecutionStudio.tsx         # Main page
│
├── components/execution-studio/
│   ├── Timeline.tsx                # Chronological event list
│   ├── ExecutionGraph.tsx          # DAG visualization
│   ├── ArchitectureView.tsx        # System architecture
│   ├── ComponentInspector.tsx       # Detailed component info
│   ├── DecisionInspector.tsx        # Decision trace
│   ├── ContextEvolution.tsx         # Context changes
│   ├── PromptViewer.tsx             # System/user prompts
│   ├── RAGExplorer.tsx              # Retrieved chunks
│   ├── LLMViewer.tsx                # Model metrics
│   ├── ReflectionViewer.tsx         # Improvement trace
│   ├── GuardrailViewer.tsx          # Validation checks
│   ├── PerformanceDashboard.tsx     # Metrics
│   └── ReplayControls.tsx           # Play/pause/step
│
├── hooks/
│   ├── useExecutionEvents.ts        # WebSocket subscription
│   ├── useExecutionTrace.ts         # Event querying
│   └── useReplayEngine.ts           # Replay logic
│
└── utils/
    └── eventNormalizer.ts           # Transform events for UI
```

---

## Event Flow Example

### User asks: "What is the project status?"

**Timeline of Events**:

```
1. request_created
   component: "ChatEndpoint"
   action: "receive_query"
   metadata: {"query": "What is the project status?"}

2. supervisor_started
   component: "SupervisorAgent"
   action: "route_query"
   status: "started"

3. agent_selected
   component: "SupervisorAgent"
   action: "select_agents"
   metadata: {
     "selected_agents": ["ProjectAgent", "DocumentAgent"],
     "reasoning": "Query mentions project status and requires documentation"
   }

4. agent_invoked
   component: "ProjectAgent"
   action: "execute"
   status: "started"

5. tool_executed
   component: "ProjectLookupTool"
   action: "lookup_project"
   metadata: {"project_id": 42}

6. llm_called
   component: "LLMClient"
   action: "generate"
   metadata: {
     "model": "claude-opus",
     "tokens_used": 145,
     "cost": 0.002
   }

7. agent_completed
   component: "ProjectAgent"
   action: "execute"
   status: "completed"
   duration_ms: 1250

8. responses_merged
   component: "SupervisorAgent"
   action: "merge_responses"
   metadata: {
     "agent_count": 2,
     "merge_strategy": "consensus"
   }

9. reflection_started
   component: "ReflectionAgent"
   action: "review"
   status: "started"

10. reflection_analysis
    component: "ReflectionAgent"
    action: "detect_hallucinations"
    metadata: {
      "hallucination_risk": 0.3,
      "citation_gaps": []
    }

11. reflection_completed
    component: "ReflectionAgent"
    action: "review"
    status: "completed"
    metadata: {
      "reflection_applied": false,
      "reasoning": "Response is high quality"
    }

12. request_completed
    component: "ChatEndpoint"
    action: "return_response"
    status: "completed"
    duration_ms: 3500
```

---

## Frontend - How It Works

### Event → UI Transformation

**Same UI renders all components** (no hardcoding):

```typescript
// Generic event renderer - works for ANY component
<EventCard event={event}>
  <div>
    <ComponentBadge name={event.component} />
    <ActionLabel action={event.action} />
    <StatusIndicator status={event.status} />
  </div>
  
  <Details>
    <Metric label="Duration" value={event.duration_ms}ms />
    <Metric label="Tokens" value={event.tokens_used} />
    <Metric label="Cost" value={event.cost} />
  </Details>
  
  <JsonViewer data={event.metadata} />
  
  <LearningPanel 
    component={event.component}
    action={event.action}
  />
</EventCard>
```

**When new component is added** (e.g., MemoryAgent):
1. MemoryAgent publishes events like any other component
2. Frontend **automatically** renders them
3. **No frontend code needed**

---

## Integration for Future Components

### Adding Memory System

**Backend Only** (no frontend changes):

```python
# memory.py
from app.execution_studio import event_bus

class MemorySystem:
    async def retrieve(self, query: str):
        event_bus.publish(ExecutionEvent(
            component="MemorySystem",
            action="retrieve_memory",
            status="started",
            metadata={"query": query}
        ))
        
        # ... actual retrieval logic ...
        
        event_bus.publish(ExecutionEvent(
            component="MemorySystem",
            action="retrieve_memory",
            status="completed",
            metadata={"results": results}
        ))
```

**Frontend automatically shows**:
- Memory retrieval events in timeline
- Memory results in JSON viewer
- Memory cost and latency
- Learning explanation for Memory System

---

## Learning Mode Implementation

**Central Explanation Database** (`learning_explanations.py`):

```python
EXPLANATIONS = {
    "SupervisorAgent": {
        "purpose": "Routes queries to specialist agents",
        "problem_solves": "How do we handle multiple domains?",
        "can_skip": False,
        "pattern": "Router Pattern, Strategy Pattern",
        "advantages": ["Specialization", "Parallelism", "Modularity"],
        "tradeoffs": ["Added latency", "Complexity"]
    },
    "ReflectionAgent": {
        "purpose": "Quality review of AI responses",
        "problem_solves": "How do we prevent hallucinations?",
        "can_skip": True,
        "pattern": "Decorator Pattern, Chain of Responsibility",
        "advantages": ["Improved quality", "Confidence scoring"],
        "tradeoffs": ["Added latency", "False positives"]
    }
}
```

Frontend fetches explanations based on `event.component`:

```typescript
const explanation = EXPLANATIONS[event.component];
<LearningPanel
  purpose={explanation.purpose}
  problemSolves={explanation.problem_solves}
  canSkip={explanation.can_skip}
  pattern={explanation.pattern}
  advantages={explanation.advantages}
  tradeoffs={explanation.tradeoffs}
/>
```

---

## WebSocket Streaming

**Real-time event delivery** without polling:

```
Browser
  ↓ WebSocket.send({request_id})
  ↓
Server (EventBusSubscriber)
  ↓ Listens for events with matching request_id
  ↓ WebSocket.send(event)
  ↓
Browser receives event in real-time
  ↓ UI updates instantly
```

---

## Replay Engine

**Pause/Play/Step through execution**:

```
Events stored in database with timestamps

1. Load all events for request_id
2. Sort by timestamp
3. User clicks "Play"
4. Emit events at original intervals
5. UI updates as if happening live
6. User can pause, step forward/back
7. Speed control (1x, 2x, 5x)
```

---

## Backward Compatibility Checklist

✅ No changes to existing HTTP endpoints
✅ No changes to database models
✅ No changes to agent implementations
✅ Event publishing is non-blocking
✅ Event failures don't break system
✅ Existing tests unaffected
✅ AI Chat works exactly as before
✅ All new features are purely additive

---

## Implementation Phases

### Phase 1: Foundation (This Sprint)
- Event Bus (pub/sub)
- Event Store (database)
- Tracer decorator
- Basic integration with Supervisor

### Phase 2: UI (Next Sprint)
- Timeline view
- Execution graph
- Component inspector

### Phase 3: Advanced (Following Sprint)
- Architecture view
- RAG explorer
- Replay engine
- Learning mode

### Phase 4: Auto-Integration (Ongoing)
- Memory system integration
- MCP integration
- Evaluation system integration
- Custom agent integration

---

## File Structure After Implementation

```
backend/app/
├── execution_studio/
│   ├── __init__.py
│   ├── event_bus.py              # 150 lines
│   ├── event_model.py            # 100 lines
│   ├── event_store.py            # 200 lines
│   ├── execution_trace_service.py # 200 lines
│   ├── tracer.py                 # 150 lines
│   ├── learning_explanations.py   # 300 lines
│   └── websocket_server.py       # 250 lines
│
├── routers/
│   └── execution_studio.py        # 300 lines
│
└── models/
    └── execution_event.py         # 50 lines (SQLAlchemy model)

frontend/src/
├── pages/
│   └── ExecutionStudio.tsx        # 200 lines
│
├── components/execution-studio/
│   ├── Timeline.tsx               # 250 lines
│   ├── ExecutionGraph.tsx         # 300 lines
│   ├── ArchitectureView.tsx       # 250 lines
│   ├── ComponentInspector.tsx     # 250 lines
│   ├── DecisionInspector.tsx      # 200 lines
│   ├── ContextEvolution.tsx       # 200 lines
│   ├── PromptViewer.tsx           # 200 lines
│   ├── RAGExplorer.tsx            # 250 lines
│   ├── LLMViewer.tsx              # 150 lines
│   ├── ReflectionViewer.tsx       # 200 lines
│   ├── GuardrailViewer.tsx        # 200 lines
│   ├── PerformanceDashboard.tsx   # 250 lines
│   └── ReplayControls.tsx         # 150 lines
│
├── hooks/
│   ├── useExecutionEvents.ts      # 100 lines
│   ├── useExecutionTrace.ts       # 150 lines
│   └── useReplayEngine.ts         # 200 lines
│
└── utils/
    └── eventNormalizer.ts         # 100 lines

Total: ~5,500 lines (Phase 1 will be ~2,000 lines)
```

---

## Success Criteria

✅ User can watch request execute in real-time
✅ Every component appears in timeline
✅ No frontend code needed for new components
✅ Decisions are explained
✅ Learning mode teaches architecture
✅ Replay shows execution at different speeds
✅ Zero impact on existing system
✅ <100ms event processing latency
✅ Can handle 100 concurrent viewers
✅ All events persisted for auditing

---

## Summary

**AI Execution Studio** creates complete transparency into how the Enterprise AI system works. By using event-driven architecture:

1. **Components** publish what happened
2. **Event Bus** routes to storage + WebSocket
3. **Frontend** renders generic events
4. **Future components** automatically integrate
5. **Users learn** why AI systems do what they do

This foundation enables the entire upcoming multi-agent platform to be visualized without additional development effort.
