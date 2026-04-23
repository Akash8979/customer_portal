from django.db import models


class Notification(models.Model):
    TYPE_TICKET_CREATED       = 'TICKET_CREATED'
    TYPE_TICKET_STATUS_CHANGED = 'TICKET_STATUS_CHANGED'
    TYPE_TICKET_ASSIGNED      = 'TICKET_ASSIGNED'
    TYPE_TICKET_ESCALATED     = 'TICKET_ESCALATED'
    TYPE_COMMENT_ADDED        = 'COMMENT_ADDED'
    TYPE_MENTION              = 'MENTION'

    TYPE_CHOICES = [
        (TYPE_TICKET_CREATED,        'Ticket Created'),
        (TYPE_TICKET_STATUS_CHANGED, 'Ticket Status Changed'),
        (TYPE_TICKET_ASSIGNED,       'Ticket Assigned'),
        (TYPE_TICKET_ESCALATED,      'Ticket Escalated'),
        (TYPE_COMMENT_ADDED,         'Comment Added'),
        (TYPE_MENTION,               'Mention'),
    ]

    id         = models.AutoField(primary_key=True)
    # recipient
    user_id    = models.IntegerField(db_index=True)
    tenant_id  = models.CharField(max_length=100, blank=True, default='')

    type       = models.CharField(max_length=40, choices=TYPE_CHOICES)
    title      = models.CharField(max_length=255)
    message    = models.TextField()
    # optional deep-link: e.g. "/internal/tickets/42"
    link       = models.CharField(max_length=500, blank=True, default='')

    is_read    = models.BooleanField(default=False, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'portal_notification'
        ordering = ['-created_at']

    def __str__(self):
        return f"[{self.type}] → user {self.user_id}: {self.title}"
