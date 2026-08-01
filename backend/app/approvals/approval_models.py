"""Approval Framework Models - Data structures for approval workflow.

Defines approval request types, policies, and workflow states.

Approval Types:
1. DELETE_PROJECT - Deleting a project (irreversible)
2. APPROVE_BUDGET - Budget approval above threshold
3. CHANGE_STATUS - Major status change (e.g., cancelled, closed)
4. ASSIGN_CREWS - Critical resource assignment
5. SEND_COMMUNICATION - Communicating about project risk
6. ESCALATE_RISK - Escalating risks to executives

Design: Approvals are gated BEFORE action execution, not after.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class ApprovalType(str, Enum):
    """Types of actions requiring approval."""

    DELETE_PROJECT = "delete_project"
    APPROVE_BUDGET = "approve_budget"
    CHANGE_STATUS = "change_status"
    ASSIGN_CREWS = "assign_crews"
    SEND_COMMUNICATION = "send_communication"
    ESCALATE_RISK = "escalate_risk"


class ApprovalStatus(str, Enum):
    """Status of an approval request."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class ApprovalPolicy:
    """Policy defining when actions require approval.

    Example:
        policy = ApprovalPolicy(
            approval_type=ApprovalType.DELETE_PROJECT,
            requires_approval=True,
            required_approvers=["admin", "project_manager"],
            timeout_hours=24,
            reason="Deletion is irreversible"
        )
    """

    def __init__(
        self,
        approval_type: ApprovalType,
        requires_approval: bool = True,
        required_approvers: List[str] = None,
        required_approval_count: int = 1,
        timeout_hours: int = 24,
        reason: str = "",
    ):
        """Initialize approval policy.

        Args:
            approval_type: Type of action
            requires_approval: Whether approval is required
            required_approvers: List of roles that can approve (e.g., ["admin", "director"])
            required_approval_count: Number of approvals needed (default 1)
            timeout_hours: Hours until approval request expires
            reason: Why this action requires approval
        """
        self.approval_type = approval_type
        self.requires_approval = requires_approval
        self.required_approvers = required_approvers or ["admin"]
        self.required_approval_count = required_approval_count
        self.timeout_hours = timeout_hours
        self.reason = reason


@dataclass
class ApprovalRequest:
    """Request for approval of a dangerous action.

    Attributes:
        id: Unique approval request ID
        type: Type of action (DELETE_PROJECT, etc.)
        status: Current status (pending, approved, rejected)
        action_description: What action is being requested
        requester_id: User who requested the action
        requested_at: When request was created
        required_approvers: Roles that can approve
        required_approval_count: How many approvals needed
        approvals: Dict of approver_id -> approval details
        approval_deadline: When request expires
        reason: Why this action requires approval
        metadata: Additional context (project_id, budget, etc.)
    """

    id: str
    type: ApprovalType
    status: ApprovalStatus = ApprovalStatus.PENDING
    action_description: str = ""
    requester_id: str = ""
    requested_at: datetime = field(default_factory=datetime.utcnow)
    required_approvers: List[str] = field(default_factory=lambda: ["admin"])
    required_approval_count: int = 1
    approvals: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    approval_deadline: Optional[datetime] = None
    reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for serialization."""
        return {
            "id": self.id,
            "type": self.type.value,
            "status": self.status.value,
            "action_description": self.action_description,
            "requester_id": self.requester_id,
            "requested_at": self.requested_at.isoformat(),
            "required_approvers": self.required_approvers,
            "required_approval_count": self.required_approval_count,
            "approvals": self.approvals,
            "approval_deadline": (
                self.approval_deadline.isoformat() if self.approval_deadline else None
            ),
            "reason": self.reason,
            "metadata": self.metadata,
        }

    def add_approval(
        self, approver_id: str, approved: bool, comment: str = ""
    ) -> None:
        """Record an approval or rejection.

        Args:
            approver_id: ID of person approving/rejecting
            approved: True if approved, False if rejected
            comment: Optional comment from approver
        """
        self.approvals[approver_id] = {
            "approved": approved,
            "at": datetime.utcnow().isoformat(),
            "comment": comment,
        }

        # Update status if rejected
        if not approved:
            self.status = ApprovalStatus.REJECTED

        # Update status if enough approvals received
        approval_count = sum(1 for a in self.approvals.values() if a["approved"])
        if approval_count >= self.required_approval_count:
            self.status = ApprovalStatus.APPROVED

    def is_expired(self) -> bool:
        """Check if approval request has expired."""
        if not self.approval_deadline:
            return False
        return datetime.utcnow() > self.approval_deadline

    def pending_approvals(self) -> int:
        """Get number of approvals still needed."""
        approved_count = sum(1 for a in self.approvals.values() if a["approved"])
        return max(0, self.required_approval_count - approved_count)


@dataclass
class ApprovalRequiredResponse:
    """Response indicating an action requires approval before execution.

    Returned by agents/tools when action needs gating.
    Client should prompt user for approval and call approval endpoint.
    """

    approval_required: bool = True
    approval_id: str = ""
    approval_type: ApprovalType = ApprovalType.DELETE_PROJECT
    reason: str = ""
    action_description: str = ""
    next_steps: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Convert to dict for API response."""
        return {
            "approval_required": self.approval_required,
            "approval_id": self.approval_id,
            "approval_type": self.approval_type.value,
            "reason": self.reason,
            "action_description": self.action_description,
            "next_steps": self.next_steps,
            "metadata": self.metadata,
        }
