# PHASE C: Planner & Executor
## Task Decomposition for Complex Requests

**Status**: ✅ IMPLEMENTED

---

## OVERVIEW

Phase C introduces task-based planning and execution for complex, multi-step requests.

**Example Problem**:
User: "Prepare an executive review for Project Alpha"

**Before Phase C**: Single LLM call tries to synthesize everything → Lossy result

**After Phase C**:
1. Planner decomposes into ordered tasks:
   - Retrieve project details
   - Retrieve risks
   - Retrieve budget
   - Search documents
   - Summarize findings
   - Generate executive summary

2. Executor runs tasks respecting dependencies
3. Final answer synthesized from all task results

---

## COMPONENTS

### TaskPlanner
**Purpose**: Decompose requests into structured task plans

**Key Methods**:
- `plan(request)` → `ExecutionPlan`
- `_classify_request()` → request type
- `_generate_tasks()` → list of tasks
- `_order_tasks()` → respect dependencies

**Request Types Supported**:
- `executive_review`: Full review with recommendations
- `status_report`: Current status snapshot
- `risk_assessment`: Risk analysis with mitigation
- `timeline_analysis`: Schedule and critical path
- `comparative_analysis`: Compare multiple items
- `general_inquiry`: Simple questions (uses Supervisor)

**Example Task Graph** (Executive Review):
```
task_0 (retrieve_project)
    ↓
task_1 (retrieve_risks)        ← parallel with task_0
    ↓
task_2 (retrieve_financials)   ← parallel with task_0
    ↓
task_3 (retrieve_schedule)     ← parallel with task_0
    ↓
task_4 (search_documents)      ← parallel with task_0
    ↓
task_5 (summarize) ← waits for all above
    ↓
task_6 (generate_executive_summary) ← final
```

**Important**: Tasks 0-4 execute in parallel (independent), then task_5 waits for all.

### TaskExecutor
**Purpose**: Execute task plans with dependency management

**Key Methods**:
- `execute(plan)` → `ExecutionResult`
- `_execute_tasks()` → respects dependencies
- `_execute_task()` → single task execution
- Task-specific executors: `_retrieve_project()`, `_retrieve_risks()`, etc.

**Execution Strategy**:
1. Track task state (pending → running → completed/failed)
2. Find ready tasks (dependencies satisfied)
3. Execute ready tasks in parallel
4. Wait for completion
5. Repeat until all tasks done

**Result Structure**:
```python
ExecutionResult(
    plan: ExecutionPlan,
    task_results: {
        "task_0": TaskResult(...),  # project data
        "task_1": TaskResult(...),  # risks
        ...
    },
    final_answer: str,  # synthesized response
    total_time_ms: float,
    success: bool,
    error: Optional[str]
)
```

---

## REQUEST ROUTING LOGIC

### When to use Supervisor vs Planner?

**Use Supervisor (Simple)** for:
- "What's the status of Project A?"
- "What are the risks?"
- "Show me the budget"
- "Find documents about X"

→ Single agent, fast response

**Use Planner + Executor (Complex)** for:
- "Prepare an executive review"
- "Give me a full status report"
- "Assess risks and impact"
- "Compare projects A and B"

→ Multi-step decomposition, synthesized response

### Integration Pattern

```python
async def chat(request: ChatRequest):
    # Step 1: Route based on complexity
    if is_simple_request(request.query):
        # Use Supervisor (Phase B)
        response = await supervisor.answer(request.query)
    else:
        # Use Planner + Executor (Phase C)
        plan = await planner.plan(request.query)
        result = await executor.execute(plan)
        response = result.final_answer
    
    return response
```

---

## TASK TYPES

```python
class TaskType(Enum):
    # Retrieval
    RETRIEVE_PROJECT = "retrieve_project"
    RETRIEVE_RISKS = "retrieve_risks"
    RETRIEVE_FINANCIALS = "retrieve_financials"
    RETRIEVE_SCHEDULE = "retrieve_schedule"
    SEARCH_DOCUMENTS = "search_documents"
    
    # Analysis
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    COMPARE = "compare"
    
    # Generation
    GENERATE_RECOMMENDATIONS = "generate_recommendations"
    GENERATE_EXECUTIVE_SUMMARY = "generate_executive_summary"
    
    # Composition
    MERGE_RESULTS = "merge_results"
```

---

## EXECUTION FLOW EXAMPLE

**User**: "Prepare an executive review for Project Alpha"

### Step 1: Planner
```
TaskPlanner.plan(request)
  → classify_request() = "executive_review"
  → generate_tasks()
    [
      Task(id="task_0", type=RETRIEVE_PROJECT),
      Task(id="task_1", type=RETRIEVE_RISKS),
      Task(id="task_2", type=RETRIEVE_FINANCIALS),
      Task(id="task_3", type=RETRIEVE_SCHEDULE),
      Task(id="task_4", type=SEARCH_DOCUMENTS),
      Task(id="task_5", type=SUMMARIZE, depends_on=[task_0..4]),
      Task(id="task_6", type=GENERATE_EXECUTIVE_SUMMARY, depends_on=[task_5])
    ]
  → order_tasks() (topological sort)
  → return ExecutionPlan
```

### Step 2: Executor
```
TaskExecutor.execute(plan)
  → _execute_tasks()
    
    Iteration 1 (4 tasks ready: 0,1,2,3,4):
      → _retrieve_project() via Supervisor
        → "Project Alpha on track, Q4 delivery"
      → _retrieve_risks() via Supervisor
        → "2 critical risks: API delay, team shortage"
      → _retrieve_financials() via Supervisor
        → "Budget 85% consumed, $150k remaining"
      → _retrieve_schedule() via Supervisor
        → "85% complete, 2 months remaining"
      → _search_documents() via Supervisor
        → "[doc1] Requirements spec, [doc2] Timeline"
      
      Result: All complete in parallel (~2s)
    
    Iteration 2 (task_5 ready):
      → _summarize()
        → Combines all above results
        → Uses Supervisor to synthesize
        → "Executive summary with key findings"
    
    Iteration 3 (task_6 ready):
      → _generate_executive_summary()
        → Formats for C-level audience
        → Adds recommendations
        → "Executive review ready for board"
  
  → _compose_answer()
    → Return final_answer from task_6
```

### Step 3: Response
```json
{
    "answer": "Executive Review for Project Alpha...",
    "final_answer": "Executive review with recommendations",
    "task_results": {
        "task_0": { "status": "completed", "data": "...", "time_ms": 234 },
        "task_1": { "status": "completed", "data": "...", "time_ms": 212 },
        ...
    },
    "total_time_ms": 2500,
    "success": true
}
```

---

## KEY DESIGN PATTERNS

### 1. Separation of Concerns
- **Planner**: Determines WHAT to do (plan structure)
- **Executor**: Determines HOW to do it (execution mechanics)
- Independent testing possible

### 2. Dependency Tracking
- Tasks specify dependencies explicitly
- Executor respects dependencies
- Enables parallel execution where possible

### 3. Composable Results
- Each task produces result
- Results passed to dependent tasks
- Final answer synthesized from all

### 4. Graceful Degradation
- If task fails, execution continues
- Failed tasks marked as such
- Final answer still composed from successful tasks

---

## SCALABILITY

**Current**: Supports ~10-20 task plans

**For 100+ task plans**:
- Add caching layer (task results cache)
- Implement distributed execution (task queue)
- Add circuit breakers for failing tasks
- Implement timeout per task

**Future**: Swap in Celery + Redis for distributed execution

---

## TESTING STRATEGY

### Unit Tests
```python
# Test planner
plan = await planner.plan("Prepare executive review")
assert len(plan.tasks) == 7
assert plan.tasks[-1].type == TaskType.GENERATE_EXECUTIVE_SUMMARY

# Test executor
result = await executor.execute(plan)
assert result.success
assert len(result.completed_tasks) == 7
```

### Integration Tests
```python
# Test full flow
orchestrator = PlanningOrchestrator(supervisor)
result = await orchestrator.handle("Executive review for Project 1")
assert "executive" in result.lower()
assert "risks" in result.lower()
```

---

## NEXT STEPS

**Phase D**: Reflection Agent
- Reviews response before sending
- Detects hallucinations
- Verifies citations
- Suggests improvements

**Phase E**: Approval Framework
- Gated actions (delete, approve, reassign)
- Approval workflows
- Audit trail

---

## FILES CREATED

```
app/
  orchestration/                    # NEW
    __init__.py
    task_planner.py                 # ✅ TaskPlanner
    task_executor.py                # ✅ TaskExecutor
```

**No changes** to existing files (backward compatible).

---

## STATUS

✅ **Phase C Complete**

Ready for Phase D: Reflection Agent
