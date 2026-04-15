import json
import logging
import redis
from django.conf import settings

logger = logging.getLogger(__name__)

_redis_client = None


def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis.from_url(
            settings.CELERY_BROKER_URL, decode_responses=True
        )
    return _redis_client


def _channel(tenant_id, ticket_id=None):
    """
    Channel naming:
      tenant-wide  : portal:events:<tenant_id>
      ticket-scoped: portal:events:<tenant_id>:ticket:<ticket_id>
    """
    if ticket_id:
        return f"portal:events:{tenant_id}:ticket:{ticket_id}"
    return f"portal:events:{tenant_id}"


def publish(tenant_id, event, data, ticket_id=None):
    """
    Publish an event to both the tenant-wide channel and, if ticket_id is
    given, the ticket-scoped channel. This means a client subscribed to
    either channel will receive the event.
    """
    message = json.dumps({"event": event, "data": data})
    try:
        r = get_redis()
        r.publish(_channel(tenant_id), message)
        if ticket_id:
            r.publish(_channel(tenant_id, ticket_id), message)
    except Exception as e:
        logger.error(f"Redis publish failed [event={event}]: {e}")


# ---------------------------------------------------------------------------
# Typed helpers — call these from views / tasks instead of raw publish()
# ---------------------------------------------------------------------------

def publish_ticket_status(tenant_id, ticket):
    from django.utils import timezone
    publish(
        tenant_id,
        event="ticket_status",
        data={
            "ticket_id": ticket.id,
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_to": ticket.assigned_to,
            "timestamp": timezone.now().isoformat(),
        },
        ticket_id=ticket.id,
    )


def publish_new_comment(tenant_id, comment):
    from django.utils import timezone
    publish(
        tenant_id,
        event="new_comment",
        data={
            "comment_id": comment.id,
            "ticket_id": comment.ticket_id,
            "user_id": comment.user_id,
            "message": comment.message,
            "timestamp": timezone.now().isoformat(),
        },
        ticket_id=comment.ticket_id,
    )


def publish_sla_breach(tenant_id, sla):
    from django.utils import timezone
    publish(
        tenant_id,
        event="sla_breach",
        data={
            "ticket_id": sla.ticket_id_id,
            "response_status": sla.response_status,
            "resolution_status": sla.resolution_status,
            "response_due_at": sla.response_due_at.isoformat() if sla.response_due_at else None,
            "resolution_due_at": sla.resolution_due_at.isoformat() if sla.resolution_due_at else None,
            "timestamp": timezone.now().isoformat(),
        },
        ticket_id=sla.ticket_id_id,
    )


def publish_ticket_created(tenant_id, ticket):
    from django.utils import timezone
    publish(
        tenant_id,
        event="ticket_created",
        data={
            "ticket_id": ticket.id,
            "title": ticket.title,
            "priority": ticket.priority,
            "category": ticket.category,
            "created_by": ticket.created_by,
            "timestamp": timezone.now().isoformat(),
        },
        ticket_id=ticket.id,
    )
