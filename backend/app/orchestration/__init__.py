"""Orchestration module - Planner and Executor for complex requests.

Handles task decomposition and execution of multi-step plans.

Components:
- task_planner.py: Decomposes requests into task plans
- task_executor.py: Executes task plans
- coordinator.py: Ties planner and executor together

Usage:
    from app.orchestration import PlanningOrchestrator

    orchestrator = PlanningOrchestrator(supervisor)

    # For complex request that needs planning
    result = await orchestrator.handle("Prepare executive review for Project Alpha")
"""

from app.orchestration.task_planner import ExecutionPlan, Task, TaskPlanner, TaskType
from app.orchestration.task_executor import ExecutionResult, TaskExecutor, TaskResult, TaskStatus

__all__ = [
    "Task",
    "TaskType",
    "ExecutionPlan",
    "TaskPlanner",
    "TaskResult",
    "TaskStatus",
    "TaskExecutor",
    "ExecutionResult",
]
