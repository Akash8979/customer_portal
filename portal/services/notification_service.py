import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


def notify_ticket_created(ticket):
    url = settings.TICKET_NOTIFY_SERVICE_URL + "/portal/ai-engine/ticket-classify"
    if not url:
        logger.warning("TICKET_NOTIFY_SERVICE_URL is not configured. Skipping notification.")
        return

    payload = {
        "id": ticket.id,
        "title": ticket.title,
        "description": ticket.description,
    }

    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        logger.info(f"Ticket #{ticket.id} notification sent successfully. Status: {response.status_code}")
    except requests.exceptions.Timeout:
        logger.error(f"Ticket #{ticket.id} notification timed out for URL: {url}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Ticket #{ticket.id} notification failed: {e}")
