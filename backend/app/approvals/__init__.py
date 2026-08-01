"""Approval Framework Module.

Handles approval workflow for sensitive/dangerous actions.

Classes:
- ApprovalManager: Orchestrates approval workflow
- ApprovalRequest: Approval request with tracking
- ApprovalPolicy: Policy defining approval requirements
- ApprovalType: Enum of action types requiring approval

Usage:
    from app.approvals import get_approval_manager, ApprovalType

    manager = get_approval_manager()

    if manager.requires_approval(ApprovalType.DELETE_PROJECT):
        req = manager.create_approval_request(
            action_type=ApprovalType.DELETE_PROJECT,
            action_description="Delete project XYZ",
            requester_id="user123"
        )
        return {"approval_required": True, "approval_id": req.id}

    # After user approves
    manager.approve(req.id, approver_id="admin123", approved=True)

    if manager.can_execute(req.id):
        # Execute the action
        pass
"""

from app.approvals.approval_manager import ApprovalManager, get_approval_manager
from app.approvals.approval_models import (
    ApprovalPolicy,
    ApprovalRequest,
    ApprovalRequiredResponse,
    ApprovalStatus,
    ApprovalType,
)

__all__ = [
    "ApprovalManager",
    "get_approval_manager",
    "ApprovalPolicy",
    "ApprovalRequest",
    "ApprovalRequiredResponse",
    "ApprovalStatus",
    "ApprovalType",
]
