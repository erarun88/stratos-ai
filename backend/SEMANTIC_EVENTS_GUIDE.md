# Semantic Execution Events Guide

## Overview

The new semantic event system transforms execution traces from mechanics-focused (which component called which) to **narrative-focused** (why did this happen, what did it produce, what was the reasoning).

Every event tells part of the story of the request. The UI can reconstruct the complete execution graph and narrative **without any hardcoded knowledge** of agents, components, or domain logic.

## Key Concepts

### Event Schema

Each `SemanticExecutionEvent` includes:

- **Identity**: `event_id`, `request_id`, `parent_event_id`, `sequence_in_parent`
- **The Story**: `purpose`, `reason`, `description`
- **Component Info**: `component`, `component_type`, `component_role`, `action`
- **I/O & Semantics**: `input` (type, description, key_fields), `output` (type, description, key_fields, confidence)
- **Relationships**: `related_events`, `dependencies`, `decision`
- **Timing & Resources**: `duration_ms`, `tokens_used`, `cost`
- **Quality**: `status`, `error`, `warnings`

### Component Types

```python
ComponentType.ORCHESTRATOR      # Routes and coordinates (SupervisorAgent)
ComponentType.SPECIALIST_AGENT  # Domain expert (ProjectAgent, RiskAgent)
ComponentType.TOOL              # Data lookup/manipulation (ProjectLookupTool)
ComponentType.INFERENCE         # LLM call (LLMClient)
ComponentType.VALIDATOR         # Quality/safety check (ReflectionAgent)
ComponentType.WORKFLOW          # Multi-step process
ComponentType.DECISION_POINT    # Choice/routing logic
ComponentType.AGGREGATOR        # Combines results
ComponentType.TRANSFORMER       # Modifies data
```

### Relationship Types

```python
RelationshipType.SEQUENTIAL     # Runs after
RelationshipType.PARALLEL       # Runs alongside
RelationshipType.DEPENDENCY     # Needs output from
RelationshipType.FEEDBACK       # Takes result back
RelationshipType.FALLBACK       # Used if first fails
RelationshipType.ALTERNATIVE    # One of multiple options
RelationshipType.VALIDATION_OF  # Validates
RelationshipType.COMPOSITION    # Combined with
```

## Usage Examples

### Example 1: Simple Operation

```python
from app.execution_studio import SemanticTracer, ComponentType

tracer = SemanticTracer(
    request_id=request_id,
    component="ProjectLookupTool",
    component_type=ComponentType.TOOL,
)

event = tracer.start_event(
    action="lookup_project",
    purpose="Retrieve project information from database",
    reason="SupervisorAgent needs project context to answer question",
    description="Looking up project by ID to get status, timeline, and risk information",
)

# Add input information
event.with_input(
    input_type="project_id",
    description="Project identifier",
    key_fields={"project_id": 123, "lookup_fields": ["status", "budget", "team"]},
)

# ... perform the lookup ...

# Add output information
event.with_output(
    output_type="project_data",
    description="Complete project record including metadata and status",
    key_fields={
        "id": 123,
        "name": "Website Redesign",
        "status": "in_progress",
        "budget": 50000,
        "spent": 32000,
    },
    confidence=0.95,
    quality_score=0.9,
)

tracer.end_event(event)
```

### Example 2: Decision Event

```python
# SupervisorAgent routing decision
event = tracer.start_event(
    action="route_query",
    purpose="Determine which specialist agents should handle this query",
    reason="User asked about project risks and budget",
)

# Track the decision
event.with_decision(
    decision_type="agent_selection",
    description="Selected RiskAgent for risk assessment and FinanceAgent for budget analysis",
    options_considered=3,  # Could have picked subset, parallel, etc.
    rationale="User query mentions both 'risks' (domain: risk_management) and 'budget' (domain: finance). Both agents can provide relevant expertise in parallel.",
    confidence=0.98,
)

event.with_output(
    output_type="routing_decision",
    description="Selected 2 specialist agents to invoke in parallel",
    key_fields={
        "selected_agents": ["RiskAgent", "FinanceAgent"],
        "execution_mode": "parallel",
        "reason": "Independent expertise, no dependencies",
    },
    confidence=0.98,
)

tracer.end_event(event)
```

### Example 3: Inference Event

```python
# LLM call event
event = tracer.start_event(
    action="generate",
    purpose="Generate answer synthesis combining project and risk insights",
    reason="Both specialist agents completed; now need unified response",
    description="Calling LLM to synthesize project data and risk analysis into coherent answer",
)

event.with_input(
    input_type="synthesis_prompt",
    description="LLM prompt with project context, risk analysis, and synthesis instructions",
    key_fields={
        "project_context": "50% complete, on budget",
        "risks_identified": 3,
        "analysis_length": 1500,  # characters
    },
)

event.with_output(
    output_type="answer",
    description="Synthesized answer addressing user question with project insights and risk implications",
    key_fields={
        "answer_length": 450,  # characters
        "sections": ["project_status", "risk_summary", "recommendations"],
    },
    confidence=0.87,
    quality_score=0.92,
)

# Add relationships if we know other events
event.with_related_event(
    event_id="project_agent_event_id",
    relationship=RelationshipType.DEPENDENCY,
    description="Used project data from ProjectAgent to inform synthesis",
)

tracer.end_event(event)
```

### Example 4: Using Semantic Tracer Async

```python
from app.execution_studio import trace_semantic_operation, ComponentType

async with trace_semantic_operation(
    request_id=request_id,
    component="ReflectionAgent",
    component_type=ComponentType.VALIDATOR,
    action="review_quality",
    purpose="Quality check: verify answer meets standards and is well-grounded",
    reason="Phase D: Reflection for quality improvement",
) as event:
    event.with_input(
        input_type="answer",
        description="Generated answer to be quality-checked",
        key_fields={"length": 450, "sections": 3},
    )
    
    # ... quality checks ...
    
    event.with_output(
        output_type="review_result",
        description="Quality assessment: answer is well-grounded with good citations",
        key_fields={
            "grounding_ok": True,
            "hallucination_risk": 0.05,
            "citation_quality": 0.92,
        },
        confidence=0.9,
    )

# Event auto-completes when exiting context
```

## How the UI Reconstructs the Execution Story

### 1. **Execution Narrative View**

Shows each event with its full context:
- Component type with color coding
- Purpose (why this step exists)
- Reason (what triggered it)
- Input summary (what data it used)
- Output summary (what it produced)
- Confidence scores
- Decision rationale

### 2. **Dependency Graph**

Reconstructs from:
- `parent_event_id` → Parent-child relationships
- `related_events` → Cross-cutting relationships
- `dependencies` → Component-level dependencies
- Event types → Parallel execution lanes

### 3. **Critical Path Analysis**

Computed from:
- Sequential relationships
- Dependency chains
- Duration metrics
- Failure propagation

### 4. **Parallel Execution Visualization**

Shown via:
- Events at same depth level
- Events with no dependency relationships
- `RelationshipType.PARALLEL` markers

## API Endpoints

### Get Semantic Trace

```bash
GET /api/execution-studio/semantic/requests/{request_id}/trace
```

Returns all semantic events with full storytelling information.

### Reconstruct Execution Graph

```bash
GET /api/execution-studio/semantic/requests/{request_id}/graph
```

Returns nodes and edges reconstructed from events:
- Nodes: Events with metadata
- Edges: Relationships and dependencies
- No hardcoded knowledge needed

## Key Benefits

✅ **Self-Describing**: Events tell the story; UI needs no hardcoding  
✅ **Narrative First**: Purpose and reason explain the "why"  
✅ **Semantic Rich**: Input/output summaries show data transformation  
✅ **Graph Reconstruction**: Complete dependency graph from trace alone  
✅ **Educational**: Users understand the reasoning behind each step  
✅ **Debuggable**: Easy to see where decisions were made  
✅ **Extensible**: New component types need no UI changes  

## Migration Path

1. **Phase 1**: Emit both old `ExecutionEvent` and new `SemanticExecutionEvent`
2. **Phase 2**: UI displays semantic events where available, falls back to old events
3. **Phase 3**: Deprecate old event system, fully semantic
4. **Phase 4**: Remove legacy code

## Example: Full Request Trace

```
ChatEndpoint.receive_query
├─ SupervisorAgent.route_query (PURPOSE: determine which agents)
│  ├─ _determine_agents (analyze query semantics)
│  └─ _invoke_agents (call in parallel)
│     ├─ ProjectAgent.answer (get project context)
│     │  ├─ _determine_tools (decide what to query)
│     │  ├─ ProjectLookupTool.execute (fetch project data)
│     │  ├─ _build_context (prepare context for LLM)
│     │  └─ LLMClient.generate (synthesize project info)
│     └─ RiskAgent.answer (analyze risks)
│        ├─ _determine_tools (find risk documents)
│        ├─ RiskLookupTool.execute (fetch risks)
│        └─ LLMClient.generate (analyze risk context)
├─ ReflectionAgent.review (quality check)
├─ ApprovalManager.check (determine if approval needed)
└─ ChatEndpoint.return_response (send to user)
```

Each event in this tree includes its purpose, reason, inputs, outputs, and relationships.
