"""
Audit logging utility.
Call log_action() inside any view after a successful mutation.
Never raises — audit failures must not break the main request.
"""
import logging

logger = logging.getLogger(__name__)


def _get_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '')


def log_action(request, action: str, resource_type: str = '', resource_id=None, detail: dict | None = None):
    """
    Write one audit log row.

    Args:
        request     : Django request (must have .user_id, .user_name, .role, .tenant_id set by JWT middleware)
        action      : SCREAMING_SNAKE verb, e.g. TICKET_CREATE, USER_DEACTIVATE
        resource_type: TICKET | BUG | COMMENT | USER | ONBOARDING | RELEASE
        resource_id : int or str id of the affected object
        detail      : arbitrary dict with before/after state or key fields
    """
    try:
        from portal.models import AuditLog
        AuditLog.objects.create(
            user_id=str(getattr(request, 'user_id', '') or ''),
            user_name=str(getattr(request, 'user_name', '') or ''),
            user_role=str(getattr(request, 'role', '') or ''),
            tenant_id=str(getattr(request, 'tenant_id', '') or ''),
            action=action,
            resource_type=resource_type,
            resource_id=str(resource_id) if resource_id is not None else '',
            detail=detail or {},
            ip_address=_get_ip(request),
        )
    except Exception as exc:
        logger.warning("audit log failed: %s", exc)
