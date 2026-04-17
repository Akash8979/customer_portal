from django.db import models


class OnboardingProject(models.Model):
    STATUS_NOT_STARTED = 'NOT_STARTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_ON_TRACK = 'ON_TRACK'
    STATUS_AT_RISK = 'AT_RISK'
    STATUS_BLOCKED = 'BLOCKED'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, 'Not Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_ON_TRACK, 'On Track'),
        (STATUS_AT_RISK, 'At Risk'),
        (STATUS_BLOCKED, 'Blocked'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    tenant_id = models.CharField(max_length=100, unique=True)
    tenant_name = models.CharField(max_length=255)
    assigned_lead = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_STARTED)
    health_score = models.CharField(
        max_length=20,
        choices=[('ON_TRACK', 'On Track'), ('AT_RISK', 'At Risk'), ('BLOCKED', 'Blocked')],
        default='ON_TRACK',
    )
    estimated_go_live = models.DateField(blank=True, null=True)
    actual_go_live = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Onboarding: {self.tenant_name}"

    class Meta:
        db_table = 'delivery_onboarding_project'
        ordering = ['-created_at']


class OnboardingPhase(models.Model):
    STATUS_NOT_STARTED = 'NOT_STARTED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_BLOCKED = 'BLOCKED'

    STATUS_CHOICES = [
        (STATUS_NOT_STARTED, 'Not Started'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_BLOCKED, 'Blocked'),
    ]

    project = models.ForeignKey(OnboardingProject, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=255)
    order = models.PositiveSmallIntegerField(default=0)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_NOT_STARTED)
    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def completion_percentage(self):
        tasks = self.tasks.all()
        if not tasks.exists():
            return 0
        done = tasks.filter(status='COMPLETED').count()
        return round((done / tasks.count()) * 100)

    def __str__(self):
        return f"{self.project.tenant_name} — Phase {self.order}: {self.name}"

    class Meta:
        db_table = 'delivery_onboarding_phase'
        ordering = ['order']


class OnboardingTask(models.Model):
    STATUS_TODO = 'TODO'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_BLOCKED = 'BLOCKED'
    STATUS_COMPLETED = 'COMPLETED'

    STATUS_CHOICES = [
        (STATUS_TODO, 'To Do'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_BLOCKED, 'Blocked'),
        (STATUS_COMPLETED, 'Completed'),
    ]

    OWNER_CLIENT = 'CLIENT'
    OWNER_DELIVERY = 'DELIVERY'

    OWNER_CHOICES = [
        (OWNER_CLIENT, 'Client'),
        (OWNER_DELIVERY, 'Delivery Team'),
    ]

    phase = models.ForeignKey(OnboardingPhase, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    owner = models.CharField(max_length=20, choices=OWNER_CHOICES, default=OWNER_DELIVERY)
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_TODO)
    due_date = models.DateField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    is_blocker = models.BooleanField(default=False)
    blocker_reason = models.TextField(blank=True, null=True)
    linked_ticket_id = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.phase.name} — {self.title}"

    class Meta:
        db_table = 'delivery_onboarding_task'
        ordering = ['due_date']
