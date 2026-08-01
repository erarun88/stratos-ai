# Architectural Decision Record
## StratOS AI Enterprise Platform

---

## ADR-001: Supervisor-Specialist Pattern vs Monolithic Agent

**Status**: ACCEPTED (Phase B)

### Question
How should we structure multiple domain agents?

### Options
1. **Monolithic Agent** (before): Single agent handles all domains
2. **Supervisor-Specialist Pattern** (chosen): Supervisor orchestrates specialists
3. **Direct Tool Invocation**: Skip agents, invoke tools directly
4. **Message Queue**: Each agent processes from queue

### Decision
**Supervisor-Specialist Pattern**

### Rationale
- ✅ Clear separation of concerns (each agent owns its domain)
- ✅ Agents are independently testable
- ✅ New agents added without changing Supervisor
- ✅ Easy to understand request flow
- ✅ Natural parallelization (agents execute concurrently)
- ✅ Scaling path clear (can distribute agents later)

### Trade-offs
- ❌ Slight orchestration overhead (negligible)
- ❌ Supervisor needs LLM access (for intent classification)
  - Mitigated: Using heuristic-based selection (Phase 2: upgrade to LLM)

### Alternatives Considered
**Option 1 (Monolithic)**: Would require refactoring for each new domain. Hard to test in isolation.

**Option 3 (Direct Tools)**: No domain expertise. Tool selection becomes a mess. Doesn't scale.

**Option 4 (Message Queue)**: Adds complexity, latency. Needed only at massive scale.

---

## ADR-002: Standardized Response Format (AgentResponse)

**Status**: ACCEPTED (Phase B)

### Question
How should agents communicate their results?

### Options
1. Each agent returns custom format
2. Standardized AgentResponse (chosen)
3. Minimal response (just answer string)
4. JSON with schema validation

### Decision
**Standardized AgentResponse**

### Rationale
- ✅ Enables result composition (Supervisor merges responses)
- ✅ Propagates quality signals (confidence, hallucination risk)
- ✅ Prepares for Reflection Agent (Phase D)
- ✅ Prepares for Approval Framework (Phase E)
- ✅ Complete execution traceability
- ✅ Consistent interface for all agents

### Fields Included
```python
@dataclass
class AgentResponse:
    answer: str                    # The answer
    confidence: float              # Quality metric
    citations: List[Citation]      # Provenance
    agent_name: str                # Which agent
    execution_time_ms: float       # Performance
    tool_calls: List[str]          # Which tools used
    context_length: int            # Input size
    hallucination_risk: float      # Quality signal
    grounding_ok: bool             # Fact-checked
    approval_required: bool        # For Phase E
    approval_reason: Optional[str] # Why approval needed
    metadata: Dict                 # Extensibility
```

### Why These Fields?
- **answer + confidence**: Core response + trust signal
- **citations**: Grounding mechanism (verify claims)
- **tool_calls + agent_name**: Traceability (which tools, which agent)
- **hallucination_risk + grounding_ok**: Quality metrics (avoid false info)
- **approval_required + approval_reason**: Phase E support
- **metadata**: Future-proof extensibility

### Trade-off
Slightly more verbose than minimal response, but enables composition and quality gates.

---

## ADR-003: Planner ≠ Executor

**Status**: ACCEPTED (Phase C)

### Question
Should Planner and Executor be separate?

### Options
1. Combined (Planner generates and immediately executes)
2. Separate (chosen): Planner generates plan, Executor runs it
3. Three-phase: Planner → Approver → Executor
4. Streaming: Generate and execute incrementally

### Decision
**Separate Planner and Executor**

### Rationale
- ✅ Different concerns (what vs how)
- ✅ Testable independently
- ✅ Enables approval before execution (Phase E path)
- ✅ Can inspect plan before committing resources
- ✅ Easier to debug (see plan before execution)
- ✅ Supports async execution (plan now, execute later)

### Example
```python
# Planner job
plan = await planner.plan(
    "Prepare executive review for Project Alpha"
)
# At this point, user can see what tasks will run

# Executor job (can happen later)
result = await executor.execute(plan)
```

### Trade-off
❌ Minimal overhead (plan generation negligible)

### Why Not Combined?
Combined would force approval AFTER execution, which is too late for dangerous actions (delete, reassign).

### Why Not Three-Phase?
Three-phase adds complexity. Two-phase sufficient.

---

## ADR-004: Base Agent as Abstract Class

**Status**: ACCEPTED (Phase B)

### Question
How should we ensure consistency across agents?

### Options
1. No base class (each agent different)
2. Base class with defaults
3. Abstract base class (chosen)
4. Mixin pattern

### Decision
**Abstract Base Class**

### Rationale
- ✅ Enforces interface (every agent has `answer()`)
- ✅ Provides utilities (citations, confidence calculation)
- ✅ Prevents implementation mistakes
- ✅ Type hints work properly
- ✅ Inheritance is familiar pattern

### Example Enforcement
```python
class Agent(ABC):
    @abstractmethod
    def _register_tools(self): pass
    
    @abstractmethod
    def get_system_prompt(self): pass
    
    @abstractmethod
    async def answer(self, query, ...): pass
```

If subclass forgets to implement, Python fails at instantiation.

### Trade-off
❌ Slightly verbose (but clarity > brevity)

---

## ADR-005: Heuristic-Based Agent Selection (Phase B)

**Status**: ACCEPTED (with Phase 3 upgrade path)

### Question
How should Supervisor decide which agents to invoke?

### Options
1. **Heuristic** (chosen): Keyword matching in query
2. **LLM-based**: Ask LLM which agents are needed
3. **ML classifier**: Train model on agent-query pairs
4. **Routing table**: Manual configuration

### Decision
**Heuristic Now, LLM Later**

### Phase B Implementation
```python
if "budget" in query_lower:
    selected.append("finance")
if "risk" in query_lower:
    selected.append("risk_management")
```

**Pros**:
- ✅ Fast (no LLM call)
- ✅ Deterministic (same query, same agents)
- ✅ Cheap (no tokens)

**Cons**:
- ❌ Misses nuance ("How risky is our budget?")
- ❌ Requires manual keyword list

### Phase 3 Upgrade Path
```python
# Future: LLM-based intent classification
intent = await self.llm_client.classify_intent(query)
selected_agents = self.agent_registry[intent]
```

**Why not Phase B?**
- One extra LLM call per query
- +500ms latency
- +$0.001 per query
- Phase B focuses on multi-agent orchestration, not optimization

### Acceptable Trade-off
For Phase B, heuristic is sufficient. Production queries will be specific ("Show me Project Alpha budget"), not ambiguous.

---

## ADR-006: Parallel Task Execution with Dependency Tracking

**Status**: ACCEPTED (Phase C)

### Question
How should Executor manage task execution?

### Options
1. Sequential: One task at a time
2. Parallel with dependencies (chosen): Parallel where independent
3. Fully parallel: Ignore dependencies
4. Distributed: Use task queue

### Decision
**Parallel with Dependency Tracking**

### Rationale
- ✅ Reduce latency: 7 sequential tasks (~14s) → parallel tasks (~2s)
- ✅ Respect dependencies: Can't summarize before retrieving
- ✅ Maximize throughput: All independent tasks run concurrently
- ✅ Simple implementation: Topological sort + asyncio.gather()

### Example
```
task_0 (retrieve_project)
    ├─ Independent: No dependencies
    └─ Runs IMMEDIATELY

task_1 (retrieve_risks)
    ├─ Independent: No dependencies
    └─ Runs IMMEDIATELY (parallel with task_0)

task_2 (retrieve_budget)
    ├─ Independent: No dependencies
    └─ Runs IMMEDIATELY (parallel with task_0, task_1)

task_5 (summarize)
    ├─ Depends on: task_0, task_1, task_2
    └─ Runs AFTER all above complete
```

**Result**: 3 independent tasks → 1 dependent task takes ~5s instead of ~15s.

### Trade-off
❌ Slight complexity (dependency tracking), but necessary for correctness.

---

## ADR-007: Backward Compatibility Over Clean Slate

**Status**: ACCEPTED (Phase B)

### Question
Should we maintain HTTP API compatibility?

### Options
1. **Backward compatible** (chosen): Keep /chat endpoint, update internals
2. **New API**: Create /chat/v2 with new format
3. **Breaking change**: Update existing /chat

### Decision
**Maintain Backward Compatibility**

### Why
- ✅ Existing clients (frontend, scripts) continue working
- ✅ No downtime during migration
- ✅ Phased rollout possible
- ✅ Enterprise requirement (don't break customers)

### Implementation
```python
# Old request format: still works
POST /chat {
    "query": "...",
    "project_id": 1,
    "response_mode": "concise"
}

# Old response format: still works
{
    "answer": "...",
    "citations": [...],
    "confidence": 0.9,
    "response_mode": "concise",
    
    # NEW: non-breaking additions
    "agents_used": ["project_management"],  # Existing clients ignore
    "metadata": {"...": "..."}
}
```

### Non-Breaking Additions
- New fields in response (clients ignore unknown fields)
- New endpoints (/chat/agents)
- New query parameters (future)

---

## ADR-008: Supervisor Should NOT Contain Domain Logic

**Status**: ACCEPTED (Phase B)

### Question
Should Supervisor have domain knowledge?

### Options
1. **Pure Orchestrator** (chosen): Supervisor routes only, no domain logic
2. **Smart Supervisor**: Supervisor has fallback logic for edge cases
3. **Hybrid**: Supervisor + agents share logic

### Decision
**Pure Orchestrator**

### Rationale
- ✅ Supervisor remains simple (routing only)
- ✅ Adding domain agents doesn't change Supervisor
- ✅ Domain logic isolated in agents (easier to test)
- ✅ Clear separation of concerns

### Example
```python
# ❌ WRONG: Supervisor with domain logic
class Supervisor:
    async def answer(self, query):
        if "executive" in query:
            # Supervisor knows about executive reviews! 
            # This is domain logic
            response = await self._generate_executive_format()

# ✅ RIGHT: Pure routing
class Supervisor:
    async def answer(self, query):
        agents = self._select_agents(query)  # Just routing
        responses = await self._invoke_agents(agents)  # Just orchestration
        return self._merge(responses)  # Just merging
```

### Trade-off
Supervisor slightly verbose, but clarity wins.

---

## ADR-009: Tool Manager as Separate Component

**Status**: ACCEPTED (Existing, maintained)

### Question
Should tools be managed separately from agents?

### Decision
**Yes, ToolManager separate**

### Rationale
- ✅ Tools are reusable across agents
- ✅ Tool registration centralized
- ✅ Parallel execution managed in one place
- ✅ Easy to add/remove tools

### Maintained From Phase B
No changes, Tool architecture is sound.

---

## ADR-010: Citations as First-Class Object

**Status**: ACCEPTED (Phase B)

### Question
How should we handle citations?

### Options
1. Citations in response metadata
2. Citations as first-class (chosen)
3. Inline citations in answer text
4. Separate citations endpoint

### Decision
**First-Class Citation Object**

### Rationale
- ✅ Structured provenance (not free text)
- ✅ Verifiable by Reflection Agent (Phase D)
- ✅ Type-safe (source, relevance, tool known)
- ✅ Supports citation metrics (relevance score)

### Example
```python
Citation(
    source="project_lookup",
    content="Project Alpha status: on track",
    relevance=0.95,
    tool="project_lookup"
)
```

### Why Not Inline?
Inline citations would require:
- Parsing answer text (fragile)
- Matching text spans (complex)
- Verification harder (no structure)

---

## PRINCIPLES APPLIED

### 1. SOLID Principles
- **S**ingle Responsibility: Each agent owns one domain
- **O**pen/Closed: New agents added without changing Supervisor
- **L**iskov Substitution: All agents implement Agent interface
- **I**nterface Segregation: Agents only expose `answer()`
- **D**ependency Inversion: Agents depend on abstractions (LLMClient), not implementations

### 2. Design Patterns
- **Strategy**: Agents as strategies
- **Template Method**: Base Agent defines skeleton
- **Factory**: Tool creation and management
- **Observer**: Logging throughout
- **Composite**: Result merging

### 3. Clean Architecture
```
Agents
    ↓ (depend on)
Tools & Services
    ↓ (depend on)
Database & APIs
    ↓ (depend on)
External systems
```

Dependencies point inward, not outward.

### 4. Testability
- Mock tools for agent testing
- Mock agents for Supervisor testing
- Mock Supervisor for executor testing
- Each component independently verifiable

---

## FUTURE CONSIDERATIONS

### Phase D: Reflection Agent
- Will inspect AgentResponse for quality signals
- Will verify citations exist
- Will detect hallucinations post-hoc

### Phase E: Approval Framework
- Will use approval_required flag in AgentResponse
- Will implement approval_reason field
- Will create approval registry

### Phase F: Advanced Routing
- Will upgrade heuristic to LLM-based intent
- Will add agent confidence scores
- Will implement agent selection optimization

---

## DOCUMENT VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | Phase A | Initial decisions |
| 1.1 | Phase B | Supervisor + agent decisions |
| 1.2 | Phase C | Planner + executor decisions |
| 1.3 | Current | ADR consolidation |

---

## CONCLUSION

These architectural decisions create a **maintainable, scalable, enterprise-grade multi-agent platform** that:

✅ Solves problems cleanly  
✅ Extensible for new agents/tools  
✅ Testable in isolation  
✅ Future-proof for Phases D & E  
✅ Production-ready  

Each decision had trade-offs considered. Future maintainers should reference this document when considering changes.
