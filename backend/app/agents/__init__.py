"""Agents module - Specialist AI agents for Enterprise AI Platform.

Structure:
- base_agent.py: Base class all agents inherit from
- supervisor_agent.py: Orchestrates specialist agents
- agent_registry.py: Dynamic agent registration and discovery
- reflection_agent.py: Post-generation quality review (Phase D)
- project_agent.py: Project management domain
- finance_agent.py: Financial domain
- risk_agent.py: Risk management domain
- schedule_agent.py: Schedule and timeline domain
- document_agent.py: Document management and RAG domain

Usage:
    from app.agents import SupervisorAgent, ProjectAgent, get_agent_registry

    # Use agent registry for dynamic agent management
    registry = get_agent_registry()
    supervisor = SupervisorAgent()

    for domain in registry.get_enabled_domains():
        agent = registry.get(domain)
        supervisor.register_agent(domain, agent)

    response = await supervisor.answer("What's the status of Project Alpha?")
"""

from app.agents.base_agent import Agent, AgentResponse, Citation
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.reflection_agent import ReflectionAgent
from app.agents.agent_registry import AgentRegistry, get_agent_registry, init_default_agents
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
    "ReflectionAgent",
    "AgentRegistry",
    "get_agent_registry",
    "init_default_agents",
    "ProjectAgent",
    "FinanceAgent",
    "RiskAgent",
    "ScheduleAgent",
    "DocumentAgent",
]
