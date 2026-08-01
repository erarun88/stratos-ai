"""Execution Studio - Event Model

Generic event model for tracing all AI system execution.
Every event contains self-describing data - no hardcoding needed in frontend.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import uuid


class EventStatus(str, Enum):
    """Status of an execution event."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class ExecutionEvent:
    """Generic event representing a step in AI system execution.

    Components publish these events. Frontend renders them generically.
    No component-specific logic needed.
    """

    # IDs for tracing
    request_id: str                     # Unique request ID (trace ID)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_event_id: Optional[str] = None  # For nesting/hierarchy

    # Timing
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0            # How long this step took

    # What happened
    component: str = ""                 # "SupervisorAgent", "ReflectionAgent", etc.
    action: str = ""                    # "route_query", "invoke_agent", etc.
    status: EventStatus = EventStatus.STARTED

    # Metrics
    tokens_used: int = 0                # LLM tokens consumed
    cost: float = 0.0                   # $ cost
    latency_ms: float = 0.0             # Network latency if applicable

    # Data
    metadata: Dict[str, Any] = field(default_factory=dict)  # Component-specific data
    error: Optional[str] = None         # Error message if failed

    # System
    created_at: datetime = field(default_factory=datetime.utcnow)
    indexed: bool = False               # Whether stored in event store

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization (e.g., JSON)."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["status"] = self.status.value
        data["event_id"] = str(self.event_id)
        data["request_id"] = str(self.request_id)
        return data

    def add_metadata(self, key: str, value: Any) -> "ExecutionEvent":
        """Add metadata (for builder pattern)."""
        self.metadata[key] = value
        return self

    def mark_completed(self, duration_ms: float = 0.0) -> "ExecutionEvent":
        """Mark event as completed."""
        self.status = EventStatus.COMPLETED
        if duration_ms > 0:
            self.duration_ms = duration_ms
        return self

    def mark_failed(self, error: str) -> "ExecutionEvent":
        """Mark event as failed."""
        self.status = EventStatus.FAILED
        self.error = error
        return self


@dataclass
class TraceMetrics:
    """Metrics for an entire execution trace."""
    request_id: str
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost: float = 0.0
    component_count: int = 0
    event_count: int = 0
    agent_count: int = 0
    tool_count: int = 0
    errors: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict."""
        return asdict(self)


# Event action types (for documentation/discovery)
EVENT_ACTIONS = {
    # Supervisor actions
    "supervisor_route_query": "Route user query to appropriate agents",
    "supervisor_select_agents": "Select which agents to invoke",
    "supervisor_invoke_parallel": "Invoke multiple agents in parallel",
    "supervisor_merge_responses": "Merge responses from multiple agents",

    # Agent actions
    "agent_execute": "Execute agent to answer question",
    "agent_determine_tools": "Determine which tools to use",
    "agent_invoke_tools": "Invoke tools to get data",
    "agent_extract_citations": "Extract citations from results",

    # LLM actions
    "llm_generate": "Call LLM to generate text",

    # Tool actions
    "tool_lookup": "Look up data via tool",
    "tool_search": "Search via tool",

    # Reflection actions
    "reflection_review": "Review response quality",
    "reflection_detect_hallucinations": "Detect unsupported claims",
    "reflection_verify_citations": "Verify citations support claims",
    "reflection_assess_clarity": "Assess response clarity",
    "reflection_improve": "Improve response text",

    # Approval actions
    "approval_check": "Check if approval required",
    "approval_create": "Create approval request",
    "approval_record": "Record approval decision",

    # Planning actions
    "planner_decompose": "Decompose request into tasks",
    "planner_order_tasks": "Order tasks by dependencies",

    # Execution actions
    "executor_execute_task": "Execute a single task",
    "executor_handle_dependency": "Handle task dependency",

    # Guardrail actions
    "guardrail_validate": "Validate response against guardrails",
}


# Event component types (for documentation/discovery)
KNOWN_COMPONENTS = {
    # System
    "ChatEndpoint": "HTTP Chat API endpoint",
    "EventBus": "Central event publishing system",

    # Orchestration
    "SupervisorAgent": "Routes queries to specialist agents",
    "TaskPlanner": "Decomposes complex requests",
    "TaskExecutor": "Executes tasks respecting dependencies",

    # Specialist agents
    "ProjectAgent": "Project management domain expert",
    "RiskAgent": "Risk management domain expert",
    "ScheduleAgent": "Schedule and timeline domain expert",
    "DocumentAgent": "Document management and RAG expert",
    "FinanceAgent": "Financial analysis domain expert",

    # Quality & Safety
    "ReflectionAgent": "Post-generation quality review",
    "ApprovalManager": "Approval workflow orchestration",
    "Guardrails": "Response validation and safety",

    # Retrieval & Augmentation
    "SemanticSearch": "Document semantic search",
    "RAGPipeline": "Retrieval-augmented generation",

    # AI & Language
    "LLMClient": "Language model API client",
    "Embeddings": "Text embedding generation",

    # Data & Tools
    "ProjectLookupTool": "Look up project information",
    "RiskLookupTool": "Look up risk information",
    "ScheduleLookupTool": "Look up schedule information",
    "SemanticSearchTool": "Search documents semantically",
    "ToolManager": "Central tool orchestration",

    # Future components (auto-integrated when added)
    "MemorySystem": "Long-term and short-term memory",
    "MCPServer": "Model Context Protocol integration",
    "EvaluationSystem": "Response quality evaluation",
    "HybridSearch": "Hybrid semantic + keyword search",
    "CacheLayer": "Response caching system",
}
