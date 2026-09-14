"""Structured audit logging for security-relevant events.

Introduced in v1.1.0.  All security-sensitive mutations (login, password
change, user creation/deletion) emit a structured JSON audit record that
can be shipped to a SIEM or log aggregation service.

Usage::

    from app.core.audit import audit_log, AuditEvent

    audit_log(
        event=AuditEvent.LOGIN_SUCCESS,
        actor_id=str(current_user.id),
        resource="user",
        resource_id=str(current_user.id),
        metadata={"ip": request.client.host},
    )
"""
import logging
import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

_audit_logger = logging.getLogger("audit")


class AuditEvent(StrEnum):
    # Authentication
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILURE = "auth.login.failure"
    LOGOUT = "auth.logout"
    PASSWORD_CHANGED = "auth.password.changed"
    PASSWORD_RESET_REQUESTED = "auth.password_reset.requested"
    PASSWORD_RESET_COMPLETED = "auth.password_reset.completed"

    # User management
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"
    USER_ACTIVATED = "user.activated"
    USER_DEACTIVATED = "user.deactivated"

    # Item management
    ITEM_CREATED = "item.created"
    ITEM_UPDATED = "item.updated"
    ITEM_DELETED = "item.deleted"

    # Tag management (new in v1.1.0)
    TAG_CREATED = "tag.created"
    TAG_UPDATED = "tag.updated"
    TAG_DELETED = "tag.deleted"
    TAG_ATTACHED = "tag.attached"
    TAG_DETACHED = "tag.detached"


def audit_log(
    event: AuditEvent,
    actor_id: str | None = None,
    resource: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    success: bool = True,
) -> None:
    """Emit a structured audit log record.

    The record is emitted at INFO level on the ``audit`` logger.  Wire the
    logger to a separate handler (file, syslog, SIEM) in your logging config.

    Args:
        event: The audit event type.
        actor_id: UUID string of the user performing the action.
        resource: The resource type (e.g. "user", "item", "tag").
        resource_id: UUID string of the affected resource.
        metadata: Additional context (IP address, changed fields, etc.).
        success: Whether the operation succeeded.
    """
    record: dict[str, Any] = {
        "audit_id": str(uuid.uuid4()),
        "timestamp": datetime.now(UTC).isoformat(),
        "event": str(event),
        "actor_id": actor_id,
        "resource": resource,
        "resource_id": resource_id,
        "success": success,
    }
    if metadata:
        record["metadata"] = metadata

    _audit_logger.info(record)
