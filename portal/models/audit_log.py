from django.db import models


class AuditLog(models.Model):
    user_id      = models.CharField(max_length=100)
    user_name    = models.CharField(max_length=255, blank=True)
    user_role    = models.CharField(max_length=50, blank=True)
    tenant_id    = models.CharField(max_length=100, blank=True)
    action       = models.CharField(max_length=100)          # e.g. TICKET_CREATE
    resource_type = models.CharField(max_length=50, blank=True)  # TICKET, BUG, USER …
    resource_id  = models.CharField(max_length=100, blank=True)
    detail       = models.JSONField(default=dict, blank=True)
    ip_address   = models.CharField(max_length=50, blank=True)
    created_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'portal_audit_log'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['action']),
            models.Index(fields=['resource_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user_name} — {self.action} — {self.created_at:%Y-%m-%d %H:%M}"
