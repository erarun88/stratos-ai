# StratOS AI - Architecture Review & Transformation Plan
## Lead AI Architect Review - August 2026

---

## PHASE A: CURRENT STATE ANALYSIS

### Existing Architecture

**Current Structure:**
```
app/
  ai/
    - llm_client.py (OpenAI integration)
    - project_agent.py (Monolithic agent)
    - context_builder.py
    - guardrails.py
    - memory/
    - prompts.py
    - response_formatter.py
  tools/
    - base.py (Tool abstraction)
    - manager.py (Tool orchestration)
    - project_lookup_tool.py
    - risk_lookup_tool.py
    - schedule_lookup_tool.py
    - semantic_search_tool.py
  routers/
    - chat.py (HTTP endpoint)
  services/
    - embedding services
    - document services
    - RAG infrastructure
```

### STRENGTHS

1. **Sound Tool Architecture**
   - Tool base class with clear interface
   - Tool manager for orchestration
   - Good separation of concerns per tool
   - ✓ Extensible: New tools can be added easily

2. **Existing Abstractions**
   - LLMClient abstraction (supports multiple providers)
   - MemoryService for conversation history
   - ContextBuilder for structured context
   - Guardrails for hallucination detection
   - ResponseFormatter for output formatting

3. **Production-Ready Infrastructure**
   - Embedding pipeline with background workers
   - Document RAG system functional
   - Semantic search operational
   - Proper async/await patterns

4. **Good Logging**
   - Structured logging in place
   - Tool execution tracking
   - Response quality metrics

### CRITICAL ISSUES IDENTIFIED

#### 1. **Monolithic ProjectAgent** ⚠️ CRITICAL
   - **Problem**: Single agent handles ALL domains (projects, risks, schedules, documents)
   - **Impact**: Unclear responsibility boundaries
   - **Why it matters**: Cannot scale to 20+ specialized agents without major refactoring
   - **Current code**: Lines 51-248 of project_agent.py are doing domain detection internally

   **Evidence**:
   ```python
   # Heuristic-based tool selection (lines 224-246)
   if any(word in query.lower() for word in ["risk", "issue", "blocker"]):
       # ProjectAgent deciding to use RiskLookupTool
   ```

   **Problem**: Each new agent would replicate this pattern → code duplication

#### 2. **No Orchestration Layer** ⚠️ CRITICAL
   - **Problem**: ProjectAgent directly invokes tools; no supervisor pattern
   - **Impact**: Cannot route queries to multiple specialized agents in parallel
   - **Example**: Query "What are project risks and budget status?" should invoke 2 agents in parallel, not sequentially
   - **Current behavior**: Single agent tries to handle both

#### 3. **No Planner/Executor Pattern** ⚠️ HIGH
   - **Problem**: Complex requests get immediate response, not decomposed into steps
   - **Example**: "Prepare executive review for Project Alpha" needs:
     - Retrieve project metadata
     - Get financial data
     - Analyze risks
     - Fetch relevant documents
     - Generate summary
     - Format for executive
   - **Current behavior**: Single LLM call with all context jumbled together

#### 4. **Tight Coupling Between Tools and ProjectAgent** 🔴 MEDIUM
   - **Problem**: Tool selection logic is hardcoded in agent
   - **Impact**: Cannot plug in new agents or tool discovery mechanisms
   - **Evidence**: Lines 209-248 of project_agent.py have string matching for tool selection

#### 5. **No Reflection/Validation** 🔴 MEDIUM
   - **Problem**: Response goes straight to user without quality review
   - **Issue**: Hallucinations might slip through despite guardrails
   - **Missing**: Second-pass validation, citation verification

#### 6. **No Approval Workflow** 🔴 MEDIUM
   - **Problem**: No mechanism to gate dangerous actions
   - **Examples that should require approval**:
     - Deleting projects
     - Approving budgets
     - Changing project status
     - Assigning personnel
   - **Current**: Agents can recommend anything without guardrails

#### 7. **Response Formatter is Trivial** 🟡 LOW
   - **Problem**: Lines 145-149 call formatter but formatter is placeholder
   - **Impact**: Response modes (concise/detailed/executive) not truly implemented
   - **Opportunity**: Proper formatter with structured output per mode

#### 8. **Tool Results Not Structured** 🟡 LOW
   - **Problem**: Tool results are dict-based, no type safety
   - **Impact**: Hard to compose results from multiple agents
   - **Example**: Cannot guarantee format when merging results from ProjectAgent + FinanceAgent

### OPPORTUNITIES

1. **Upgrade Tool System**
   - Add metadata: cost, latency requirements, dependencies
   - Implement tool discovery (agents request capabilities, don't hardcode)
   - Add rate limiting, caching

2. **Build Supervisor Agent**
   - Stateless orchestrator
   - Routes to correct specialists
   - Merges results intelligently
   - Handles parallel execution

3. **Implement Planning System**
   - Decompose complex requests
   - Generate task graphs
   - Execute with proper sequencing
   - Retry failed subtasks

4. **Add Reflection Layer**
   - Validate citations
   - Detect hallucinations post-hoc
   - Improve clarity
   - Second-pass refinement

5. **Build Approval Framework**
   - Central approval registry
   - Pluggable approval policies
   - Audit trail
   - Async approval support

---

## REFACTORING REQUIRED

### What Will NOT Change
- Tool base class architecture ✓
- Tool manager pattern ✓
- Existing tools (project_lookup, risk_lookup, etc.) ✓
- LLMClient abstraction ✓
- Embedding/RAG pipeline ✓
- Memory service ✓
- Database models ✓

### What MUST Change

#### 1. ProjectAgent Refactor
**Current**: Lines 51-249, does everything
**After**: Pure FinanceAgent, ProjectAgent, RiskAgent, etc. (focused agents)
- Remove tool selection logic (move to Supervisor)
- Remove orchestration (move to Supervisor)
- Keep: LLM generation, formatting, confidence scoring
- Each agent has: own prompts, own tool set, own validation

#### 2. New Supervisor Agent
**Current**: Doesn't exist
**After**: Single orchestration entry point
- Understands user intent
- Routes to agents
- Executes in parallel
- Merges results
- NEVER contains domain logic

#### 3. Tool Registration
**Current**: Hardcoded in agent.__init__
**After**: Registry pattern with agent-level subscriptions
```python
tool_registry.subscribe("ProjectAgent", ["project_lookup", "schedule_lookup"])
tool_registry.subscribe("FinanceAgent", ["budget_lookup", "cost_variance"])
```

---

## BACKWARD COMPATIBILITY

✓ **HTTP API unchanged**: POST /chat still works
✓ **Response format unchanged**: ChatResponse shape preserved
✓ **Tool interface unchanged**: Tools still implement execute()
✓ **Database unchanged**: All models preserved
✓ **Config unchanged**: Existing .env still works

**Only internal refactoring** - no breaking changes to clients.

---

## IMPLEMENTATION SEQUENCE

1. **Phase A** ✓ DONE: Review & Analysis
2. **Phase B**: Build Supervisor + Specialist Agents
3. **Phase C**: Implement Planner & Executor
4. **Phase D**: Add Reflection Agent
5. **Phase E**: Approval Framework

---

## METRICS FOR SUCCESS

- [ ] Supervisor orchestrates 5+ agents without modification
- [ ] Complex query decomposed into parallel tasks
- [ ] Reflection layer reduces hallucination rate
- [ ] Approval workflow prevents dangerous actions
- [ ] Zero breaking changes to HTTP API
- [ ] All existing tools still work
- [ ] New agents added in <1 hour
- [ ] Response latency < 3s for simple queries
- [ ] Full audit trail logged

---

## NEXT STEPS

**Phase B kickoff**: Design Supervisor Agent, specialist agents, and unified response interface.
