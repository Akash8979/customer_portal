from django.db import models


class Feature(models.Model):
    STATUS_PLANNED = 'PLANNED'
    STATUS_IN_DEV = 'IN_DEV'
    STATUS_IN_QA = 'IN_QA'
    STATUS_IN_STAGING = 'IN_STAGING'
    STATUS_RELEASED = 'RELEASED'
    STATUS_BACKLOG = 'BACKLOG'
    STATUS_DECLINED = 'DECLINED'

    STATUS_CHOICES = [
        (STATUS_BACKLOG, 'Backlog'),
        (STATUS_PLANNED, 'Planned'),
        (STATUS_IN_DEV, 'In Development'),
        (STATUS_IN_QA, 'In QA'),
        (STATUS_IN_STAGING, 'In Staging'),
        (STATUS_RELEASED, 'Released'),
        (STATUS_DECLINED, 'Declined'),
    ]

    QUARTER_CHOICES = [
        ('Q1', 'Q1'), ('Q2', 'Q2'), ('Q3', 'Q3'), ('Q4', 'Q4'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_BACKLOG)
    assignee = models.CharField(max_length=255, blank=True, null=True)
    quarter = models.CharField(max_length=5, choices=QUARTER_CHOICES, blank=True, null=True)
    year = models.PositiveSmallIntegerField(blank=True, null=True)
    estimated_release = models.DateField(blank=True, null=True)
    actual_release = models.DateField(blank=True, null=True)
    is_public = models.BooleanField(default=True)
    vote_count = models.PositiveIntegerField(default=0)
    linked_release = models.ForeignKey(
        'delivery.Release', on_delete=models.SET_NULL, null=True, blank=True, related_name='features'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'delivery_feature'
        ordering = ['-created_at']


class FeatureRequest(models.Model):
    STATUS_UNDER_REVIEW = 'UNDER_REVIEW'
    STATUS_ON_ROADMAP = 'ON_ROADMAP'
    STATUS_DECLINED = 'DECLINED'
    STATUS_RELEASED = 'RELEASED'

    STATUS_CHOICES = [
        (STATUS_UNDER_REVIEW, 'Under Review'),
        (STATUS_ON_ROADMAP, 'On Roadmap'),
        (STATUS_DECLINED, 'Declined'),
        (STATUS_RELEASED, 'Released'),
    ]

    feature = models.ForeignKey(Feature, on_delete=models.SET_NULL, null=True, blank=True, related_name='requests')
    tenant_id = models.CharField(max_length=100)
    requested_by = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_UNDER_REVIEW)
    decline_reason = models.TextField(blank=True, null=True)
    linked_ticket_id = models.IntegerField(blank=True, null=True)
    upvotes = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.tenant_id}] {self.title}"

    class Meta:
        db_table = 'delivery_feature_request'
        ordering = ['-created_at']


class FeatureVote(models.Model):
    feature = models.ForeignKey(Feature, on_delete=models.CASCADE, related_name='votes')
    tenant_id = models.CharField(max_length=100)
    user_email = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'delivery_feature_vote'
        unique_together = ('feature', 'user_email')
