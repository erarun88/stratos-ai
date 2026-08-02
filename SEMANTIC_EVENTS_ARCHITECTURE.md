# Semantic Execution Events Architecture

## Executive Summary

The execution event schema has been completely redesigned to tell the **story of the request**, not just the mechanics. Every event is now self-describing with purpose, reason, input/output summaries, and relationships. The UI can reconstruct the complete execution graph from the trace alone, **without any hardcoded knowledge** of agents or components.

## Problem Statement

**Before**: Events were mechanical - "ProjectAgent called LLMClient with query X"
- UI had to hardcode knowledge of every agent/component
- Why something happened was invisible
- What transformed during execution was unclear
- Hard to debug or understand decisions

**After**: Events tell the story - "ProjectAgent routed query to specialist agents because user asked about risks and budget"
- UI is component-agnostic, understands narrative
- Purpose and reasoning are explicit
- I/O transformations are documented
- Clear decision trails

## Core Event Schema

### SemanticExecutionEvent

```python
@dataclass
class SemanticExecutionEvent:
    # === IDENTITY & HIERARCHY ===
    event_id: str                          # Unique event ID
    request_id: str                        # Trace ID
    parent_event_id: Optional[str]        # Parent event for hierarchy
    sequence_in_parent: int                # Order among siblings
    
    # === THE STORY ===
    purpose: str                           # Why this event exists
    reason: str                            # What triggered it
    description: str                       # Narrative of what happened
    
    # === WHAT & WHO ===
    component: str                         # "SupervisorAgent", "ProjectTool", etc.
    component_type: ComponentType          # "orchestrator", "specialist_agent", "tool", etc.
    component_role: str                    # "coordinator", "specialist", "validator"
    action: str                            # "route_query", "lookup_project", "generate"
    
    # === I/O & SEMANTICS ===
    input: InputSummary                    # What data was used
    output: OutputSummary                  # What was produced
    
    # === RELATIONSHIPS ===
    related_events: List[RelatedEvent]    # How this event relates to others
    dependencies: List[ComponentDependency]  # Components this depends on
    decision: Optional[Decision]           # Decision made during execution
    
    # === TIMING & QUALITY ===
    timestamp: datetime
    duration_ms: float
    status: EventStatus
    error: Optional[str]
    warnings: List[str]
    
    # === RESOURCES ===
    tokens_used: int
    tokens_input: int
    tokens_output: int
    cost: float
    
    # === METADATA ===
    metadata: Dict[str, Any]
```

### InputSummary

```python
@dataclass
class InputSummary:
    type: str                              # "query", "project_data", "documents"
    description: str                       # Human-readable summary
    key_fields: Dict[str, Any]            # Important input parts
    source_event_ids: List[str]           # Where input came from
```

### OutputSummary

```python
@dataclass
class OutputSummary:
    type: str                              # "answer", "recommendations", "metrics"
    description: str                       # Human-readable summary
    key_fields: Dict[str, Any]            # Important output parts
    confidence: float                      # 0-1, confidence in output
    quality_score: float                   # 0-1, quality of output
```

### Decision

```python
@dataclass
class Decision:
    type: str                              # "routing", "selection", "synthesis"
    description: str                       # What was decided
    options_considered: int                # How many alternatives
    rationale: str                         # Why this choice
    confidence: float                      # 0-1, confidence in decision
```

## Component Types

Self-describing component categories:

| Type | Purpose | Examples |
|------|---------|----------|
| `ORCHESTRATOR` | Routes and coordinates | SupervisorAgent, Planner |
| `SPECIALIST_AGENT` | Domain expert | ProjectAgent, RiskAgent, FinanceAgent |
| `TOOL` | Data lookup/manipulation | ProjectLookupTool, RiskLookupTool |
| `INFERENCE` | LLM call | LLMClient.generate |
| `VALIDATOR` | Quality/safety check | ReflectionAgent, ApprovalManager |
| `WORKFLOW` | Multi-step process | RAG pipeline |
| `DECISION_POINT` | Choice/routing | Selection logic |
| `AGGREGATOR` | Combines results | Response merger |
| `TRANSFORMER` | Modifies data | Output formatter |

## Relationship Types

Describes how events relate:

| Relationship | Meaning |
|--------------|---------|
| `SEQUENTIAL` | Runs after |
| `PARALLEL` | Runs alongside |
| `DEPENDENCY` | Needs output from |
| `FEEDBACK` | Takes result back |
| `FALLBACK` | Used if first fails |
| `ALTERNATIVE` | One of multiple options |
| `VALIDATION_OF` | Validates |
| `COMPOSITION` | Combined with |

## Data Flow

### Emission Pipeline

```
Component calls SemanticTracer.start_event()
    ↓
Event created with purpose/reason
    ↓
Event enhanced with input/output/decision
    ↓
SemanticTracer.end_event() stores event
    ↓
Event stored in SemanticEventModel (PostgreSQL)
```

### Retrieval Pipeline

```
API: GET /semantic/requests/{request_id}/trace
    ↓
SemanticEventStore.get_request_trace()
    ↓
Reconstructs SemanticExecutionEvent objects from DB
    ↓
Serialized to JSON with full storytelling data
    ↓
Frontend receives complete semantic trace
```

### Graph Reconstruction

```
Frontend receives semantic events
    ↓
Builds parent-child tree from parent_event_id
    ↓
Extracts dependencies from related_events
    ↓
Constructs nodes (events) and edges (relationships)
    ↓
Visualizes execution graph without hardcoding
```

## Implementation

### Backend Components

1. **`semantic_event.py`** (NEW)
   - `SemanticExecutionEvent` class
   - Component and relationship enums
   - Builder pattern for easier construction

2. **`semantic_event_store.py`** (NEW)
   - `SemanticEventModel` - ORM model
   - `SemanticEventStore` - Query service
   - Conversion to/from DB

3. **`semantic_tracer.py`** (NEW)
   - `SemanticTracer` - High-level API
   - `trace_semantic_operation()` - Async context manager
   - Automatic parent-child tracking

4. **`trace_context.py`** (ENHANCED)
   - Event stack tracking
   - Automatic parent assignment

5. **`execution_studio_api.py`** (UPDATED)
   - `/semantic/requests/{id}/trace` - Get events
   - `/semantic/requests/{id}/graph` - Get reconstructed graph

### Frontend Components

1. **`ExecutionGraph.tsx`** (NEW)
   - **Narrative View**: Event details with purpose/reason/I/O
   - **Graph View**: Dependency visualization
   - Component type color coding
   - Status indicators
   - Relationship visualization

### Database Schema

```sql
CREATE TABLE semantic_execution_events (
    event_id VARCHAR(36) PRIMARY KEY,
    request_id VARCHAR(36) NOT NULL,
    parent_event_id VARCHAR(36),
    sequence_in_parent INT,
    
    -- The Story
    purpose TEXT NOT NULL,
    reason TEXT,
    description TEXT,
    
    -- What & Who
    component VARCHAR(255),
    component_type VARCHAR(50),
    component_role VARCHAR(100),
    action VARCHAR(255),
    
    -- I/O (JSON)
    input_json JSON,      -- {type, description, key_fields, source_event_ids}
    output_json JSON,     -- {type, description, key_fields, confidence}
    
    -- Relationships (JSON)
    related_events_json JSON,   -- [{event_id, relationship, description}]
    dependencies_json JSON,     -- [{component, reason, criticality}]
    decision_json JSON,         -- {type, description, rationale}
    
    -- Timing & Quality
    timestamp DATETIME,
    duration_ms FLOAT,
    status VARCHAR(50),
    error TEXT,
    warnings_json JSON,
    
    -- Resources
    tokens_used INT,
    tokens_input INT,
    tokens_output INT,
    cost FLOAT,
    
    -- Metadata
    metadata_json JSON,
    created_at DATETIME
);

CREATE INDEX idx_semantic_request_component ON semantic_execution_events(request_id, component);
CREATE INDEX idx_semantic_parent_sequence ON semantic_execution_events(parent_event_id, sequence_in_parent);
```

## Usage Example

### Before (Mechanical Events)

```
Event: component=ProjectAgent, action=execute
Event: component=ProjectLookupTool, action=query
Event: component=LLMClient, action=generate
```

UI has to hardcode: "ProjectAgent calls tools, then calls LLM"

### After (Semantic Events)

```
Event {
  purpose: "Retrieve project information from database"
  reason: "SupervisorAgent needs context to answer user query"
  description: "Looking up project by ID to get status and timeline"
  input: {
    type: "project_id"
    description: "Project identifier"
    key_fields: {project_id: 123}
  }
  output: {
    type: "project_data"
    description: "Complete project record"
    key_fields: {status: "in_progress", budget: 50000}
  }
}
```

UI reads: "ProjectLookupTool retrieved project data for SupervisorAgent to answer user question"
**No hardcoding needed.**

## Key Advantages

### 1. **Zero Hardcoding**
- Add new agent? No UI changes needed
- New component type? UI handles it automatically
- Change routing logic? Trace tells the story

### 2. **Narrative Understanding**
- UI shows why things happened, not just that they happened
- Complete execution story is self-contained in events
- Decision rationale is explicit

### 3. **Graph Reconstruction**
- Complete DAG from events alone
- No separate graph schema
- Relationships are data, not structure

### 4. **Educational**
- Users see reasoning behind each step
- Decision points are clear
- Alternative paths shown

### 5. **Debuggable**
- Purpose/reason make failures clear
- Input/output show data transformation
- Relationships show dependencies

### 6. **Extensible**
- New component types: just add enum
- New relationship types: just add enum
- New metadata: just add to key_fields

## API Examples

### Get Complete Trace

```bash
curl http://localhost:8000/api/execution-studio/semantic/requests/req-123/trace
```

Response:
```json
{
  "request_id": "req-123",
  "event_count": 15,
  "events": [
    {
      "event_id": "evt-1",
      "parent_event_id": null,
      "component": "ChatEndpoint",
      "component_type": "orchestrator",
      "purpose": "Receive and process user chat query",
      "reason": "User submitted question via chat API",
      "description": "ChatEndpoint accepted query about project risks",
      "input": {
        "type": "query",
        "description": "User question",
        "key_fields": {"query": "What are the risks for project ABC?"}
      },
      "output": {
        "type": "answer",
        "description": "Response sent to user",
        "confidence": 0.92
      }
    },
    ...
  ]
}
```

### Reconstruct Graph

```bash
curl http://localhost:8000/api/execution-studio/semantic/requests/req-123/graph
```

Response:
```json
{
  "request_id": "req-123",
  "nodes": [
    {
      "id": "evt-1",
      "label": "ChatEndpoint::receive_query",
      "component": "ChatEndpoint",
      "component_type": "orchestrator",
      "purpose": "Receive and process user chat query",
      "status": "completed"
    },
    ...
  ],
  "edges": [
    {
      "source": "evt-1",
      "target": "evt-2",
      "relationship": "parent-child",
      "label": "0"
    },
    {
      "source": "evt-2",
      "target": "evt-3",
      "relationship": "parallel",
      "label": "ProjectAgent runs alongside RiskAgent"
    }
  ]
}
```

## Migration Strategy

### Phase 1 (Current): Coexistence
- New `SemanticExecutionEvent` system available
- Old `ExecutionEvent` system still works
- Dual emission for backward compatibility

### Phase 2: Semantic Primary
- Semantic events used for new features
- Old events serve as fallback
- UI prefers semantic where available

### Phase 3: Deprecation
- Old event system marked deprecated
- Documentation points to semantic
- Migration period for components

### Phase 4: Removal
- Old event system removed
- Complete semantic stack
- New components only emit semantic events

## Future Enhancements

1. **Event Aggregation**: Combine related events into "phases"
2. **Execution Styles**: Render execution as flowchart, timeline, or tree
3. **Cost Attribution**: Trace cost through component chain
4. **A/B Testing**: Compare execution graphs for different routing
5. **Performance Analytics**: Identify bottlenecks from graph structure
6. **Audit Trail**: Use semantic events for compliance logging

## Conclusion

The semantic event schema transforms the execution trace from a technical log into a **complete, self-describing narrative** of the request. The UI becomes component-agnostic, users understand the reasoning behind each step, and debugging becomes investigation rather than archaeology.

No hardcoded knowledge. No special cases. Just data that tells its own story.
