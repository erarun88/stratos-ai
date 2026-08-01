"""Agent Registry - Dynamic agent registration and discovery.

The Agent Registry allows agents to be registered, discovered, and managed
without hardcoding them in routers.

Usage:
    registry = AgentRegistry()

    # Register agents
    registry.register("project_management", ProjectAgent())
    registry.register("risk_management", RiskAgent())

    # Or load from config
    registry.load_from_config("agents_config.yaml")

    # List available agents
    agents = registry.list_agents()

    # Get specific agent
    agent = registry.get("project_management")

    # Check if agent enabled
    if registry.is_enabled("project_management"):
        ...
"""

import logging
from typing import Dict, Optional, List, Any
import json
import yaml

from app.agents.base_agent import Agent

logger = logging.getLogger(__name__)


class AgentRegistryConfig:
    """Configuration for agent registry."""

    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> "AgentRegistryConfig":
        """Load config from dictionary.

        Args:
            config_dict: Dict with 'agents' key containing agent configs

        Returns:
            AgentRegistryConfig instance
        """
        cfg = AgentRegistryConfig()
        cfg.agents = config_dict.get("agents", {})
        return cfg

    @staticmethod
    def from_json(json_path: str) -> "AgentRegistryConfig":
        """Load config from JSON file.

        Args:
            json_path: Path to JSON config file

        Returns:
            AgentRegistryConfig instance
        """
        with open(json_path) as f:
            data = json.load(f)
        return AgentRegistryConfig.from_dict(data)

    @staticmethod
    def from_yaml(yaml_path: str) -> "AgentRegistryConfig":
        """Load config from YAML file.

        Args:
            yaml_path: Path to YAML config file

        Returns:
            AgentRegistryConfig instance
        """
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return AgentRegistryConfig.from_dict(data)


class AgentRegistry:
    """Registry for specialist agents.

    Allows dynamic registration, discovery, and management of agents.
    Supports loading from config files (JSON/YAML).

    Example config.yaml:
        agents:
          project_management:
            class: ProjectAgent
            enabled: true
            description: "Project management and status"
          risk_management:
            class: RiskAgent
            enabled: true
            description: "Risk identification and mitigation"
    """

    def __init__(self):
        """Initialize empty agent registry."""
        self.agents: Dict[str, Agent] = {}
        self.metadata: Dict[str, Dict[str, Any]] = {}
        logger.info("AgentRegistry initialized")

    def register(
        self,
        domain: str,
        agent: Agent,
        enabled: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Register an agent.

        Args:
            domain: Domain name (e.g., "project_management")
            agent: Agent instance
            enabled: Whether agent is enabled (default True)
            metadata: Optional metadata (description, version, etc.)
        """
        self.agents[domain] = agent
        self.metadata[domain] = {
            "enabled": enabled,
            "agent_name": agent.__class__.__name__,
            "domain": domain,
            "description": agent.DESCRIPTION,
            "version": agent.VERSION,
            **(metadata or {}),
        }
        logger.info(f"Registered agent: {domain} ({agent.__class__.__name__})")

    def unregister(self, domain: str) -> bool:
        """Unregister an agent.

        Args:
            domain: Domain name

        Returns:
            True if agent was registered and removed
        """
        if domain in self.agents:
            del self.agents[domain]
            del self.metadata[domain]
            logger.info(f"Unregistered agent: {domain}")
            return True
        return False

    def get(self, domain: str) -> Optional[Agent]:
        """Get agent by domain.

        Args:
            domain: Domain name

        Returns:
            Agent instance or None if not found
        """
        return self.agents.get(domain)

    def is_enabled(self, domain: str) -> bool:
        """Check if agent is enabled.

        Args:
            domain: Domain name

        Returns:
            True if agent is registered and enabled
        """
        meta = self.metadata.get(domain, {})
        return meta.get("enabled", False)

    def enable(self, domain: str) -> bool:
        """Enable an agent.

        Args:
            domain: Domain name

        Returns:
            True if agent exists and was enabled
        """
        if domain in self.metadata:
            self.metadata[domain]["enabled"] = True
            logger.info(f"Enabled agent: {domain}")
            return True
        return False

    def disable(self, domain: str) -> bool:
        """Disable an agent.

        Args:
            domain: Domain name

        Returns:
            True if agent exists and was disabled
        """
        if domain in self.metadata:
            self.metadata[domain]["enabled"] = False
            logger.info(f"Disabled agent: {domain}")
            return True
        return False

    def list_agents(self, enabled_only: bool = False) -> Dict[str, str]:
        """List registered agents.

        Args:
            enabled_only: If True, only return enabled agents

        Returns:
            Dict mapping domain -> description
        """
        result = {}
        for domain, agent in self.agents.items():
            meta = self.metadata.get(domain, {})
            if enabled_only and not meta.get("enabled", False):
                continue
            result[domain] = agent.DESCRIPTION
        return result

    def list_metadata(self, enabled_only: bool = False) -> Dict[str, Dict[str, Any]]:
        """List agent metadata.

        Args:
            enabled_only: If True, only return metadata for enabled agents

        Returns:
            Dict mapping domain -> metadata
        """
        result = {}
        for domain, meta in self.metadata.items():
            if enabled_only and not meta.get("enabled", False):
                continue
            result[domain] = meta
        return result

    def get_enabled_domains(self) -> List[str]:
        """Get list of enabled agent domains.

        Returns:
            List of domain names for enabled agents
        """
        return [
            domain
            for domain, meta in self.metadata.items()
            if meta.get("enabled", False)
        ]

    def count(self, enabled_only: bool = False) -> int:
        """Count registered agents.

        Args:
            enabled_only: If True, only count enabled agents

        Returns:
            Number of agents
        """
        if enabled_only:
            return len(self.get_enabled_domains())
        return len(self.agents)

    def to_dict(self) -> Dict[str, Any]:
        """Convert registry to dictionary representation.

        Returns:
            Dict with agents and metadata
        """
        return {
            "agents": {
                domain: agent.__class__.__name__ for domain, agent in self.agents.items()
            },
            "metadata": self.metadata,
            "enabled_count": len(self.get_enabled_domains()),
            "total_count": len(self.agents),
        }


# Global singleton registry
_agent_registry: Optional[AgentRegistry] = None


def get_agent_registry() -> AgentRegistry:
    """Get or create global agent registry.

    Returns:
        Global AgentRegistry instance
    """
    global _agent_registry
    if _agent_registry is None:
        _agent_registry = AgentRegistry()
    return _agent_registry


def init_default_agents() -> AgentRegistry:
    """Initialize registry with default agents.

    This is called by the application on startup to populate the registry
    with the standard agent set.

    Returns:
        Initialized AgentRegistry
    """
    from app.agents import ProjectAgent, RiskAgent, ScheduleAgent, DocumentAgent

    registry = get_agent_registry()

    # Register default agents
    registry.register("project_management", ProjectAgent(), enabled=True)
    registry.register("risk_management", RiskAgent(), enabled=True)
    registry.register("schedule", ScheduleAgent(), enabled=True)
    registry.register("document_management", DocumentAgent(), enabled=True)

    logger.info(
        f"Initialized default agents: {len(registry.list_agents())} agents registered"
    )

    return registry
