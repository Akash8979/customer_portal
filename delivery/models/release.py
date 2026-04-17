from django.db import models


class Release(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_IN_TESTING = 'IN_TESTING'
    STATUS_PUBLISHED = 'PUBLISHED'

    STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_IN_TESTING, 'In Testing'),
        (STATUS_PUBLISHED, 'Published'),
    ]

    version = models.CharField(max_length=50, unique=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    release_notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_DRAFT)
    is_hotfix = models.BooleanField(default=False)
    release_date = models.DateField(blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_by = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"v{self.version} — {self.title}"

    class Meta:
        db_table = 'delivery_release'
        ordering = ['-release_date', '-created_at']
