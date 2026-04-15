import logging
from datetime import timedelta
from django.utils import timezone
from portal.models.sla import SLAPolicy, SLATracking

logger = logging.getLogger(__name__)


def initialize_sla_for_ticket(ticket):
    """
    Called after a ticket is created.
    Looks up the matching SLAPolicy for the ticket's tenant + priority,
    computes response_due_at and resolution_due_at, and creates an SLATracking record.
    """
    if not ticket.priority:
        logger.info(f"Ticket #{ticket.id} has no priority set — skipping SLA initialization.")
        return

    policy = SLAPolicy.objects.filter(
        tenant_id=ticket.tenant_id,
        priority=ticket.priority,
    ).first()

    if not policy:
        logger.warning(
            f"No SLA policy found for tenant '{ticket.tenant_id}' and priority '{ticket.priority}'. "
            f"Skipping SLA initialization for ticket #{ticket.id}."
        )
        return

    now = timezone.now()

    SLATracking.objects.create(
        ticket_id_id=ticket.id,
        sla_policy=policy,
        response_due_at=now + timedelta(minutes=policy.response_time_minutes),
        resolution_due_at=now + timedelta(minutes=policy.resolution_time_minutes),
        response_status=SLATracking.STATUS_PENDING,
        resolution_status=SLATracking.STATUS_PENDING,
    )

    logger.info(
        f"SLA tracking initialized for ticket #{ticket.id} "
        f"(policy: {policy.priority}, "
        f"response due: {policy.response_time_minutes}m, "
        f"resolution due: {policy.resolution_time_minutes}m)."
    )
