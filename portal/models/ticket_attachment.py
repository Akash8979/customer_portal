from django.db import models


class TicketAttachment(models.Model):
    id = models.AutoField(primary_key=True)
    reference_id = models.IntegerField()
    attachment_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment {self.attachment_id}"

    class Meta:
        db_table = 'portal_ticket_attachment'
        ordering = ['-created_at']
