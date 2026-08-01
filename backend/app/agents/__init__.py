"""Agents module - Specialist AI agents for Enterprise AI Platform.

Structure:
- base_agent.py: Base class all agents inherit from
- supervisor_agent.py: Orchestrates specialist agents
- project_agent.py: Project management domain
- finance_agent.py: Financial domain
- risk_agent.py: Risk management domain
- schedule_agent.py: Schedule and timeline domain
- document_agent.py: Document management and RAG domain

Usage:
    from app.agents import SupervisorAgent, ProjectAgent, FinanceAgent

    supervisor = SupervisorAgent()
    supervisor.register_agent("project_management", ProjectAgent())
    supervisor.register_agent("finance", FinanceAgent())

    response = await supervisor.answer("What's the status of Project Alpha?")
"""

from app.agents.base_agent import Agent, AgentResponse, Citation
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.project_agent import ProjectAgent
from app.agents.finance_agent import FinanceAgent
from app.agents.risk_agent import RiskAgent
from app.agents.schedule_agent import ScheduleAgent
from app.agents.document_agent import DocumentAgent

__all__ = [
    "Agent",
    "AgentResponse",
    "Citation",
    "SupervisorAgent",
    "ProjectAgent",
    "FinanceAgent",
    "RiskAgent",
    "ScheduleAgent",
    "DocumentAgent",
]
