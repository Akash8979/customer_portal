import logging

from django.core.mail import send_mail
from django.conf import settings

logger = logging.getLogger(__name__)


def _send(subject, message, recipient, log_label):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        logger.info(f"{log_label} email sent to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send {log_label} email to {recipient}: {e}")


def send_ticket_created_email(ticket):
    subject = f"[Ticket #{ticket.id}] New Ticket: {ticket.title}"
    message = f"""
A new support ticket has been created.

Ticket ID   : {ticket.id}
Title       : {ticket.title}
Category    : {ticket.category}
Priority    : {ticket.priority}
Status      : {ticket.status}
Created By  : {ticket.created_by}
Description :
{ticket.description}

---
Customer Portal
"""
    _send(subject, message, ticket.created_by, f"ticket_created #{ticket.id}")


def send_ticket_updated_email(ticket):
    subject = f"[Ticket #{ticket.id}] Updated: {ticket.title}"
    message = f"""
Your support ticket has been updated.

Ticket ID   : {ticket.id}
Title       : {ticket.title}
Category    : {ticket.category}
Priority    : {ticket.priority}
Status      : {ticket.status}
Assigned To : {ticket.assigned_to or 'Unassigned'}

---
Customer Portal
"""
    _send(subject, message, ticket.created_by, f"ticket_updated #{ticket.id}")


def send_comment_created_email(comment, ticket):
    subject = f"[Ticket #{ticket.id}] New Comment"
    message = f"""
A new comment has been added to your ticket.

Ticket ID   : {ticket.id}
Ticket Title: {ticket.title}
Comment ID  : {comment.id}
Comment     :
{comment.message}

---
Customer Portal
"""
    _send(subject, message, ticket.created_by, f"comment_created #{comment.id}")


def send_comment_updated_email(comment, ticket):
    subject = f"[Ticket #{ticket.id}] Comment Updated"
    message = f"""
A comment on your ticket has been updated.

Ticket ID   : {ticket.id}
Ticket Title: {ticket.title}
Comment ID  : {comment.id}
Updated Comment:
{comment.message}

---
Customer Portal
"""
    _send(subject, message, ticket.created_by, f"comment_updated #{comment.id}")
