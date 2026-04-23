import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


# ── AI-engine classifier (kept from original) ────────────────────────────────

def notify_ticket_created(ticket):
    url = settings.TICKET_NOTIFY_SERVICE_URL + "/portal/ai-engine/ticket-classify"
    if not url:
        logger.warning("TICKET_NOTIFY_SERVICE_URL is not configured. Skipping notification.")
        return
    payload = {"id": ticket.id, "title": ticket.title, "description": ticket.description}
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Ticket #{ticket.id} notification sent. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error(f"Ticket #{ticket.id} notification timed out for URL: {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ticket #{ticket.id} notification failed: {e}")


# ── Core in-app notification creator ─────────────────────────────────────────

def create_notification(*, user_id, tenant_id='', notif_type, title, message, link=''):
    """Persist one in-app notification row. Never raises — failures are logged."""
    try:
        from portal.models import Notification
        Notification.objects.create(
            user_id=user_id,
            tenant_id=tenant_id or '',
            type=notif_type,
            title=title,
            message=message,
            link=link,
        )
    except Exception as exc:
        logger.warning("create_notification failed: %s", exc)


# ── Recipient helpers ─────────────────────────────────────────────────────────

def _all_agent_ids():
    """Return ids of all active internal agents / leads / admins."""
    try:
        from user_management.models import UserProfile
        return list(
            UserProfile.objects
            .filter(is_active=True, role__in=['AGENT', 'LEAD', 'ADMIN'])
            .values_list('id', flat=True)
        )
    except Exception as exc:
        logger.warning("_all_agent_ids failed: %s", exc)
        return []


def _tenant_user_ids(tenant_id):
    """Return ids of all active users belonging to a tenant."""
    try:
        from user_management.models import UserProfile
        return list(
            UserProfile.objects
            .filter(is_active=True, tenant_id=tenant_id)
            .values_list('id', flat=True)
        )
    except Exception as exc:
        logger.warning("_tenant_user_ids failed: %s", exc)
        return []


# ── Event-specific fan-out helpers ────────────────────────────────────────────

def on_ticket_created(ticket, actor_user_id=None):
    """Client created a ticket → notify all internal agents."""
    from portal.models import Notification
    link = f"/internal/tickets/{ticket.id}"
    for uid in _all_agent_ids():
        if uid == actor_user_id:
            continue
        create_notification(
            user_id=uid,
            notif_type=Notification.TYPE_TICKET_CREATED,
            title="New ticket submitted",
            message=f"#{ticket.id} — {ticket.title}",
            link=link,
        )


def on_ticket_status_changed(ticket, old_status, actor_user_id=None):
    """Status changed → notify client users on that tenant + all agents."""
    from portal.models import Notification

    for uid in _tenant_user_ids(ticket.tenant_id):
        if uid == actor_user_id:
            continue
        create_notification(
            user_id=uid,
            tenant_id=ticket.tenant_id,
            notif_type=Notification.TYPE_TICKET_STATUS_CHANGED,
            title="Ticket status updated",
            message=f"#{ticket.id} — {ticket.title}: {old_status} → {ticket.status}",
            link=f"/client/tickets/{ticket.id}",
        )

    for uid in _all_agent_ids():
        if uid == actor_user_id:
            continue
        create_notification(
            user_id=uid,
            notif_type=Notification.TYPE_TICKET_STATUS_CHANGED,
            title="Ticket status changed",
            message=f"#{ticket.id} — {ticket.title}: {old_status} → {ticket.status}",
            link=f"/internal/tickets/{ticket.id}",
        )


def on_ticket_assigned(ticket, assigned_user_id, actor_user_id=None):
    """Ticket assigned → notify the new assignee."""
    from portal.models import Notification
    if not assigned_user_id or assigned_user_id == actor_user_id:
        return
    create_notification(
        user_id=assigned_user_id,
        notif_type=Notification.TYPE_TICKET_ASSIGNED,
        title="Ticket assigned to you",
        message=f"#{ticket.id} — {ticket.title}",
        link=f"/internal/tickets/{ticket.id}",
    )


def on_ticket_escalated(ticket, actor_user_id=None):
    """Ticket escalated → notify leads and admins."""
    from portal.models import Notification
    try:
        from user_management.models import UserProfile
        leads = list(
            UserProfile.objects
            .filter(is_active=True, role__in=['LEAD', 'ADMIN'])
            .values_list('id', flat=True)
        )
    except Exception:
        leads = []

    for uid in leads:
        if uid == actor_user_id:
            continue
        create_notification(
            user_id=uid,
            notif_type=Notification.TYPE_TICKET_ESCALATED,
            title="Ticket escalated",
            message=f"#{ticket.id} — {ticket.title} has been escalated.",
            link=f"/internal/tickets/{ticket.id}",
        )


def on_comment_added(comment, ticket, actor_user_id=None):
    """
    Comment posted:
    - Internal note  → notify agents (excluding poster)
    - Public comment → notify tenant users + assigned agent
    """
    from portal.models import Notification

    if comment.is_internal:
        for uid in _all_agent_ids():
            if uid == actor_user_id:
                continue
            create_notification(
                user_id=uid,
                notif_type=Notification.TYPE_COMMENT_ADDED,
                title="New internal note",
                message=f"#{ticket.id} — {ticket.title}",
                link=f"/internal/tickets/{ticket.id}",
            )
    else:
        for uid in _tenant_user_ids(ticket.tenant_id):
            if uid == actor_user_id:
                continue
            create_notification(
                user_id=uid,
                tenant_id=ticket.tenant_id,
                notif_type=Notification.TYPE_COMMENT_ADDED,
                title="New reply on your ticket",
                message=f"#{ticket.id} — {ticket.title}",
                link=f"/client/tickets/{ticket.id}",
            )
        if ticket.assigned_to:
            try:
                from user_management.models import UserProfile
                agent = UserProfile.objects.filter(
                    email=ticket.assigned_to, is_active=True
                ).first()
                if agent and agent.id != actor_user_id:
                    create_notification(
                        user_id=agent.id,
                        notif_type=Notification.TYPE_COMMENT_ADDED,
                        title="New comment on your ticket",
                        message=f"#{ticket.id} — {ticket.title}",
                        link=f"/internal/tickets/{ticket.id}",
                    )
            except Exception as exc:
                logger.warning("on_comment_added agent lookup: %s", exc)


def on_mention(mentioned_user_id, ticket, actor_user_id=None):
    """User was @mentioned in a comment."""
    from portal.models import Notification
    if mentioned_user_id == actor_user_id:
        return
    create_notification(
        user_id=mentioned_user_id,
        notif_type=Notification.TYPE_MENTION,
        title="You were mentioned",
        message=f"You were mentioned in ticket #{ticket.id} — {ticket.title}",
        link=f"/internal/tickets/{ticket.id}",
    )
