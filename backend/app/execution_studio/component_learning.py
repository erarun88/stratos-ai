"""Component Learning System - Educational content about system components.

Provides explanations, patterns, tips, and best practices for each component.
Enables "Learn Mode" in Execution Studio.
"""

from dataclasses import dataclass
from typing import List, Dict

@dataclass
class ComponentLearning:
    """Educational metadata about a component."""
    component: str
    purpose: str
    description: str
    design_pattern: str
    workflow_steps: List[str]
    when_to_use: List[str]
    when_not_to_use: List[str]
    performance_tips: List[str]
    common_mistakes: List[str]
    related_components: List[str]


# Learning content for each component
COMPONENT_LEARNING: Dict[str, ComponentLearning] = {
    "ChatEndpoint": ComponentLearning(
        component="ChatEndpoint",
        purpose="Entry point for all user interactions with the AI system",
        description="The HTTP API gateway that receives user chat messages and returns AI responses. This is where every conversation starts.",
        design_pattern="Gateway Pattern",
        workflow_steps=[
            "Receive HTTP POST request with user query",
            "Extract query text and optional context (project_id, etc.)",
            "Pass to Supervisor for routing",
            "Wait for response from specialist agents",
            "Format response and return to client",
        ],
        when_to_use=[
            "You're building a web/mobile app that needs AI assistance",
            "You want a unified interface to the entire AI system",
        ],
        when_not_to_use=[
            "You need direct agent access (use agents directly instead)",
            "You're building non-chat applications (might want different endpoint)",
        ],
        performance_tips=[
            "Cache common questions to reduce latency",
            "Use request batching for multiple simultaneous queries",
            "Monitor response times - if >10s, investigate downstream bottlenecks",
        ],
        common_mistakes=[
            "Sending queries without project context (less accurate results)",
            "Not handling partial responses gracefully",
            "Ignoring timeout errors from slow agents",
        ],
        related_components=["SupervisorAgent", "LLMClient"],
    ),

    "SupervisorAgent": ComponentLearning(
        component="SupervisorAgent",
        purpose="Orchestrates specialist agents to answer complex multi-domain queries",
        description="Routes queries to the appropriate specialist agents based on intent. Coordinates parallel execution and merges results.",
        design_pattern="Orchestrator Pattern (like a conductor leading an orchestra)",
        workflow_steps=[
            "Analyze user query to extract intent",
            "Identify which domains are relevant (project, risk, finance, etc.)",
            "Score agent relevance (0-1 confidence)",
            "Select best agents based on relevance and dependencies",
            "Invoke agents in parallel (if independent)",
            "Merge results into coherent response",
        ],
        when_to_use=[
            "Query spans multiple domains (e.g., 'status AND risks AND budget')",
            "Need parallel execution of independent agents",
            "Want intelligent routing without hardcoding",
        ],
        when_not_to_use=[
            "Single-domain query (direct agent call is faster)",
            "Real-time streaming needed (orchestration adds latency)",
        ],
        performance_tips=[
            "Parallelization is the biggest win - independent agents run together",
            "Avoid invoking too many agents (3-4 is optimal, >5 is overkill)",
            "Cache agent scoring results for repeated query patterns",
        ],
        common_mistakes=[
            "Routing to all agents regardless of relevance (wastes tokens/time)",
            "Sequential agent invocation instead of parallel",
            "Not considering dependencies between agents",
        ],
        related_components=["ProjectAgent", "RiskAgent", "FinanceAgent", "ScheduleAgent"],
    ),

    "ProjectAgent": ComponentLearning(
        component="ProjectAgent",
        purpose="Domain expert for project management queries (status, budget, team, timeline)",
        description="Handles questions about project details, team capacity, budget allocation, and project status. Uses project database and semantic search.",
        design_pattern="Specialist Agent Pattern (expert in one domain)",
        workflow_steps=[
            "Parse project-related keywords from query",
            "Determine which data to retrieve (status, budget, team, timeline)",
            "Call ProjectLookupTool to fetch project data",
            "Build LLM context with formatted project data",
            "Call LLM to synthesize human-readable response",
            "Return answer with confidence score",
        ],
        when_to_use=[
            "Questions about 'project status', 'budget', 'team capacity'",
            "Need authoritative project information from database",
            "Want natural language explanation of project metrics",
        ],
        when_not_to_use=[
            "Risk analysis (use RiskAgent instead)",
            "Financial forecasting (use FinanceAgent instead)",
            "Schedule/timeline questions (use ScheduleAgent instead)",
        ],
        performance_tips=[
            "Use specific project IDs when available - speeds up lookup",
            "Batch related project questions together",
            "Results are database-backed, so highly reliable",
        ],
        common_mistakes=[
            "Asking about non-project topics (reduces accuracy)",
            "Ignoring database freshness (data updates on a schedule)",
            "Expecting real-time data (cached for performance)",
        ],
        related_components=["ProjectLookupTool", "LLMClient", "SupervisorAgent"],
    ),

    "RiskAgent": ComponentLearning(
        component="RiskAgent",
        purpose="Domain expert for project risk analysis (blockers, issues, escalations)",
        description="Identifies and analyzes project risks, blockers, and escalation items. Searches risk documents and recommends mitigations.",
        design_pattern="Specialist Agent Pattern",
        workflow_steps=[
            "Extract risk keywords from query (risk, blocker, issue, escalation)",
            "Search project documents for risk-related content",
            "Call RiskLookupTool to retrieve risk data",
            "Analyze severity and impact of identified risks",
            "Generate mitigation recommendations",
            "Return structured risk assessment",
        ],
        when_to_use=[
            "Questions about 'project risks', 'blockers', 'issues'",
            "Need risk prioritization and impact analysis",
            "Want mitigation strategies",
        ],
        when_not_to_use=[
            "Project status queries (use ProjectAgent)",
            "Financial risk analysis (use FinanceAgent)",
            "Schedule risks (use ScheduleAgent)",
        ],
        performance_tips=[
            "Risk data is semantic - provides contextual understanding",
            "Batch risk queries for efficiency",
            "Use specific risk types when asking (reduces false positives)",
        ],
        common_mistakes=[
            "Confusing risk severity with probability",
            "Ignoring mitigation recommendations",
            "Not escalating critical risks appropriately",
        ],
        related_components=["RiskLookupTool", "LLMClient", "SupervisorAgent"],
    ),

    "FinanceAgent": ComponentLearning(
        component="FinanceAgent",
        purpose="Domain expert for financial analysis (budget, spend, forecasts, ROI)",
        description="Analyzes project financials including budgets, spending, forecasts, and return on investment.",
        design_pattern="Specialist Agent Pattern",
        workflow_steps=[
            "Extract financial keywords from query",
            "Identify analysis type (budget vs spend vs forecast)",
            "Retrieve financial data from database",
            "Perform calculations (burn rate, runway, etc.)",
            "Generate forecast or projection if requested",
            "Return analysis with charts/numbers",
        ],
        when_to_use=[
            "Questions about 'budget', 'spending', 'cost'",
            "Need financial forecasts or ROI analysis",
            "Want spend vs budget comparison",
        ],
        when_not_to_use=[
            "Project status (use ProjectAgent)",
            "Risk analysis (use RiskAgent)",
            "Timeline questions (use ScheduleAgent)",
        ],
        performance_tips=[
            "Financial data requires precision - always verify calculations",
            "Use historical trends for better forecasts",
            "Cache frequently accessed budget data",
        ],
        common_mistakes=[
            "Ignoring tax implications in ROI calculations",
            "Forecasting too far in future (accuracy degrades)",
            "Not considering one-time vs recurring costs",
        ],
        related_components=["ProjectAgent", "LLMClient", "SupervisorAgent"],
    ),

    "ScheduleAgent": ComponentLearning(
        component="ScheduleAgent",
        purpose="Domain expert for project timelines and schedules",
        description="Handles timeline questions, milestone tracking, and schedule optimization.",
        design_pattern="Specialist Agent Pattern",
        workflow_steps=[
            "Parse schedule keywords (timeline, milestone, deadline)",
            "Retrieve project schedule from database",
            "Analyze critical path and dependencies",
            "Identify schedule risks or delays",
            "Suggest optimizations if requested",
        ],
        when_to_use=[
            "Questions about 'timeline', 'milestones', 'deadlines'",
            "Need schedule optimization",
            "Want critical path analysis",
        ],
        when_not_to_use=[
            "Budget questions (use FinanceAgent)",
            "Risk analysis (use RiskAgent)",
            "Project status (use ProjectAgent)",
        ],
        performance_tips=[
            "Critical path analysis is the highest-value output",
            "Dependencies matter more than duration",
            "Buffer planning is key to schedule reliability",
        ],
        common_mistakes=[
            "Ignoring task dependencies in timeline",
            "Not accounting for resource constraints",
            "Underestimating uncertainty in estimates",
        ],
        related_components=["ProjectAgent", "LLMClient", "SupervisorAgent"],
    ),

    "DocumentAgent": ComponentLearning(
        component="DocumentAgent",
        purpose="Domain expert for document retrieval and analysis",
        description="Finds and summarizes relevant documents using semantic search. Provides context from project documentation.",
        design_pattern="Specialist Agent Pattern + RAG (Retrieval-Augmented Generation)",
        workflow_steps=[
            "Extract key topics from user query",
            "Perform semantic search across project documents",
            "Rank results by relevance",
            "Retrieve top-N documents",
            "Summarize relevant sections",
            "Return with document citations",
        ],
        when_to_use=[
            "Need information from project documentation",
            "Want semantic search across documents",
            "Asking general project questions (docs often have answers)",
        ],
        when_not_to_use=[
            "Real-time data needed (documents are static)",
            "Sensitive data (documents may not be redacted)",
        ],
        performance_tips=[
            "Semantic search finds meaning, not just keywords",
            "Document freshness matters - old docs can mislead",
            "Combining with other agents amplifies value",
        ],
        common_mistakes=[
            "Trusting outdated documentation",
            "Not validating document info with other sources",
            "Ignoring document confidence scores",
        ],
        related_components=["SemanticSearchTool", "LLMClient", "SupervisorAgent"],
    ),

    "LLMClient": ComponentLearning(
        component="LLMClient",
        purpose="Generates natural language responses using OpenAI GPT models",
        description="Wrapper around OpenAI API. Handles prompt engineering, context management, and response formatting.",
        design_pattern="API Client Pattern",
        workflow_steps=[
            "Receive context and prompt from agent",
            "Add system prompt for role-playing",
            "Add user prompt with context",
            "Call OpenAI API (GPT-4 or GPT-3.5)",
            "Parse response and extract text",
            "Track token usage and cost",
        ],
        when_to_use=[
            "Need natural language generation",
            "Want to leverage LLM intelligence",
            "Formatting structured data into prose",
        ],
        when_not_to_use=[
            "Simple formatting (use string templates)",
            "Real-time responses needed (LLM adds 1-3s latency)",
        ],
        performance_tips=[
            "Reuse prompts to leverage caching",
            "Shorter context = faster responses",
            "Temperature tuning affects creativity vs accuracy",
        ],
        common_mistakes=[
            "Oversized context (increases latency and cost)",
            "Poor prompt engineering (ruins response quality)",
            "Not handling rate limits (API throttling)",
        ],
        related_components=["All Agents", "ChatEndpoint"],
    ),

    "ReflectionAgent": ComponentLearning(
        component="ReflectionAgent",
        purpose="Quality assurance - validates response grounding and detects hallucinations",
        description="Reviews generated responses for accuracy, factual grounding, and hallucinations. Part of quality control pipeline.",
        design_pattern="Quality Gate Pattern",
        workflow_steps=[
            "Receive LLM-generated response",
            "Check grounding (are claims supported by context?)",
            "Detect hallucinations (unsupported claims)",
            "Verify citation accuracy",
            "Return quality score and feedback",
            "Optionally improve response if needed",
        ],
        when_to_use=[
            "High-stakes responses where accuracy matters",
            "Need confidence scoring",
            "Want to reduce hallucinations",
        ],
        when_not_to_use=[
            "Speed is critical (adds 500ms-1s latency)",
            "Creative/speculative responses (reflection is strict)",
        ],
        performance_tips=[
            "Enables iterative improvement (re-prompt if poor score)",
            "Catches errors LLM missed",
            "Confidence scores are valuable for ranking results",
        ],
        common_mistakes=[
            "Ignoring low grounding scores",
            "Being too strict (some creativity is good)",
            "Not using feedback for improvement",
        ],
        related_components=["LLMClient", "SupervisorAgent"],
    ),

    "ApprovalManager": ComponentLearning(
        component="ApprovalManager",
        purpose="Approval gating for dangerous actions (delete, escalate, budget changes)",
        description="Detects when responses suggest dangerous actions and requires approval before execution.",
        design_pattern="Authorization Gate Pattern",
        workflow_steps=[
            "Analyze response for dangerous keywords",
            "Classify action type (delete, escalate, budget change)",
            "Check if action requires approval",
            "Create approval request if needed",
            "Wait for human approval",
            "Log decision for audit trail",
        ],
        when_to_use=[
            "Dangerous action detected in response",
            "Want audit trail of decisions",
            "Need human oversight for critical changes",
        ],
        when_not_to_use=[
            "Read-only queries (no approval needed)",
            "Low-stakes changes",
        ],
        performance_tips=[
            "Approval requests block execution (don't ignore them)",
            "Audit trail is valuable for compliance",
            "Clear descriptions help approvers decide quickly",
        ],
        common_mistakes=[
            "Approving without reviewing rationale",
            "Ignoring approval requests",
            "Deleting approval history (compliance risk)",
        ],
        related_components=["SupervisorAgent", "ReflectionAgent"],
    ),
}


def get_component_learning(component: str) -> ComponentLearning:
    """Get learning content for a component.

    Args:
        component: Component name

    Returns:
        ComponentLearning if found, else generic learning data
    """
    if component in COMPONENT_LEARNING:
        return COMPONENT_LEARNING[component]

    # Generic fallback
    return ComponentLearning(
        component=component,
        purpose="Custom component",
        description="This component is part of the AI system.",
        design_pattern="Unknown",
        workflow_steps=["No specific workflow documented"],
        when_to_use=["When needed"],
        when_not_to_use=["When not needed"],
        performance_tips=["Monitor performance metrics"],
        common_mistakes=["Misusing the component"],
        related_components=[],
    )


def get_all_learning() -> Dict[str, ComponentLearning]:
    """Get all component learning data."""
    return COMPONENT_LEARNING.copy()
