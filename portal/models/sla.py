from django.db import models
from .ticket import Ticket


class SLAPolicy(models.Model):
    """
    Defines response and resolution time limits per priority level for a tenant.
    """
    PRIORITY_LOW = 'LOW'
    PRIORITY_MEDIUM = 'MEDIUM'
    PRIORITY_HIGH = 'HIGH'
    PRIORITY_CRITICAL = 'CRITICAL'

    PRIORITY_CHOICES = [
        (PRIORITY_LOW, 'Low'),
        (PRIORITY_MEDIUM, 'Medium'),
        (PRIORITY_HIGH, 'High'),
        (PRIORITY_CRITICAL, 'Critical'),
    ]

    id = models.AutoField(primary_key=True)
    tenant_id = models.CharField(max_length=100)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES)
    # Time limits in minutes
    response_time_minutes = models.PositiveIntegerField(help_text='Max time to first response in minutes')
    resolution_time_minutes = models.PositiveIntegerField(help_text='Max time to resolution in minutes')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portal_sla_policy'
        unique_together = ('tenant_id', 'priority')

    def __str__(self):
        return f"{self.tenant_id} | {self.priority} | response={self.response_time_minutes}m | resolution={self.resolution_time_minutes}m"


class SLATracking(models.Model):
    """
    Tracks SLA status for each ticket — whether response/resolution deadlines were met.
    """
    STATUS_PENDING = 'PENDING'
    STATUS_MET = 'MET'
    STATUS_BREACHED = 'BREACHED'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_MET, 'Met'),
        (STATUS_BREACHED, 'Breached'),
    ]

    id = models.AutoField(primary_key=True)
    ticket_id = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='sla_tracking')
    sla_policy = models.ForeignKey(SLAPolicy, on_delete=models.SET_NULL, null=True, related_name='trackings')

    response_due_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)
    response_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    resolution_due_at = models.DateTimeField(null=True, blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    resolution_status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'portal_sla_tracking'

    def __str__(self):
        return f"Ticket#{self.ticket_id} | response={self.response_status} | resolution={self.resolution_status}"
