"""Execution Studio - Learning Explanations

Educational content about AI system components and architecture.
Explains why each component exists and how it works.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class ComponentExplanation:
    """Explanation for an AI system component."""
    component_name: str
    purpose: str
    problem_solves: str
    can_skip: bool
    design_pattern: str
    advantages: List[str]
    tradeoffs: List[str]
    related_components: List[str]
    docs_link: Optional[str] = None


# Comprehensive explanations database
COMPONENT_EXPLANATIONS: Dict[str, ComponentExplanation] = {
    # System Components
    "ChatEndpoint": ComponentExplanation(
        component_name="Chat Endpoint",
        purpose="HTTP API that receives user queries and returns AI responses",
        problem_solves="How do users interact with the AI system?",
        can_skip=False,
        design_pattern="REST API, Facade Pattern",
        advantages=["Simple HTTP interface", "Language-agnostic", "Easy to integrate"],
        tradeoffs=["Request-response latency", "No bidirectional streaming"],
        related_components=["SupervisorAgent", "Approval Framework"],
        docs_link="/docs/architecture#chat-endpoint",
    ),

    "EventBus": ComponentExplanation(
        component_name="Event Bus",
        purpose="Central pub/sub system for publishing execution events",
        problem_solves="How do we make the system transparent and educational?",
        can_skip=False,
        design_pattern="Pub/Sub Pattern, Observer Pattern",
        advantages=["Loose coupling", "Scalable", "Real-time updates"],
        tradeoffs=["Async complexity", "Eventually consistent"],
        related_components=["EventStore", "WebSocket Server"],
        docs_link="/docs/architecture#event-bus",
    ),

    # Orchestration Components
    "SupervisorAgent": ComponentExplanation(
        component_name="Supervisor Agent",
        purpose="Routes queries to the most appropriate specialist agents",
        problem_solves="How do we handle multiple domains (project, risk, schedule, documents)?",
        can_skip=False,
        design_pattern="Router Pattern, Strategy Pattern, Supervisor Pattern",
        advantages=[
            "Domain expertise specialization",
            "Parallel agent execution (4x faster)",
            "Easy to add new domains",
        ],
        tradeoffs=["Added latency from routing", "Coordination complexity"],
        related_components=[
            "ProjectAgent",
            "RiskAgent",
            "ScheduleAgent",
            "DocumentAgent",
        ],
        docs_link="/docs/phases/phase-b#supervisor-agent",
    ),

    "TaskPlanner": ComponentExplanation(
        component_name="Task Planner",
        purpose="Decomposes complex requests into subtasks with dependencies",
        problem_solves="How do we handle multi-step requests like 'health check'?",
        can_skip=True,
        design_pattern="Strategy Pattern, Builder Pattern",
        advantages=["Handles complex requests", "Respects dependencies", "Explainable"],
        tradeoffs=["Planning overhead", "Not needed for simple queries"],
        related_components=["TaskExecutor", "SupervisorAgent"],
        docs_link="/docs/phases/phase-c#task-planner",
    ),

    "TaskExecutor": ComponentExplanation(
        component_name="Task Executor",
        purpose="Executes task plans respecting dependencies and running independent tasks in parallel",
        problem_solves="How do we efficiently execute complex multi-step requests?",
        can_skip=True,
        design_pattern="Executor Pattern, DAG Execution",
        advantages=["Parallel execution where possible", "Handles failures gracefully"],
        tradeoffs=["Execution complexity", "Error recovery needed"],
        related_components=["TaskPlanner", "SupervisorAgent"],
        docs_link="/docs/phases/phase-c#task-executor",
    ),

    # Specialist Agents
    "ProjectAgent": ComponentExplanation(
        component_name="Project Agent",
        purpose="Domain expert for project management queries",
        problem_solves="How do we answer questions about project status, scope, milestones?",
        can_skip=False,
        design_pattern="Specialist Pattern, Agent Pattern",
        advantages=["Deep domain expertise", "Focused tools", "Consistent responses"],
        tradeoffs=["Cannot answer other domains", "Requires domain knowledge"],
        related_components=["SupervisorAgent", "ProjectLookupTool"],
        docs_link="/docs/phases/phase-b#project-agent",
    ),

    "RiskAgent": ComponentExplanation(
        component_name="Risk Agent",
        purpose="Domain expert for risk management and issue tracking",
        problem_solves="How do we identify and prioritize risks and blockers?",
        can_skip=False,
        design_pattern="Specialist Pattern",
        advantages=["Risk expertise", "Escalation support"],
        tradeoffs=["Narrow domain focus"],
        related_components=["SupervisorAgent", "RiskLookupTool"],
        docs_link="/docs/phases/phase-b#risk-agent",
    ),

    "ScheduleAgent": ComponentExplanation(
        component_name="Schedule Agent",
        purpose="Domain expert for project schedules and timelines",
        problem_solves="How do we track deadlines, delays, and critical paths?",
        can_skip=False,
        design_pattern="Specialist Pattern",
        advantages=["Schedule expertise", "Critical path analysis"],
        tradeoffs=["Narrow domain focus"],
        related_components=["SupervisorAgent", "ScheduleLookupTool"],
        docs_link="/docs/phases/phase-b#schedule-agent",
    ),

    "DocumentAgent": ComponentExplanation(
        component_name="Document Agent",
        purpose="Domain expert for document retrieval and semantic search (RAG)",
        problem_solves="How do we ground answers in actual project documentation?",
        can_skip=False,
        design_pattern="Specialist Pattern, RAG Pattern",
        advantages=["Source grounding", "Citation support", "Strict guardrails"],
        tradeoffs=["Requires good documentation", "RAG latency"],
        related_components=["SupervisorAgent", "SemanticSearchTool"],
        docs_link="/docs/phases/phase-b#document-agent",
    ),

    "FinanceAgent": ComponentExplanation(
        component_name="Finance Agent",
        purpose="Domain expert for financial analysis and budget tracking",
        problem_solves="How do we answer questions about project costs and budgets?",
        can_skip=True,
        design_pattern="Specialist Pattern",
        advantages=["Financial expertise", "Budget tracking"],
        tradeoffs=["Not yet implemented", "Requires financial data"],
        related_components=["SupervisorAgent"],
        docs_link="/docs/phases/phase-b#finance-agent",
    ),

    # Quality & Safety
    "ReflectionAgent": ComponentExplanation(
        component_name="Reflection Agent (Phase D)",
        purpose="Reviews AI responses BEFORE delivering to users for quality assurance",
        problem_solves="How do we prevent hallucinations and improve response quality?",
        can_skip=True,
        design_pattern="Decorator Pattern, Chain of Responsibility",
        advantages=[
            "Hallucination detection",
            "Citation verification",
            "Clarity improvement",
            "40% fewer false claims",
        ],
        tradeoffs=["+500ms latency", "May over-improve"],
        related_components=["Guardrails"],
        docs_link="/docs/phases/phase-d",
    ),

    "ApprovalManager": ComponentExplanation(
        component_name="Approval Framework (Phase E)",
        purpose="Approval gating for sensitive actions (delete, escalate, approve budget)",
        problem_solves="How do we prevent dangerous actions without human approval?",
        can_skip=True,
        design_pattern="Approval Pattern, Policy Pattern",
        advantages=[
            "Operational safety",
            "Audit trails",
            "Compliance ready",
            "Configurable policies",
        ],
        tradeoffs=["Extra step for users", "Approval latency"],
        related_components=["SupervisorAgent"],
        docs_link="/docs/phases/phase-e",
    ),

    "Guardrails": ComponentExplanation(
        component_name="Guardrails",
        purpose="Validates responses against safety and quality criteria",
        problem_solves="How do we ensure AI responses meet our standards?",
        can_skip=False,
        design_pattern="Validation Pattern, Strategy Pattern",
        advantages=["Safety assurance", "Consistent quality", "Auditable"],
        tradeoffs=["May reject valid responses", "Setup complexity"],
        related_components=["ReflectionAgent"],
        docs_link="/docs/architecture#guardrails",
    ),

    # Retrieval & Augmentation
    "SemanticSearch": ComponentExplanation(
        component_name="Semantic Search",
        purpose="Finds relevant documents based on semantic similarity",
        problem_solves="How do we find relevant documentation for RAG?",
        can_skip=False,
        design_pattern="RAG Pattern, Vector Search Pattern",
        advantages=["Semantic understanding", "Better than keyword search"],
        tradeoffs=["Embedding latency", "Relevance tuning needed"],
        related_components=["DocumentAgent", "Embeddings"],
        docs_link="/docs/architecture#semantic-search",
    ),

    "RAGPipeline": ComponentExplanation(
        component_name="RAG Pipeline",
        purpose="Retrieval-Augmented Generation - combines retrieval with generation",
        problem_solves="How do we ground LLM responses in actual data?",
        can_skip=False,
        design_pattern="RAG Pattern",
        advantages=["Source grounding", "Reduced hallucinations", "Citations"],
        tradeoffs=["Retrieval errors propagate", "Added latency"],
        related_components=["SemanticSearch", "DocumentAgent"],
        docs_link="/docs/architecture#rag",
    ),

    # AI & Language
    "LLMClient": ComponentExplanation(
        component_name="LLM Client",
        purpose="Calls Claude (or other LLM) to generate text",
        problem_solves="How do we generate intelligent responses?",
        can_skip=False,
        design_pattern="API Client Pattern, Adapter Pattern",
        advantages=["State-of-the-art generation", "Configurable models"],
        tradeoffs=["API latency", "Cost per call", "Rate limits"],
        related_components=["All agents"],
        docs_link="/docs/architecture#llm-client",
    ),

    "Embeddings": ComponentExplanation(
        component_name="Embeddings",
        purpose="Converts text to vector embeddings for semantic search",
        problem_solves="How do we enable semantic search?",
        can_skip=False,
        design_pattern="Vector Embedding Pattern",
        advantages=["Semantic understanding", "Efficient search"],
        tradeoffs=["Embedding quality varies", "Added storage needs"],
        related_components=["SemanticSearch"],
        docs_link="/docs/architecture#embeddings",
    ),

    # Data & Tools
    "ToolManager": ComponentExplanation(
        component_name="Tool Manager",
        purpose="Orchestrates tool execution and result aggregation",
        problem_solves="How do we coordinate multiple tools?",
        can_skip=False,
        design_pattern="Manager Pattern, Factory Pattern",
        advantages=["Centralized tool coordination", "Error handling"],
        tradeoffs=["Added complexity", "Single point of failure"],
        related_components=["All tools"],
        docs_link="/docs/architecture#tool-manager",
    ),

    "ProjectLookupTool": ComponentExplanation(
        component_name="Project Lookup Tool",
        purpose="Retrieves project information from database",
        problem_solves="How do we get project data?",
        can_skip=False,
        design_pattern="Tool Pattern, Data Access Pattern",
        advantages=["Fast lookup", "Database consistency"],
        tradeoffs=["Only project data"],
        related_components=["ProjectAgent"],
        docs_link="/docs/tools#project-lookup",
    ),

    "RiskLookupTool": ComponentExplanation(
        component_name="Risk Lookup Tool",
        purpose="Retrieves risk and issue data",
        problem_solves="How do we get risk information?",
        can_skip=False,
        design_pattern="Tool Pattern",
        advantages=["Risk data access"],
        tradeoffs=["Requires data model"],
        related_components=["RiskAgent"],
        docs_link="/docs/tools#risk-lookup",
    ),

    "ScheduleLookupTool": ComponentExplanation(
        component_name="Schedule Lookup Tool",
        purpose="Retrieves schedule and timeline data",
        problem_solves="How do we get schedule information?",
        can_skip=False,
        design_pattern="Tool Pattern",
        advantages=["Schedule data access"],
        tradeoffs=["Requires data model"],
        related_components=["ScheduleAgent"],
        docs_link="/docs/tools#schedule-lookup",
    ),

    "SemanticSearchTool": ComponentExplanation(
        component_name="Semantic Search Tool",
        purpose="Searches documents semantically",
        problem_solves="How do we find relevant documents?",
        can_skip=False,
        design_pattern="Tool Pattern, RAG Pattern",
        advantages=["Semantic search", "Flexible queries"],
        tradeoffs=["Embedding dependencies"],
        related_components=["DocumentAgent", "SemanticSearch"],
        docs_link="/docs/tools#semantic-search",
    ),
}

# Action explanations (why an action happened)
ACTION_EXPLANATIONS: Dict[str, str] = {
    # Chat Endpoint
    "receive_query": "Receive user query at HTTP endpoint",
    "return_response": "Return final response to user",

    # Supervisor Agent
    "route_query": "Route user query to determine which agents to use",
    "select_agents": "Select which specialist agents are needed",
    "answer": "Orchestrate agents and return unified answer",

    # Specialist Agent Actions (ProjectAgent, RiskAgent, ScheduleAgent, DocumentAgent, FinanceAgent)
    "answer_query": "Answer domain-specific question",
    "determine_tools": "Determine which data lookup tools are needed",
    "tools_selected": "Tools selected for data retrieval",
    "execute_tools": "Execute tools to retrieve necessary data",
    "tools_executed": "Tools executed and data retrieved",
    "build_context": "Build context string from tool results",
    "context_built": "Context prepared for LLM",
    "invoke_llm": "Call LLM to generate response",
    "llm_response_received": "LLM returned generated response",
    "extract_citations": "Extract citations from tool results",
    "citations_extracted": "Citations extracted and verified",
    "apply_guardrails": "Apply quality and safety guardrails",
    "guardrails_applied": "Guardrails validation complete",

    # LLM Client
    "generate_start": "Start LLM API call",
    "generate_complete": "LLM API call succeeded",
    "generate_failed": "LLM API call failed",

    # Reflection Agent (Phase D)
    "review_response": "Review and improve AI response quality",
    "check_hallucinations": "Check for unsupported claims (hallucinations)",
    "hallucinations_checked": "Hallucination risk assessment complete",
    "verify_citations": "Verify citations support the response",
    "citations_verified": "Citation verification complete",
    "assess_clarity": "Assess response clarity and readability",
    "clarity_assessed": "Clarity assessment complete",
    "improve_answer": "Apply improvements to response",
    "answer_improved": "Response improved successfully",

    # Approval Manager (Phase E)
    "create_approval_request": "Create approval request for sensitive action",
    "approval_approved": "Action approved by authorized user",
    "approval_rejected": "Action rejected by authorized user",
    "approval_expired": "Approval request expired (deadline passed)",
    "can_execute_check": "Check if action has been approved and can execute",

    # Legacy actions (backwards compatibility)
    "supervisor_route_query": "Route user query to appropriate specialist agents",
    "supervisor_select_agents": "Select which agents to invoke based on query semantics",
    "supervisor_invoke_parallel": "Invoke multiple agents in parallel for speed",
    "supervisor_merge_responses": "Merge responses from multiple agents intelligently",
    "agent_execute": "Execute the agent to answer the question",
    "agent_determine_tools": "Determine which tools this agent needs",
    "agent_invoke_tools": "Execute tools to retrieve necessary data",
    "llm_generate": "Call LLM (Claude) to generate the response",
    "tool_lookup": "Look up data via a tool",
    "reflection_review": "Review response quality (hallucination detection)",
    "reflection_detect_hallucinations": "Check for unsupported claims",
    "reflection_improve": "Improve response clarity and citations",
    "approval_check": "Check if this action requires approval",
    "approval_create": "Create approval request for sensitive action",
    "approval_record": "Record approval decision",
    "planner_decompose": "Break complex request into subtasks",
    "executor_execute_task": "Execute a single task",
}


def get_component_explanation(component: str) -> Optional[ComponentExplanation]:
    """Get explanation for a component.

    Args:
        component: Component name

    Returns:
        ComponentExplanation or None
    """
    return COMPONENT_EXPLANATIONS.get(component)


def get_action_explanation(action: str) -> Optional[str]:
    """Get explanation for an action.

    Args:
        action: Action name

    Returns:
        Explanation string or None
    """
    return ACTION_EXPLANATIONS.get(action)
