from django.db import models


class Bug(models.Model):
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CRITICAL = 'CRITICAL'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low'),
        (SEVERITY_MEDIUM, 'Medium'),
        (SEVERITY_HIGH, 'High'),
        (SEVERITY_CRITICAL, 'Critical'),
    ]

    STATUS_REPORTED = 'REPORTED'
    STATUS_REPRODUCED = 'REPRODUCED'
    STATUS_ROOT_CAUSE = 'ROOT_CAUSE_IDENTIFIED'
    STATUS_FIX_IN_PROGRESS = 'FIX_IN_PROGRESS'
    STATUS_IN_QA = 'IN_QA'
    STATUS_DEPLOYED = 'DEPLOYED'
    STATUS_VERIFIED = 'VERIFIED'
    STATUS_CLOSED = 'CLOSED'

    STATUS_CHOICES = [
        (STATUS_REPORTED, 'Reported'),
        (STATUS_REPRODUCED, 'Reproduced'),
        (STATUS_ROOT_CAUSE, 'Root Cause Identified'),
        (STATUS_FIX_IN_PROGRESS, 'Fix In Progress'),
        (STATUS_IN_QA, 'In QA'),
        (STATUS_DEPLOYED, 'Deployed'),
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_CLOSED, 'Closed'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    steps_to_reproduce = models.TextField(blank=True, null=True)
    environment = models.CharField(max_length=100, blank=True, null=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default=SEVERITY_MEDIUM)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_REPORTED)
    assignee = models.CharField(max_length=255, blank=True, null=True)
    affected_tenants = models.JSONField(default=list, blank=True)
    client_impact = models.TextField(blank=True, null=True)
    root_cause = models.TextField(blank=True, null=True)
    fix_notes = models.TextField(blank=True, null=True)
    internal_notes = models.TextField(blank=True, null=True)
    linked_ticket_ids = models.JSONField(default=list, blank=True)
    linked_release = models.ForeignKey(
        'delivery.Release', on_delete=models.SET_NULL, null=True, blank=True, related_name='bugs'
    )
    pr_url = models.CharField(max_length=500, blank=True, null=True)
    deployed_at = models.DateTimeField(blank=True, null=True)
    verified_at = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.severity}] {self.title}"

    class Meta:
        db_table = 'delivery_bug'
        ordering = ['-created_at']
