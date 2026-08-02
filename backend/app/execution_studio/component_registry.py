"""Component Registry - Metadata for all system components.

Provides self-describing metadata for visualization and learning.
No hardcoding needed - components are self-documenting.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class ComponentMetadata:
    """Metadata about a component for visualization and learning."""
    component: str
    display_name: str
    component_type: str  # "orchestrator", "agent", "tool", "inference", etc.
    icon: str  # emoji
    description: str  # One-line explanation
    color: str  # For visualization
    layer: int  # UI layer (0=entry, 1=routing, 2=execution, 3=quality)
    position: tuple  # (x, y) for diagram layout


# Component Registry - Add all components here
COMPONENT_REGISTRY: Dict[str, ComponentMetadata] = {
    # Entry Points
    "ChatEndpoint": ComponentMetadata(
        component="ChatEndpoint",
        display_name="Chat API",
        component_type="orchestrator",
        icon="💬",
        description="HTTP API endpoint for chat requests",
        color="purple",
        layer=0,
        position=(50, 5),
    ),

    # Orchestration
    "SupervisorAgent": ComponentMetadata(
        component="SupervisorAgent",
        display_name="Supervisor",
        component_type="orchestrator",
        icon="🎯",
        description="Routes queries to specialist agents",
        color="blue",
        layer=1,
        position=(50, 20),
    ),

    # Specialist Agents
    "ProjectAgent": ComponentMetadata(
        component="ProjectAgent",
        display_name="Project Expert",
        component_type="specialist_agent",
        icon="📊",
        description="Handles project management queries",
        color="green",
        layer=2,
        position=(20, 40),
    ),
    "RiskAgent": ComponentMetadata(
        component="RiskAgent",
        display_name="Risk Expert",
        component_type="specialist_agent",
        icon="⚠️",
        description="Analyzes project risks and issues",
        color="orange",
        layer=2,
        position=(50, 40),
    ),
    "FinanceAgent": ComponentMetadata(
        component="FinanceAgent",
        display_name="Finance Expert",
        component_type="specialist_agent",
        icon="💰",
        description="Analyzes financial data and budgets",
        color="yellow",
        layer=2,
        position=(80, 40),
    ),
    "ScheduleAgent": ComponentMetadata(
        component="ScheduleAgent",
        display_name="Schedule Expert",
        component_type="specialist_agent",
        icon="📅",
        description="Manages project timelines",
        color="cyan",
        layer=2,
        position=(20, 55),
    ),
    "DocumentAgent": ComponentMetadata(
        component="DocumentAgent",
        display_name="Document Expert",
        component_type="specialist_agent",
        icon="📄",
        description="Retrieves and summarizes documents",
        color="indigo",
        layer=2,
        position=(80, 55),
    ),

    # Inference
    "LLMClient": ComponentMetadata(
        component="LLMClient",
        display_name="LLM Engine",
        component_type="inference",
        icon="🧠",
        description="Language model for text generation",
        color="red",
        layer=2,
        position=(50, 70),
    ),

    # Quality & Safety
    "ReflectionAgent": ComponentMetadata(
        component="ReflectionAgent",
        display_name="Quality Check",
        component_type="validator",
        icon="✅",
        description="Reviews response quality and grounding",
        color="green",
        layer=3,
        position=(25, 85),
    ),
    "ApprovalManager": ComponentMetadata(
        component="ApprovalManager",
        display_name="Approval Gate",
        component_type="validator",
        icon="🔒",
        description="Checks if approval required for actions",
        color="red",
        layer=3,
        position=(75, 85),
    ),

    # Tools
    "ProjectLookupTool": ComponentMetadata(
        component="ProjectLookupTool",
        display_name="Project Lookup",
        component_type="tool",
        icon="🔍",
        description="Retrieves project information from database",
        color="green",
        layer=2,
        position=(15, 50),
    ),
    "RiskLookupTool": ComponentMetadata(
        component="RiskLookupTool",
        display_name="Risk Lookup",
        component_type="tool",
        icon="📋",
        description="Searches for project risks and issues",
        color="orange",
        layer=2,
        position=(45, 50),
    ),
    "SemanticSearchTool": ComponentMetadata(
        component="SemanticSearchTool",
        display_name="Semantic Search",
        component_type="tool",
        icon="🔎",
        description="Semantic document search",
        color="blue",
        layer=2,
        position=(85, 50),
    ),
}


def get_component_metadata(component: str) -> ComponentMetadata:
    """Get metadata for a component.

    Args:
        component: Component name

    Returns:
        ComponentMetadata if found, otherwise generic metadata
    """
    if component in COMPONENT_REGISTRY:
        return COMPONENT_REGISTRY[component]

    # Generic metadata for unknown components
    return ComponentMetadata(
        component=component,
        display_name=component,
        component_type="unknown",
        icon="⚙️",
        description="Component",
        color="gray",
        layer=2,
        position=(50, 50),
    )


def get_all_components() -> Dict[str, ComponentMetadata]:
    """Get all registered components."""
    return COMPONENT_REGISTRY.copy()


def register_component(metadata: ComponentMetadata) -> None:
    """Register a new component.

    Args:
        metadata: Component metadata to register
    """
    COMPONENT_REGISTRY[metadata.component] = metadata
