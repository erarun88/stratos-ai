# Semantic Events Quick Start

## What Changed

The execution event schema has been completely redesigned to be **self-describing and narrative-focused**. Instead of just tracking which component called which, events now tell the complete story of why things happened, what data transformed, and how components relate.

## Key Files Added

### Backend

- `backend/app/execution_studio/semantic_event.py` - Event schema (142 KB)
- `backend/app/execution_studio/semantic_event_store.py` - Database & queries (300 KB)
- `backend/app/execution_studio/semantic_tracer.py` - High-level API (200 KB)

### Frontend

- `frontend/src/components/execution-studio/ExecutionGraph.tsx` - Visualization (500 lines)
- Updated `ExecutionStudio.tsx` - Integrated new graph view

### Documentation

- `SEMANTIC_EVENTS_ARCHITECTURE.md` - Complete architecture & design
- `backend/SEMANTIC_EVENTS_GUIDE.md` - Usage guide with examples

## How to Use

### For Backend Component Developers

#### Simple Event (Tool)

```python
from app.execution_studio import SemanticTracer, ComponentType

# Create tracer
tracer = SemanticTracer(
    request_id=request_id,
    component="ProjectLookupTool",
    component_type=ComponentType.TOOL,
)

# Start event
event = tracer.start_event(
    action="lookup",
    purpose="Retrieve project information from database",
    reason="Supervisor needs context to answer user question",
)

# Add input info
event.with_input(
    input_type="project_id",
    description="Project identifier",
    key_fields={"project_id": 123},
)

# ... do work ...

# Add output info
event.with_output(
    output_type="project_record",
    description="Complete project with status and budget",
    key_fields={"status": "in_progress", "budget": 50000},
    confidence=0.95,
)

# End event
tracer.end_event(event)
```

#### Orchestration Event (Agent)

```python
event = tracer.start_event(
    action="route_query",
    purpose="Determine which specialist agents should handle this query",
    reason="User asked about multiple domains",
)

# Track decision
event.with_decision(
    decision_type="agent_selection",
    description="Selected ProjectAgent and RiskAgent",
    options_considered=3,
    rationale="User asked about status (project) and risks. These agents have relevant expertise.",
    confidence=0.98,
)

tracer.end_event(event)
```

#### Async Operation

```python
from app.execution_studio import trace_semantic_operation, ComponentType

async with trace_semantic_operation(
    component="LLMClient",
    component_type=ComponentType.INFERENCE,
    action="generate",
    purpose="Generate text using LLM",
) as event:
    event.with_input(
        input_type="prompt",
        description="LLM prompt",
        key_fields={"prompt_length": 1200},
    )
    
    # ... generate ...
    
    event.with_output(
        output_type="text",
        description="Generated response",
        key_fields={"tokens": 250, "length": 450},
        confidence=0.92,
    )

# Automatically completed on exit
```

### For Frontend Developers

#### Display Execution Narrative

```tsx
import ExecutionGraph from './components/execution-studio/ExecutionGraph'

export function MyPage() {
  return (
    <ExecutionGraph requestId={requestId} />
  )
}
```

The component shows:
- **Narrative View**: Full event details with purpose, reason, I/O, decisions
- **Graph View**: Dependency visualization showing relationships
- **Status**: Color-coded execution status
- **Relationships**: How components relate to each other

## Database Schema

The system uses a new table: `semantic_execution_events`

Key fields:
- `event_id` - Unique event identifier
- `request_id` - Trace ID (groups related events)
- `parent_event_id` - Parent for hierarchy
- `purpose`, `reason`, `description` - The story
- `component_type` - Self-describing type (orchestrator, agent, tool, etc.)
- `input_json`, `output_json` - Semantic I/O
- `related_events_json`, `dependencies_json` - Relationships
- `decision_json` - Decision rationale

**No migration needed** - works alongside existing `execution_events` table.

## API Endpoints

### Get Semantic Trace

```
GET /api/execution-studio/semantic/requests/{request_id}/trace
```

Returns all semantic events with full storytelling data.

### Reconstruct Execution Graph

```
GET /api/execution-studio/semantic/requests/{request_id}/graph
```

Returns nodes and edges - complete execution DAG reconstructed from events alone.

## Component Types Available

```python
ComponentType.ORCHESTRATOR        # Routes and coordinates
ComponentType.SPECIALIST_AGENT    # Domain expert agent
ComponentType.TOOL               # Data lookup tool
ComponentType.INFERENCE          # LLM call
ComponentType.VALIDATOR          # Quality/safety check
ComponentType.WORKFLOW           # Multi-step process
ComponentType.DECISION_POINT     # Choice/routing
ComponentType.AGGREGATOR         # Combines results
ComponentType.TRANSFORMER        # Modifies data
```

## Relationship Types Available

```python
RelationshipType.SEQUENTIAL      # Runs after
RelationshipType.PARALLEL        # Runs alongside
RelationshipType.DEPENDENCY      # Needs output from
RelationshipType.FEEDBACK        # Takes result back
RelationshipType.FALLBACK        # Used if first fails
RelationshipType.ALTERNATIVE     # One of multiple options
RelationshipType.VALIDATION_OF   # Validates
RelationshipType.COMPOSITION     # Combined with
```

## Testing in UI

1. **Open Execution Studio**: http://localhost:5173/execution-studio
2. **Ask a question**: Go to AI Chat and ask something like "What's the status of project X?"
3. **View Semantic Trace**: Go back to Execution Studio, select the request
4. **Click "Execution Graph"**: New component shows narrative and dependencies
5. **Click Event**: See full details - purpose, reason, I/O, decisions, relationships

## Key Benefits

✅ **Zero Hardcoding** - UI needs no knowledge of specific agents/components
✅ **Self-Describing** - Events tell their own story
✅ **Graph Reconstruction** - Complete DAG from trace alone
✅ **Decision Visible** - Rationale for each step is explicit
✅ **Extensible** - New component types need no UI changes
✅ **Debuggable** - Clear data transformations and dependencies

## Example Output

### Event in Narrative View

```
🟢 ProjectAgent :: lookup

💡 Purpose
  "Retrieve project information to answer user question"

🎯 Reason
  "Supervisor determined user asked about project status"

📥 Input
  project_id: 123
  Lookup fields: ["status", "budget", "timeline"]

📤 Output
  status: "in_progress"
  budget: 50000 spent: 32000
  Confidence: 95%

🔗 Dependencies
  • Database: For retrieving project records
  • LLMClient: For synthesizing response
```

### Dependency Graph

```
ChatEndpoint (orchestrator)
├─ SupervisorAgent (orchestrator)
│  ├─ ProjectAgent (specialist_agent) ─→ LLMClient (inference)
│  └─ RiskAgent (specialist_agent) ──→ LLMClient (inference)
├─ ReflectionAgent (validator)
└─ ApprovalManager (validator)
```

## Next Steps

1. **Backend**: Start emitting semantic events in your components
   - Use `SemanticTracer` for direct control
   - Use `trace_semantic_operation()` for async
   - Build events incrementally with fluent API

2. **Frontend**: ExecutionGraph component is ready to use
   - Shows narrative by default
   - Can switch to graph view
   - Handles missing data gracefully

3. **Monitor**: Track semantic event usage in execution studio
   - See which components emit events
   - Identify components still using old system
   - Gradually migrate to semantic events

## Troubleshooting

**Events not appearing?**
- Check that component is being invoked
- Verify request_id is set correctly
- Check database table `semantic_execution_events`

**UI not showing narrative?**
- Ensure `/semantic/requests/{id}/trace` API is callable
- Check browser console for errors
- Verify events have purpose/reason/I/O fields

**Want to see existing events?**
- Semantic events are stored separately
- Old `execution_events` table still has old events
- Both systems work in parallel during migration

## Architecture Diagram

```
Component Code (Agent, Tool, etc)
    ↓
SemanticTracer API
    ↓
SemanticExecutionEvent (in-memory)
    ↓
SemanticEventStore (database)
    ↓
PostgreSQL (semantic_execution_events table)
    ↓
API: /semantic/requests/{id}/trace
    ↓
Frontend: ExecutionGraph Component
    ↓
User sees complete execution narrative + graph
```

## Learning More

- **Full Architecture**: Read `SEMANTIC_EVENTS_ARCHITECTURE.md`
- **Usage Examples**: Read `backend/SEMANTIC_EVENTS_GUIDE.md`
- **Code**: Check `backend/app/execution_studio/semantic_*.py`
- **UI**: Check `frontend/src/components/execution-studio/ExecutionGraph.tsx`

---

**Status**: ✅ Ready to use in new code
**Migration**: Can coexist with old `ExecutionEvent` system
**Support**: Full documentation available in repo
