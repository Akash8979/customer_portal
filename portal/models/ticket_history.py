from django.db import models


class TicketHistory(models.Model):
    ticket_id  = models.IntegerField(db_index=True)
    user_id    = models.IntegerField(null=True, blank=True)
    action     = models.CharField(max_length=100)
    field_name = models.CharField(max_length=100, null=True, blank=True)
    old_value  = models.TextField(null=True, blank=True)
    new_value  = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_ticket_history'
        ordering = ['-created_at']

    def __str__(self):
        return f"Ticket #{self.ticket_id} — {self.action}"
