"""Approval Framework Endpoints - HTTP API for approval workflow.

Endpoints:
- GET /approvals/pending - List pending approval requests
- GET /approvals/{approval_id} - Get approval request details
- POST /approvals/{approval_id}/approve - Approve an action
- POST /approvals/{approval_id}/reject - Reject an action
- GET /approvals/{approval_id}/audit - Get audit trail
- GET /approvals - List all approval requests (with filtering)
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from app.approvals import (
    ApprovalRequest,
    ApprovalRequiredResponse,
    ApprovalStatus,
    ApprovalType,
    get_approval_manager,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["approvals"])

manager = get_approval_manager()


@router.get("/pending", response_model=List[dict])
async def list_pending_approvals():
    """List all pending approval requests.

    Returns:
        List of pending approval requests
    """
    try:
        requests = manager.list_pending()
        return [req.to_dict() for req in requests]
    except Exception as e:
        logger.error(f"Failed to list pending approvals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[dict])
async def list_approvals(
    status: Optional[str] = Query(None, description="Filter by status"),
    approval_type: Optional[str] = Query(None, description="Filter by type"),
):
    """List approval requests with optional filtering.

    Args:
        status: Optional status filter (pending, approved, rejected, expired)
        approval_type: Optional type filter

    Returns:
        List of matching approval requests
    """
    try:
        # Convert query params to enums if provided
        status_enum = None
        if status:
            try:
                status_enum = ApprovalStatus(status)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

        type_enum = None
        if approval_type:
            try:
                type_enum = ApprovalType(approval_type)
            except ValueError:
                raise HTTPException(
                    status_code=400, detail=f"Invalid approval_type: {approval_type}"
                )

        requests = manager.list_requests(status=status_enum, approval_type=type_enum)
        return [req.to_dict() for req in requests]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list approvals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{approval_id}", response_model=dict)
async def get_approval(approval_id: str):
    """Get details of an approval request.

    Args:
        approval_id: ID of approval request

    Returns:
        Approval request details
    """
    try:
        request = manager.get_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        return request.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get approval {approval_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{approval_id}/approve", response_model=dict)
async def approve_action(
    approval_id: str,
    approver_id: str = Query(..., description="ID of approver"),
    comment: str = Query("", description="Optional comment"),
):
    """Approve an action.

    Args:
        approval_id: ID of approval request
        approver_id: ID of user approving
        comment: Optional comment

    Returns:
        Updated approval request with approval recorded
    """
    try:
        request = manager.get_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if request.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot approve request in {request.status} state",
            )

        # Record approval
        can_execute = manager.approve(
            request_id=approval_id,
            approver_id=approver_id,
            approved=True,
            comment=comment,
        )

        logger.info(
            f"Approved action {approval_id} by {approver_id}. "
            f"Can execute: {can_execute}"
        )

        return request.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to approve {approval_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{approval_id}/reject", response_model=dict)
async def reject_action(
    approval_id: str,
    approver_id: str = Query(..., description="ID of rejecter"),
    comment: str = Query("", description="Reason for rejection"),
):
    """Reject an action.

    Args:
        approval_id: ID of approval request
        approver_id: ID of user rejecting
        comment: Reason for rejection

    Returns:
        Updated approval request with rejection recorded
    """
    try:
        request = manager.get_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        if request.status != ApprovalStatus.PENDING:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot reject request in {request.status} state",
            )

        # Record rejection
        manager.approve(
            request_id=approval_id,
            approver_id=approver_id,
            approved=False,
            comment=comment,
        )

        logger.info(f"Rejected action {approval_id} by {approver_id}. Reason: {comment}")

        return request.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to reject {approval_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{approval_id}/audit", response_model=List[dict])
async def get_audit_trail(approval_id: str):
    """Get audit trail for an approval request.

    Args:
        approval_id: ID of approval request

    Returns:
        List of audit log entries
    """
    try:
        request = manager.get_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        audit = manager.get_audit_trail(approval_id)
        return audit

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get audit trail for {approval_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{approval_id}/cancel", response_model=dict)
async def cancel_approval(
    approval_id: str,
    reason: str = Query("", description="Reason for cancellation"),
):
    """Cancel an approval request.

    Args:
        approval_id: ID of approval request
        reason: Reason for cancellation

    Returns:
        Updated approval request
    """
    try:
        request = manager.get_request(approval_id)
        if not request:
            raise HTTPException(status_code=404, detail="Approval request not found")

        manager.cancel_request(approval_id, reason=reason)

        logger.info(f"Cancelled approval {approval_id}. Reason: {reason}")

        return request.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel {approval_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
