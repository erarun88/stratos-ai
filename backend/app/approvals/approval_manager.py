"""Approval Manager - Orchestrates approval workflow and audit trail.

Responsibilities:
1. Create approval requests for dangerous actions
2. Track approvals and rejections
3. Determine action eligibility (approval complete, expired, etc.)
4. Maintain audit trail of all approvals
5. Policy registry for approval requirements

Usage:
    manager = ApprovalManager()

    # Register approval policies
    manager.register_policy(ApprovalPolicy(
        approval_type=ApprovalType.DELETE_PROJECT,
        requires_approval=True,
        required_approvers=["admin"]
    ))

    # Check if action requires approval
    if manager.requires_approval(ApprovalType.DELETE_PROJECT):
        req = manager.create_approval_request(
            type=ApprovalType.DELETE_PROJECT,
            action_description="Delete project XYZ",
            requester_id="user123"
        )
        return req  # Tell user to get approval

    # When user approves
    manager.approve(req.id, approver_id="admin123", approved=True)

    # Check if action can execute
    if manager.can_execute(req.id):
        # Proceed with action
        pass
"""

import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from app.approvals.approval_models import (
    ApprovalPolicy,
    ApprovalRequest,
    ApprovalRequiredResponse,
    ApprovalStatus,
    ApprovalType,
)
from app.execution_studio import emit_event

logger = logging.getLogger(__name__)


class ApprovalManager:
    """Orchestrates approval workflow for sensitive actions.

    Singleton pattern - one manager per application.
    Maintains approval registry, policies, and audit trail.

    Key methods:
    - requires_approval(action_type) -> bool
    - create_approval_request(...) -> ApprovalRequest
    - approve(request_id, approver_id, approved) -> None
    - can_execute(request_id) -> bool
    - get_request(request_id) -> ApprovalRequest
    - list_pending() -> List[ApprovalRequest]
    """

    def __init__(self):
        """Initialize Approval Manager."""
        self.policies: Dict[ApprovalType, ApprovalPolicy] = {}
        self.requests: Dict[str, ApprovalRequest] = {}
        self.audit_trail: List[Dict] = []

        self._register_default_policies()
        logger.info("ApprovalManager initialized with default policies")

    def _register_default_policies(self) -> None:
        """Register default approval policies for dangerous actions."""
        # DELETE_PROJECT: requires approval, single admin approval
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.DELETE_PROJECT,
                requires_approval=True,
                required_approvers=["admin", "project_manager"],
                required_approval_count=1,
                timeout_hours=24,
                reason="Project deletion is irreversible",
            )
        )

        # APPROVE_BUDGET: requires single approval
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.APPROVE_BUDGET,
                requires_approval=True,
                required_approvers=["finance", "director"],
                required_approval_count=1,
                timeout_hours=48,
                reason="Budget approval requires financial sign-off",
            )
        )

        # CHANGE_STATUS: e.g., cancel, close
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.CHANGE_STATUS,
                requires_approval=True,
                required_approvers=["project_manager", "director"],
                required_approval_count=1,
                timeout_hours=24,
                reason="Major status changes require approval",
            )
        )

        # ASSIGN_CREWS: critical assignments
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.ASSIGN_CREWS,
                requires_approval=True,
                required_approvers=["resource_manager", "director"],
                required_approval_count=1,
                timeout_hours=24,
                reason="Critical crew assignments require approval",
            )
        )

        # SEND_COMMUNICATION: risk communications
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.SEND_COMMUNICATION,
                requires_approval=True,
                required_approvers=["communications", "director"],
                required_approval_count=1,
                timeout_hours=12,
                reason="Risk communications require approval before sending",
            )
        )

        # ESCALATE_RISK: escalating to executives
        self.register_policy(
            ApprovalPolicy(
                approval_type=ApprovalType.ESCALATE_RISK,
                requires_approval=True,
                required_approvers=["director", "ceo"],
                required_approval_count=1,
                timeout_hours=4,
                reason="Executive escalations require approval",
            )
        )

    def register_policy(self, policy: ApprovalPolicy) -> None:
        """Register an approval policy.

        Args:
            policy: ApprovalPolicy defining requirements for action type
        """
        self.policies[policy.approval_type] = policy
        logger.info(f"Registered approval policy for {policy.approval_type}")

    def requires_approval(self, action_type: ApprovalType) -> bool:
        """Check if action requires approval.

        Args:
            action_type: Type of action to check

        Returns:
            True if approval is required
        """
        policy = self.policies.get(action_type)
        return policy and policy.requires_approval

    def create_approval_request(
        self,
        action_type: ApprovalType,
        action_description: str,
        requester_id: str,
        metadata: Dict = None,
    ) -> ApprovalRequest:
        """Create an approval request for a dangerous action.

        Args:
            action_type: Type of action requiring approval
            action_description: What action is being requested
            requester_id: User requesting the action
            metadata: Additional context (project_id, amount, etc.)

        Returns:
            ApprovalRequest with unique ID
        """
        policy = self.policies.get(action_type)
        if not policy:
            raise ValueError(f"No approval policy for {action_type}")

        req_id = f"approval_{uuid.uuid4().hex[:16]}"
        deadline = datetime.utcnow() + timedelta(hours=policy.timeout_hours)

        request = ApprovalRequest(
            id=req_id,
            type=action_type,
            status=ApprovalStatus.PENDING,
            action_description=action_description,
            requester_id=requester_id,
            requested_at=datetime.utcnow(),
            required_approvers=policy.required_approvers,
            required_approval_count=policy.required_approval_count,
            approval_deadline=deadline,
            reason=policy.reason,
            metadata=metadata or {},
        )

        self.requests[req_id] = request
        self._audit_log("approval_created", req_id, requester_id)

        # Emit event: approval request created
        emit_event("ApprovalManager", "create_approval_request", metadata={
            "approval_id": req_id,
            "approval_type": action_type,
            "requester_id": requester_id,
            "deadline_hours": policy.timeout_hours,
        })

        logger.info(
            f"Created approval request: {req_id} for {action_type} "
            f"(requested by {requester_id})"
        )

        return request

    def approve(
        self,
        request_id: str,
        approver_id: str,
        approved: bool,
        comment: str = "",
    ) -> bool:
        """Record an approval or rejection.

        Args:
            request_id: ID of approval request
            approver_id: User approving/rejecting
            approved: True to approve, False to reject
            comment: Optional comment from approver

        Returns:
            True if action can now execute (approval complete)
        """
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        if request.status != ApprovalStatus.PENDING:
            raise ValueError(
                f"Cannot approve request in {request.status} state"
            )

        request.add_approval(approver_id, approved, comment)

        action = "approved" if approved else "rejected"
        self._audit_log(f"approval_{action}", request_id, approver_id, comment)

        # Emit event: approval processed
        emit_event("ApprovalManager", f"approval_{action}", metadata={
            "approval_id": request_id,
            "approver_id": approver_id,
            "approval_type": request.type,
            "status": request.status,
            "pending_approvals": request.pending_approvals(),
        })

        logger.info(
            f"Recorded {action} for {request_id} by {approver_id}. "
            f"Status: {request.status}, pending: {request.pending_approvals()}"
        )

        return request.status == ApprovalStatus.APPROVED

    def can_execute(self, request_id: str) -> bool:
        """Check if action can execute (approval complete and not expired).

        Args:
            request_id: ID of approval request

        Returns:
            True if action can execute
        """
        request = self.requests.get(request_id)
        if not request:
            return False

        if request.is_expired():
            request.status = ApprovalStatus.EXPIRED
            self._audit_log("approval_expired", request_id, "system")

            # Emit event: approval expired
            emit_event("ApprovalManager", "approval_expired", metadata={
                "approval_id": request_id,
                "approval_type": request.type,
            })

            logger.warning(f"Approval request expired: {request_id}")
            return False

        # Emit event: can_execute check
        can_exec = request.status == ApprovalStatus.APPROVED
        emit_event("ApprovalManager", "can_execute_check", metadata={
            "approval_id": request_id,
            "approval_type": request.type,
            "can_execute": can_exec,
            "status": request.status,
        })

        return can_exec

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        """Retrieve approval request by ID.

        Args:
            request_id: ID of approval request

        Returns:
            ApprovalRequest or None if not found
        """
        return self.requests.get(request_id)

    def list_pending(self) -> List[ApprovalRequest]:
        """Get all pending approval requests.

        Returns:
            List of pending ApprovalRequest objects
        """
        return [
            req
            for req in self.requests.values()
            if req.status == ApprovalStatus.PENDING and not req.is_expired()
        ]

    def list_requests(
        self,
        status: Optional[ApprovalStatus] = None,
        approval_type: Optional[ApprovalType] = None,
    ) -> List[ApprovalRequest]:
        """List approval requests with optional filtering.

        Args:
            status: Filter by status (optional)
            approval_type: Filter by type (optional)

        Returns:
            List of matching ApprovalRequest objects
        """
        results = list(self.requests.values())

        if status:
            results = [r for r in results if r.status == status]

        if approval_type:
            results = [r for r in results if r.type == approval_type]

        return results

    def cancel_request(self, request_id: str, reason: str = "") -> None:
        """Cancel an approval request.

        Args:
            request_id: ID of approval request
            reason: Optional reason for cancellation
        """
        request = self.requests.get(request_id)
        if not request:
            raise ValueError(f"Approval request not found: {request_id}")

        request.status = ApprovalStatus.CANCELLED
        self._audit_log("approval_cancelled", request_id, "system", reason)

        logger.info(f"Cancelled approval request: {request_id}")

    def _audit_log(
        self,
        action: str,
        request_id: str,
        user_id: str,
        details: str = "",
    ) -> None:
        """Log action to audit trail.

        Args:
            action: Action type (approval_created, approved, rejected, etc.)
            request_id: Approval request ID
            user_id: User performing action
            details: Additional details
        """
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "request_id": request_id,
            "user_id": user_id,
            "details": details,
        }
        self.audit_trail.append(entry)

    def get_audit_trail(self, request_id: str) -> List[Dict]:
        """Get audit trail for a request.

        Args:
            request_id: ID of approval request

        Returns:
            List of audit log entries
        """
        return [e for e in self.audit_trail if e["request_id"] == request_id]


# Global singleton
_approval_manager: Optional[ApprovalManager] = None


def get_approval_manager() -> ApprovalManager:
    """Get or create global approval manager."""
    global _approval_manager
    if _approval_manager is None:
        _approval_manager = ApprovalManager()
    return _approval_manager
