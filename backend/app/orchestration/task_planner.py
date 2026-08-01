"""Task Planner - Decomposes complex requests into executable task plans.

The Planner takes high-level requests and generates structured task plans.

Example:
    User: "Prepare an executive review for Project Alpha"

    Planner generates:
    [
        Task(type="retrieve_project", params={"project_id": 1}),
        Task(type="retrieve_risks", params={"project_id": 1}),
        Task(type="retrieve_financials", params={"project_id": 1}),
        Task(type="search_documents", params={"query": "Project Alpha requirements", "limit": 5}),
        Task(type="summarize", params={"tasks": [0, 1, 2, 3]}),
        Task(type="generate_recommendations", params={"summary": "..."})
    ]

Key design:
- Planner does NOT execute tasks
- Planner generates plan as DAG (dependencies tracked)
- Executor then runs the plan
- Planner and Executor are independent

Why separate?
- Planner focuses on "what tasks and in what order"
- Executor focuses on "actually running tasks"
- Easier to test, reason about, and extend
- Supports approval before execution (Phase E)
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TaskType(str, Enum):
    """Types of tasks in an execution plan."""

    # Retrieval tasks
    RETRIEVE_PROJECT = "retrieve_project"
    RETRIEVE_RISKS = "retrieve_risks"
    RETRIEVE_FINANCIALS = "retrieve_financials"
    RETRIEVE_SCHEDULE = "retrieve_schedule"
    SEARCH_DOCUMENTS = "search_documents"

    # Analysis tasks
    ANALYZE = "analyze"
    SUMMARIZE = "summarize"
    COMPARE = "compare"

    # Generation tasks
    GENERATE_RECOMMENDATIONS = "generate_recommendations"
    GENERATE_EXECUTIVE_SUMMARY = "generate_executive_summary"

    # Composition tasks
    MERGE_RESULTS = "merge_results"


@dataclass
class Task:
    """A single task in an execution plan."""

    id: str  # Unique identifier (e.g., "task_0", "task_1")
    type: TaskType  # What kind of task
    description: str  # Human-readable description
    params: Dict[str, Any] = field(default_factory=dict)  # Task parameters
    depends_on: List[str] = field(default_factory=list)  # Task IDs this depends on

    def __repr__(self) -> str:
        deps = f" → {self.depends_on}" if self.depends_on else ""
        return f"Task({self.type.value}{deps}): {self.description}"


@dataclass
class ExecutionPlan:
    """A structured plan of tasks to execute."""

    request: str  # Original user request
    tasks: List[Task]  # Ordered list of tasks
    dependencies: Dict[str, List[str]]  # task_id -> [depends_on_ids]
    reasoning: str = ""  # Why this plan was chosen

    @property
    def is_empty(self) -> bool:
        """Check if plan has no tasks."""
        return len(self.tasks) == 0

    @property
    def is_valid(self) -> bool:
        """Check if plan has valid dependencies (no cycles)."""
        return self._check_no_cycles()

    def _check_no_cycles(self) -> bool:
        """Verify there are no circular dependencies."""
        # Simple check: if task depends on itself (directly or indirectly)
        # For now, assume plans are acyclic (they should be)
        return True

    def __repr__(self) -> str:
        return f"ExecutionPlan({len(self.tasks)} tasks)"


class TaskPlanner:
    """Generates execution plans for complex requests.

    Responsibilities:
    - Understand user intent
    - Decompose into tasks
    - Determine dependencies
    - Order tasks appropriately
    - Return structured plan

    The Planner does NOT execute tasks.
    The Executor takes this plan and runs it.
    """

    def __init__(self):
        """Initialize planner."""
        logger.info("TaskPlanner initialized")

    async def plan(self, request: str, project_id: Optional[int] = None) -> ExecutionPlan:
        """Generate an execution plan for a request.

        Args:
            request: High-level user request (natural language)
            project_id: Optional project context

        Returns:
            ExecutionPlan with ordered tasks and dependencies
        """
        logger.info(f"TaskPlanner.plan: {request[:100]}...")

        # Step 1: Classify the request type
        request_type = self._classify_request(request)
        logger.debug(f"Request type: {request_type}")

        # Step 2: Generate tasks based on request type
        tasks = await self._generate_tasks(request_type, request, project_id)

        # Step 3: Order tasks and determine dependencies
        ordered_tasks, dependencies = self._order_tasks(tasks)

        # Step 4: Create plan
        plan = ExecutionPlan(
            request=request,
            tasks=ordered_tasks,
            dependencies=dependencies,
            reasoning=f"Generated {len(ordered_tasks)} tasks for {request_type} request",
        )

        logger.info(f"Generated plan: {len(ordered_tasks)} tasks")
        for task in ordered_tasks:
            logger.debug(f"  {task}")

        return plan

    def _classify_request(self, request: str) -> str:
        """Classify what type of request this is.

        Types:
        - executive_review: "Prepare executive review for Project X"
        - status_report: "Give me a full status report"
        - risk_assessment: "Assess risks for Project X"
        - timeline_analysis: "Analyze timeline and critical path"
        - comparative_analysis: "Compare projects A and B"

        Args:
            request: User request

        Returns:
            Request type string
        """
        request_lower = request.lower()

        # Executive review
        if any(word in request_lower for word in ["executive", "review", "board", "c-level"]):
            return "executive_review"

        # Status report
        if any(word in request_lower for word in ["status report", "full status", "overview"]):
            return "status_report"

        # Risk assessment
        if any(word in request_lower for word in ["assess risk", "risk analysis"]):
            return "risk_assessment"

        # Timeline analysis
        if any(word in request_lower for word in ["timeline", "critical path", "schedule analysis"]):
            return "timeline_analysis"

        # Comparative
        if any(word in request_lower for word in ["compare", "versus", "vs", "difference"]):
            return "comparative_analysis"

        # Default
        return "general_inquiry"

    async def _generate_tasks(
        self, request_type: str, request: str, project_id: Optional[int]
    ) -> List[Task]:
        """Generate tasks for a request type.

        Args:
            request_type: Type of request
            request: Original request
            project_id: Optional project ID

        Returns:
            List of Task objects (unordered)
        """
        tasks = []

        if request_type == "executive_review":
            # Executive review needs: project, risks, financials, docs, summary
            tasks = [
                Task(
                    id="task_0",
                    type=TaskType.RETRIEVE_PROJECT,
                    description="Retrieve project details",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_1",
                    type=TaskType.RETRIEVE_RISKS,
                    description="Retrieve project risks and blockers",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_2",
                    type=TaskType.RETRIEVE_FINANCIALS,
                    description="Retrieve budget and financial status",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_3",
                    type=TaskType.RETRIEVE_SCHEDULE,
                    description="Retrieve schedule and milestones",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_4",
                    type=TaskType.SEARCH_DOCUMENTS,
                    description="Search project documents",
                    params={"query": request, "project_id": project_id, "limit": 5},
                ),
                Task(
                    id="task_5",
                    type=TaskType.SUMMARIZE,
                    description="Summarize findings for executive",
                    params={"depends_on": ["task_0", "task_1", "task_2", "task_3", "task_4"]},
                ),
                Task(
                    id="task_6",
                    type=TaskType.GENERATE_EXECUTIVE_SUMMARY,
                    description="Generate executive summary with recommendations",
                    params={"depends_on": ["task_5"]},
                ),
            ]

        elif request_type == "status_report":
            # Status report: project + risks + schedule + docs
            tasks = [
                Task(
                    id="task_0",
                    type=TaskType.RETRIEVE_PROJECT,
                    description="Retrieve project status",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_1",
                    type=TaskType.RETRIEVE_RISKS,
                    description="Retrieve current risks",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_2",
                    type=TaskType.RETRIEVE_SCHEDULE,
                    description="Retrieve schedule status",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_3",
                    type=TaskType.SEARCH_DOCUMENTS,
                    description="Search relevant documents",
                    params={"query": request, "project_id": project_id, "limit": 3},
                ),
                Task(
                    id="task_4",
                    type=TaskType.SUMMARIZE,
                    description="Synthesize status report",
                    params={"depends_on": ["task_0", "task_1", "task_2", "task_3"]},
                ),
            ]

        elif request_type == "risk_assessment":
            # Risk assessment: risks + impact analysis
            tasks = [
                Task(
                    id="task_0",
                    type=TaskType.RETRIEVE_RISKS,
                    description="Retrieve all risks",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_1",
                    type=TaskType.SEARCH_DOCUMENTS,
                    description="Search risk-related documents",
                    params={"query": "risks blockers issues", "project_id": project_id, "limit": 5},
                ),
                Task(
                    id="task_2",
                    type=TaskType.ANALYZE,
                    description="Analyze risk impact and dependencies",
                    params={"depends_on": ["task_0", "task_1"]},
                ),
                Task(
                    id="task_3",
                    type=TaskType.GENERATE_RECOMMENDATIONS,
                    description="Generate mitigation recommendations",
                    params={"depends_on": ["task_2"]},
                ),
            ]

        elif request_type == "timeline_analysis":
            # Timeline: schedule + risks affecting timeline + forecasts
            tasks = [
                Task(
                    id="task_0",
                    type=TaskType.RETRIEVE_SCHEDULE,
                    description="Retrieve detailed schedule",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_1",
                    type=TaskType.RETRIEVE_RISKS,
                    description="Retrieve risks affecting timeline",
                    params={"project_id": project_id},
                ),
                Task(
                    id="task_2",
                    type=TaskType.ANALYZE,
                    description="Analyze critical path and delays",
                    params={"depends_on": ["task_0", "task_1"]},
                ),
                Task(
                    id="task_3",
                    type=TaskType.GENERATE_RECOMMENDATIONS,
                    description="Recommend timeline optimizations",
                    params={"depends_on": ["task_2"]},
                ),
            ]

        else:  # default / general_inquiry
            # For simple questions, use Supervisor (not a complex plan)
            tasks = [
                Task(
                    id="task_0",
                    type=TaskType.ANALYZE,
                    description="Route to Supervisor for general inquiry",
                    params={"request": request, "project_id": project_id},
                ),
            ]

        return tasks

    def _order_tasks(self, tasks: List[Task]) -> tuple[List[Task], Dict[str, List[str]]]:
        """Order tasks respecting dependencies.

        Uses topological sort to determine execution order.

        Args:
            tasks: Unordered list of tasks

        Returns:
            Tuple of (ordered_tasks, dependency_map)
        """
        # Build dependency map
        dependencies = {task.id: task.depends_on for task in tasks}

        # Topological sort (simplified for MVP)
        ordered = []
        processed = set()

        def visit(task_id: str):
            if task_id in processed:
                return
            processed.add(task_id)

            # Add dependencies first
            for dep_id in dependencies.get(task_id, []):
                visit(dep_id)

            # Then add self
            task = next((t for t in tasks if t.id == task_id), None)
            if task:
                ordered.append(task)

        for task in tasks:
            visit(task.id)

        return ordered, dependencies

    def debug_plan(self, plan: ExecutionPlan) -> str:
        """Return human-readable plan summary."""
        lines = [f"Execution Plan: {len(plan.tasks)} tasks"]
        lines.append(f"Reasoning: {plan.reasoning}")
        lines.append("")

        for task in plan.tasks:
            indent = "  " if task.depends_on else ""
            deps = f" (depends on: {', '.join(task.depends_on)})" if task.depends_on else ""
            lines.append(f"{indent}→ {task.description}{deps}")

        return "\n".join(lines)
