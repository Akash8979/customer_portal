import logging
from django.db.models import Q
from django.utils import timezone
from celery import shared_task
from .models.sla import SLATracking
from .publishers import publish_sla_breach

logger = logging.getLogger(__name__)


@shared_task(name='portal.tasks.check_sla')
def check_sla():
    """
    Celery beat task — runs every 5 minutes.
    Evaluates all PENDING SLA records and marks them MET or BREACHED.

    Response SLA:
      - If ticket has a first response (responded_at is set): MET if within deadline, else BREACHED.
      - If no response yet and response_due_at has passed: BREACHED.

    Resolution SLA:
      - If ticket is resolved (resolved_at is set): MET if within deadline, else BREACHED.
      - If not resolved yet and resolution_due_at has passed: BREACHED.
    """
    now = timezone.now()
    updated_response = 0
    updated_resolution = 0
    
    pending_records = SLATracking.objects.filter(
        Q(response_status=SLATracking.STATUS_PENDING) |
        Q(resolution_status=SLATracking.STATUS_PENDING)
    ).select_related('ticket_id')

    for record in pending_records:
        changed = False
        breached = False

        # --- Response SLA ---
        if record.response_status == SLATracking.STATUS_PENDING and record.response_due_at:
            if record.responded_at:
                record.response_status = (
                    SLATracking.STATUS_MET
                    if record.responded_at <= record.response_due_at
                    else SLATracking.STATUS_BREACHED
                )
                changed = True
                updated_response += 1
            elif now > record.response_due_at:
                record.response_status = SLATracking.STATUS_BREACHED
                changed = True
                breached = True
                updated_response += 1

        # --- Resolution SLA ---
        if record.resolution_status == SLATracking.STATUS_PENDING and record.resolution_due_at:
            if record.resolved_at:
                record.resolution_status = (
                    SLATracking.STATUS_MET
                    if record.resolved_at <= record.resolution_due_at
                    else SLATracking.STATUS_BREACHED
                )
                changed = True
                updated_resolution += 1
            elif now > record.resolution_due_at:
                record.resolution_status = SLATracking.STATUS_BREACHED
                changed = True
                breached = True
                updated_resolution += 1

        if changed:
            record.save(update_fields=['response_status', 'resolution_status', 'updated_at'])
            if breached:
                tenant_id = record.ticket_id.tenant_id
                publish_sla_breach(tenant_id, record)

    logger.info(
        'SLA check complete — response updates: %d, resolution updates: %d',
        updated_response,
        updated_resolution,
    )
    return {'response_updates': updated_response, 'resolution_updates': updated_resolution}
