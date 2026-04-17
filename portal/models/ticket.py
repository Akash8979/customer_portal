from django.db import models


class Ticket(models.Model):
    # ── Priority ──────────────────────────────────────────────────────────────
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

    # ── Category ──────────────────────────────────────────────────────────────
    CATEGORY_BUG = 'BUG'
    CATEGORY_FEATURE = 'FEATURE_REQUEST'
    CATEGORY_QUESTION = 'QUESTION'
    CATEGORY_ONBOARDING = 'ONBOARDING_ISSUE'
    CATEGORY_INTEGRATION = 'INTEGRATION_ISSUE'
    CATEGORY_PERFORMANCE = 'PERFORMANCE_ISSUE'
    CATEGORY_SUPPORT = 'SUPPORT'
    CATEGORY_BILLING = 'BILLING'
    CATEGORY_OTHER = 'OTHER'

    CATEGORY_CHOICES = [
        (CATEGORY_BUG, 'Bug Report'),
        (CATEGORY_FEATURE, 'Feature Request'),
        (CATEGORY_QUESTION, 'Question'),
        (CATEGORY_ONBOARDING, 'Onboarding Issue'),
        (CATEGORY_INTEGRATION, 'Integration Issue'),
        (CATEGORY_PERFORMANCE, 'Performance Issue'),
        (CATEGORY_SUPPORT, 'Support'),
        (CATEGORY_BILLING, 'Billing'),
        (CATEGORY_OTHER, 'Other'),
    ]

    # ── Status ────────────────────────────────────────────────────────────────
    STATUS_OPEN = 'OPEN'
    STATUS_TRIAGED = 'TRIAGED'
    STATUS_ACKNOWLEDGED = 'ACKNOWLEDGED'
    STATUS_IN_PROGRESS = 'IN_PROGRESS'
    STATUS_PENDING_CLIENT = 'PENDING_CLIENT'
    STATUS_PENDING_RELEASE = 'PENDING_RELEASE'
    STATUS_RESOLVED = 'RESOLVED'
    STATUS_CLOSED = 'CLOSED'
    STATUS_REOPENED = 'REOPENED'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_TRIAGED, 'Triaged'),
        (STATUS_ACKNOWLEDGED, 'Acknowledged'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_PENDING_CLIENT, 'Pending Client'),
        (STATUS_PENDING_RELEASE, 'Pending Release'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
        (STATUS_REOPENED, 'Reopened'),
    ]

    # ── Severity (client-reported blocking level) ─────────────────────────────
    SEVERITY_LOW = 'LOW'
    SEVERITY_MEDIUM = 'MEDIUM'
    SEVERITY_HIGH = 'HIGH'
    SEVERITY_CRITICAL = 'CRITICAL'

    SEVERITY_CHOICES = [
        (SEVERITY_LOW, 'Low — minor inconvenience'),
        (SEVERITY_MEDIUM, 'Medium — workaround exists'),
        (SEVERITY_HIGH, 'High — significantly impacted'),
        (SEVERITY_CRITICAL, 'Critical — completely blocked'),
    ]

    # ── Source ────────────────────────────────────────────────────────────────
    SOURCE_PORTAL = 'PORTAL'
    SOURCE_EMAIL = 'EMAIL'
    SOURCE_PHONE = 'PHONE'

    SOURCE_CHOICES = [
        (SOURCE_PORTAL, 'Portal'),
        (SOURCE_EMAIL, 'Email'),
        (SOURCE_PHONE, 'Phone'),
    ]

    # ── Sentiment (AI-set) ────────────────────────────────────────────────────
    SENTIMENT_POSITIVE = 'POSITIVE'
    SENTIMENT_NEUTRAL = 'NEUTRAL'
    SENTIMENT_NEGATIVE = 'NEGATIVE'
    SENTIMENT_FRUSTRATED = 'FRUSTRATED'

    SENTIMENT_CHOICES = [
        (SENTIMENT_POSITIVE, 'Positive'),
        (SENTIMENT_NEUTRAL, 'Neutral'),
        (SENTIMENT_NEGATIVE, 'Negative'),
        (SENTIMENT_FRUSTRATED, 'Frustrated'),
    ]

    # ── Core fields ───────────────────────────────────────────────────────────
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_OPEN)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, null=True, blank=True)
    tenant_id = models.CharField(max_length=100)
    created_by = models.CharField(max_length=255)
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    due_date = models.DateTimeField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    closed_at = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    # ── New fields ────────────────────────────────────────────────────────────
    tags = models.JSONField(default=list, blank=True)
    internal_note = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default=SOURCE_PORTAL)
    sentiment_score = models.CharField(max_length=20, choices=SENTIMENT_CHOICES, null=True, blank=True)
    is_escalated = models.BooleanField(default=False)
    escalated_at = models.DateTimeField(blank=True, null=True)
    csat_rating = models.PositiveSmallIntegerField(blank=True, null=True)
    csat_comment = models.TextField(blank=True, null=True)
    duplicate_of = models.IntegerField(blank=True, null=True)
    linked_bug_id = models.IntegerField(blank=True, null=True)
    linked_feature_id = models.IntegerField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.status}] {self.title}"

    class Meta:
        db_table = 'portal_ticket'
        ordering = ['-created_at']
