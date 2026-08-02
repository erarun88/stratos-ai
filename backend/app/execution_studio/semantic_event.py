"""Execution Studio - Semantic Event Model

Self-describing events that tell the story of execution.
Every event includes purpose, reason, inputs/outputs, and relationships.
The UI can reconstruct the complete execution graph from trace alone.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, Optional, List
from enum import Enum
import uuid


class EventStatus(str, Enum):
    """Status of an execution event."""
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ComponentType(str, Enum):
    """Type of component (tells the story of what it does)."""
    ORCHESTRATOR = "orchestrator"      # Routes and coordinates
    SPECIALIST_AGENT = "specialist_agent"  # Domain expert
    TOOL = "tool"                       # Data lookup/manipulation
    INFERENCE = "inference"             # LLM call
    VALIDATOR = "validator"             # Quality/safety check
    WORKFLOW = "workflow"               # Multi-step process
    DECISION_POINT = "decision_point"   # Choice/routing logic
    AGGREGATOR = "aggregator"           # Combines results
    TRANSFORMER = "transformer"         # Modifies data


class RelationshipType(str, Enum):
    """How events relate to each other."""
    SEQUENTIAL = "sequential"           # Runs after
    PARALLEL = "parallel"               # Runs alongside
    DEPENDENCY = "dependency"           # Needs output from
    FEEDBACK = "feedback"               # Takes result back
    FALLBACK = "fallback"               # Used if first fails
    ALTERNATIVE = "alternative"         # One of multiple options
    VALIDATION_OF = "validation_of"     # Validates
    COMPOSITION = "composition"         # Combined with


@dataclass
class InputSummary:
    """What data was used by this event."""
    type: str                          # "query", "project_data", "documents", etc.
    description: str                   # Human-readable summary
    key_fields: Dict[str, Any] = field(default_factory=dict)  # Important input parts
    source_event_ids: List[str] = field(default_factory=list)  # Where it came from


@dataclass
class OutputSummary:
    """What was produced by this event."""
    type: str                          # "answer", "recommendations", "metrics", etc.
    description: str                   # Human-readable summary
    key_fields: Dict[str, Any] = field(default_factory=dict)  # Important output parts
    confidence: float = 0.5             # 0-1, how confident in output
    quality_score: float = 0.5          # 0-1, quality of output


@dataclass
class RelatedEvent:
    """Relationship to another event."""
    event_id: str
    relationship: RelationshipType
    description: str                   # Why this relationship matters


@dataclass
class ComponentDependency:
    """Component this event depends on."""
    component: str
    reason: str                        # Why this dependency exists
    criticality: str = "required"      # "required", "optional", "fallback"


@dataclass
class Decision:
    """Decision made during execution."""
    type: str                          # "routing", "selection", "synthesis", etc.
    description: str                   # What was decided
    options_considered: int = 0
    rationale: str = ""                # Why this choice
    confidence: float = 0.5


@dataclass
class SemanticExecutionEvent:
    """Self-describing event that tells the story of execution.

    Every field helps reconstruct the execution narrative.
    The UI needs no hardcoded knowledge to understand this event.
    """

    # === IDENTITY & HIERARCHY ===
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""                # Trace ID
    parent_event_id: Optional[str] = None  # What called this
    sequence_in_parent: int = 0         # Order among siblings

    # === THE STORY ===
    purpose: str = ""                  # Why this event exists
    reason: str = ""                   # What triggered it
    description: str = ""              # Human narrative of what happened

    # === WHAT & WHO ===
    component: str = ""                # "SupervisorAgent", "ProjectLookupTool", etc.
    component_type: ComponentType = ComponentType.TOOL
    component_role: str = ""           # "coordinator", "specialist", "validator"
    action: str = ""                   # "route_query", "lookup_project", "generate"

    # === I/O & SEMANTICS ===
    input: InputSummary = field(default_factory=lambda: InputSummary(type="unknown", description=""))
    output: OutputSummary = field(default_factory=lambda: OutputSummary(type="unknown", description=""))

    # === RELATIONSHIPS ===
    related_events: List[RelatedEvent] = field(default_factory=list)
    dependencies: List[ComponentDependency] = field(default_factory=list)
    decision: Optional[Decision] = None

    # === TIMING ===
    timestamp: datetime = field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    started_relative_ms: float = 0.0   # Time since request started

    # === STATUS & QUALITY ===
    status: EventStatus = EventStatus.STARTED
    error: Optional[str] = None
    warnings: List[str] = field(default_factory=list)

    # === RESOURCES ===
    tokens_used: int = 0
    tokens_input: int = 0
    tokens_output: int = 0
    cost: float = 0.0

    # === METADATA ===
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    indexed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["created_at"] = self.created_at.isoformat()
        data["status"] = self.status.value
        data["component_type"] = self.component_type.value
        data["event_id"] = str(self.event_id)
        data["request_id"] = str(self.request_id)

        # Serialize enums in nested objects
        if data.get("related_events"):
            data["related_events"] = [
                {
                    "event_id": e["event_id"],
                    "relationship": e["relationship"].value if isinstance(e["relationship"], RelationshipType) else e["relationship"],
                    "description": e["description"],
                }
                for e in data["related_events"]
            ]

        if data.get("decision") and data["decision"]:
            data["decision"]["type"] = data["decision"]["type"]

        return data

    @staticmethod
    def build(
        request_id: str,
        component: str,
        component_type: ComponentType,
        action: str,
        purpose: str,
        reason: str = "",
        description: str = "",
        parent_event_id: Optional[str] = None,
    ) -> "SemanticExecutionEvent":
        """Builder for creating well-structured events.

        Args:
            request_id: Trace ID
            component: Component name
            component_type: What kind of component
            action: What action was performed
            purpose: Why this event exists
            reason: What triggered it
            description: Human narrative
            parent_event_id: Parent event

        Returns:
            SemanticExecutionEvent ready to be enhanced
        """
        return SemanticExecutionEvent(
            request_id=request_id,
            component=component,
            component_type=component_type,
            action=action,
            purpose=purpose,
            reason=reason,
            description=description,
            parent_event_id=parent_event_id,
        )

    def with_input(
        self,
        input_type: str,
        description: str,
        key_fields: Optional[Dict[str, Any]] = None,
        source_event_ids: Optional[List[str]] = None,
    ) -> "SemanticExecutionEvent":
        """Add input details."""
        self.input = InputSummary(
            type=input_type,
            description=description,
            key_fields=key_fields or {},
            source_event_ids=source_event_ids or [],
        )
        return self

    def with_output(
        self,
        output_type: str,
        description: str,
        key_fields: Optional[Dict[str, Any]] = None,
        confidence: float = 0.5,
        quality_score: float = 0.5,
    ) -> "SemanticExecutionEvent":
        """Add output details."""
        self.output = OutputSummary(
            type=output_type,
            description=description,
            key_fields=key_fields or {},
            confidence=confidence,
            quality_score=quality_score,
        )
        return self

    def with_decision(
        self,
        decision_type: str,
        description: str,
        options_considered: int = 0,
        rationale: str = "",
        confidence: float = 0.5,
    ) -> "SemanticExecutionEvent":
        """Add decision information."""
        self.decision = Decision(
            type=decision_type,
            description=description,
            options_considered=options_considered,
            rationale=rationale,
            confidence=confidence,
        )
        return self

    def with_dependency(
        self,
        component: str,
        reason: str,
        criticality: str = "required",
    ) -> "SemanticExecutionEvent":
        """Add a dependency."""
        self.dependencies.append(
            ComponentDependency(
                component=component,
                reason=reason,
                criticality=criticality,
            )
        )
        return self

    def with_related_event(
        self,
        event_id: str,
        relationship: RelationshipType,
        description: str,
    ) -> "SemanticExecutionEvent":
        """Add a relationship to another event."""
        self.related_events.append(
            RelatedEvent(
                event_id=event_id,
                relationship=relationship,
                description=description,
            )
        )
        return self

    def add_warning(self, warning: str) -> "SemanticExecutionEvent":
        """Add a warning."""
        self.warnings.append(warning)
        return self

    def mark_completed(self, duration_ms: float = 0.0) -> "SemanticExecutionEvent":
        """Mark as completed."""
        self.status = EventStatus.COMPLETED
        if duration_ms > 0:
            self.duration_ms = duration_ms
        return self

    def mark_failed(self, error: str) -> "SemanticExecutionEvent":
        """Mark as failed."""
        self.status = EventStatus.FAILED
        self.error = error
        return self


# Keep the old event model for backward compatibility
from app.execution_studio.event_model import ExecutionEvent, TraceMetrics

__all__ = [
    "SemanticExecutionEvent",
    "EventStatus",
    "ComponentType",
    "RelationshipType",
    "InputSummary",
    "OutputSummary",
    "RelatedEvent",
    "ComponentDependency",
    "Decision",
    # Backward compatibility
    "ExecutionEvent",
    "TraceMetrics",
]
