from django.db import models


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    ticket_id = models.IntegerField()
    tenant_id = models.CharField(max_length=100)
    user_id = models.IntegerField()
    parent_id = models.IntegerField(null=True, blank=True)
    message = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Comment {self.id} on Ticket {self.ticket_id}"

    class Meta:
        db_table = 'portal_comment'
        ordering = ['created_at']
