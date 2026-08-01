# StratOS AI Platform - Quick Reference Guide

## For Developers

---

## 🚀 QUICK START

### Run the Application
```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Frontend (in another terminal)
cd frontend
npm run dev

# Open browser to http://localhost:5173
```

### Test Chat Endpoint
```bash
# Simple query (Supervisor)
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the status of Project Alpha?",
    "project_id": 1,
    "response_mode": "concise"
  }'

# List available agents
curl http://localhost:8000/chat/agents

# Health check
curl http://localhost:8000/chat/health
```

---

## 📊 ARCHITECTURE LAYERS

```
┌─────────────────────────────────────────────────┐
│         HTTP API (Backward Compatible)          │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Orchestration (Supervisor or Planner+Executor) │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Agents (Project, Risk, Schedule, Document)    │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│           Tools (Lookup, Search, etc)           │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  Data Layer (Database, APIs, Documents)         │
└─────────────────────────────────────────────────┘
```

---

## 🤖 ADDING A NEW AGENT

### Step 1: Create Agent Class
```python
# app/agents/my_agent.py
from app.agents.base_agent import Agent, AgentResponse

class MySpecialistAgent(Agent):
    DOMAIN = "my_domain"
    DESCRIPTION = "What this agent does"
    VERSION = "1.0"
    
    def _register_tools(self) -> None:
        """Register tools this agent uses"""
        self.tool_manager.register(MyTool())
    
    def get_system_prompt(self) -> str:
        """Domain-specific system prompt"""
        return """You are a specialist in my domain.
        
        Your expertise:
        - Thing 1
        - Thing 2
        
        Guidelines:
        - Always cite sources
        - Be concise
        """
    
    async def answer(self, query: str, project_id: Optional[int], 
                     context_data: Optional[dict]) -> AgentResponse:
        """Answer a question"""
        start_time = time.time()
        
        # Determine tools
        tool_calls = await self._determine_tools(query, project_id)
        
        # Execute tools
        tool_results = await self._execute_tools(tool_calls)
        
        # Build context
        context = self._build_context(tool_results)
        
        # LLM call
        llm_response = await self.llm_client.generate(
            messages=[{
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}"
            }],
            system_prompt=self.get_system_prompt()
        )
        
        # Extract citations
        citations = self._extract_citations(tool_results, llm_response)
        
        # Apply guardrails
        confidence = 0.85  # Calculate properly
        
        # Return response
        return await self.create_response(
            answer=llm_response,
            citations=citations,
            confidence=confidence,
            tool_calls=[t["tool"] for t in tool_calls],
            context_length=len(context),
            execution_time_ms=(time.time() - start_time) * 1000
        )
    
    async def _determine_tools(self, query: str, project_id: Optional[int]):
        """Determine which tools to use"""
        tool_calls = []
        
        if any(word in query.lower() for word in ["my_keywords"]):
            tool_calls.append({
                "tool": "my_tool",
                "params": {"project_id": project_id}
            })
        
        return tool_calls
    
    def _build_context(self, tool_results: Dict) -> str:
        """Build context from tool results"""
        parts = []
        for tool_name, result in tool_results.items():
            if result.success and result.data:
                parts.append(f"From {tool_name}:\n{result.data}")
        return "\n\n".join(parts)
```

### Step 2: Register with Supervisor
```python
# In chat router or initialization
from app.agents.my_agent import MySpecialistAgent

supervisor = get_supervisor()
supervisor.register_agent("my_domain", MySpecialistAgent())
```

### Step 3: Test
```bash
# Agent should appear in list
curl http://localhost:8000/chat/agents

# Supervisor should route to it
curl -X POST http://localhost:8000/chat \
  -d '{"query": "Query that triggers my domain"}'
```

---

## 🔧 ADDING A NEW TOOL

### Step 1: Create Tool
```python
# app/tools/my_tool.py
from app.tools.base import Tool, ToolResult

class MyTool(Tool):
    name = "my_tool"
    description = "What this tool does"
    
    async def execute(self, project_id: int, **kwargs) -> ToolResult:
        """Execute the tool"""
        try:
            # Do work
            data = await self._query_database(project_id)
            
            return ToolResult(
                success=True,
                data=data,
                metadata={"query_count": 1}
            )
        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
    
    async def _query_database(self, project_id: int):
        """Query database for data"""
        # Implementation
        pass
```

### Step 2: Register in Agent
```python
class MyAgent(Agent):
    def _register_tools(self):
        self.tool_manager.register(MyTool())
```

### Step 3: Use in Agent
```python
async def _determine_tools(self, query, project_id):
    return [{
        "tool": "my_tool",
        "params": {"project_id": project_id}
    }]
```

---

## 📝 UNDERSTANDING THE RESPONSE

```python
{
    # Core answer
    "answer": "The response text here",
    
    # Quality metric (0.0-1.0, higher = more confident)
    "confidence": 0.92,
    
    # Sources
    "citations": [
        {
            "source": "project_lookup",
            "content": "Project details...",
            "relevance": 0.95,
            "tool": "project_lookup"
        }
    ],
    
    # Which agents contributed
    "agents_used": ["project_management", "risk_management"],
    
    # Additional details
    "metadata": {
        "elapsed_ms": 1234,
        "hallucination_risk": 0.05,
        "grounding_ok": True,
        "tool_count": 2
    }
}
```

**Confidence Score**:
- 0.0-0.3 = Low confidence (may have errors)
- 0.3-0.6 = Medium confidence (probably OK)
- 0.6-0.9 = High confidence (well grounded)
- 0.9-1.0 = Very high confidence (strong evidence)

---

## 🗂️ FILE LOCATIONS

### Agents
```
app/agents/
  base_agent.py           # Base class for all agents
  supervisor_agent.py     # Orchestrator
  project_agent.py        # Project management domain
  risk_agent.py           # Risk management domain
  schedule_agent.py       # Schedule domain
  document_agent.py       # Document/RAG domain
  finance_agent.py        # Finance domain (placeholder)
```

### Orchestration
```
app/orchestration/
  task_planner.py         # Decompose requests into tasks
  task_executor.py        # Execute task plans
```

### Tools
```
app/tools/
  base.py                 # Tool base class
  manager.py              # Tool orchestration
  project_lookup_tool.py  # Existing tools
  risk_lookup_tool.py
  schedule_lookup_tool.py
  semantic_search_tool.py
```

### HTTP API
```
app/routers/
  chat.py                 # Chat endpoint (updated)
  documents.py            # Document endpoints (existing)
  search.py               # Search endpoints (existing)
```

---

## 🧪 TESTING

### Test an Agent
```python
import pytest
from app.agents.project_agent import ProjectAgent

@pytest.mark.asyncio
async def test_project_agent_answer():
    agent = ProjectAgent()
    
    response = await agent.answer(
        query="What is the status of Project Alpha?",
        project_id=1
    )
    
    assert response.answer
    assert 0.0 <= response.confidence <= 1.0
    assert len(response.citations) > 0
    assert response.agent_name == "ProjectAgent"
```

### Test Supervisor
```python
@pytest.mark.asyncio
async def test_supervisor_orchestration():
    supervisor = SupervisorAgent()
    supervisor.register_agent("project_management", ProjectAgent())
    
    response = await supervisor.answer(
        query="What is the status?",
        project_id=1
    )
    
    assert response["answer"]
    assert "project_management" in response["agents_used"]
```

### Test Planner
```python
@pytest.mark.asyncio
async def test_planner():
    planner = TaskPlanner()
    
    plan = await planner.plan("Prepare executive review for Project Alpha")
    
    assert len(plan.tasks) > 0
    assert plan.is_valid
    assert plan.tasks[-1].type == TaskType.GENERATE_EXECUTIVE_SUMMARY
```

---

## 🔍 DEBUGGING

### Enable Verbose Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Or just for agents
logging.getLogger("app.agents").setLevel(logging.DEBUG)
logging.getLogger("app.orchestration").setLevel(logging.DEBUG)
```

### Trace a Request
```bash
# Watch logs while making request
tail -f /path/to/logs/app.log | grep -i "supervisor\|agent\|executor"

# Or enable debug mode
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

### Inspect Task Plan
```python
# Get the plan without executing
plan = await planner.plan(request)
print(planner.debug_plan(plan))

# Output:
# Execution Plan: 7 tasks
# Reasoning: Generated 7 tasks for executive_review request
# → Retrieve project details
# → Retrieve risks (depends on: [])
# → Retrieve budget (depends on: [])
# → Retrieve schedule (depends on: [])
# → Search documents (depends on: [])
# → Summarize (depends on: [task_0, task_1, task_2, task_3, task_4])
# → Generate executive summary (depends on: [task_5])
```

---

## 📈 PERFORMANCE TUNING

### Latency
- Simple query: 1-2 seconds
- Complex query: 2-3 seconds (parallel execution helps)
- Bottleneck: LLM API calls (OpenAI latency ~1s per call)

### Ways to Improve
1. Cache frequent queries
2. Cache semantic search results
3. Batch LLM calls (when possible)
4. Use faster LLM (GPT-4 mini vs GPT-4)

### Monitoring
```bash
# Check response time
curl -w "\nTotal: %{time_total}s\n" http://localhost:8000/chat ...

# Monitor per-component times
# Check logs for execution_time_ms in each TaskResult
```

---

## 🚨 COMMON ISSUES

### Issue: Agent not selected
**Symptom**: Query doesn't route to expected agent

**Fix**: Check keyword matching in `_select_agents()`
```python
# In supervisor_agent.py
if any(word in query_lower for word in ["keyword1", "keyword2"]):
    selected.append("domain_name")
```

### Issue: Tool returns no results
**Symptom**: Tool executes but returns empty data

**Fix**: Check tool implementation
```python
# Tool should return ToolResult(success=True, data=...)
# even if data is empty
```

### Issue: LLM response is generic
**Symptom**: Answer doesn't use provided context

**Fix**: Check system prompt and context quality
```python
# Verify system prompt is in agent.get_system_prompt()
# Verify context is non-empty in _build_context()
```

---

## 📚 DOCUMENTATION HIERARCHY

1. **QUICK_REFERENCE.md** (this file) - Quick lookups
2. **PLATFORM_ARCHITECTURE.md** - Complete system design
3. **PHASE_B_IMPLEMENTATION.md** - Agent orchestration details
4. **PHASE_C_IMPLEMENTATION.md** - Planning & execution details
5. **ARCHITECTURAL_DECISIONS.md** - Why decisions were made
6. **Code comments** - Implementation-level details

---

## 🎯 NEXT STEPS

### For New Feature
1. Check if existing agent covers it
2. If not, create new agent (see "Adding a New Agent" above)
3. Add tests
4. Update documentation

### For Bug Fix
1. Reproduce with test
2. Fix code
3. Verify test passes
4. Check logs for side effects

### For Optimization
1. Identify bottleneck (logging shows execution_time_ms)
2. Profile the code
3. Implement fix
4. Benchmark before/after

---

## 📞 SUPPORT

### Stuck?
- Check ARCHITECTURAL_DECISIONS.md for design rationale
- Review existing agents (project_agent.py is a good template)
- Enable DEBUG logging
- Check tool results in logs

### Want to Contribute?
1. Create feature branch
2. Add tests
3. Update documentation
4. Submit PR with clear description

---

## ✅ CHECKLIST: ADDING A NEW AGENT

- [ ] Create agent class inheriting from Agent
- [ ] Define DOMAIN, DESCRIPTION, VERSION
- [ ] Implement _register_tools()
- [ ] Implement get_system_prompt()
- [ ] Implement answer()
- [ ] Implement _determine_tools()
- [ ] Register with Supervisor
- [ ] Test with curl
- [ ] Write unit tests
- [ ] Update documentation
- [ ] Add to QUICK_REFERENCE.md

---

**Version**: 1.0  
**Last Updated**: Phase C Complete  
**Maintainer**: Architecture Team
