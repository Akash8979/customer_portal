import hashlib
from django.db import models


def hash_password(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


class UserProfile(models.Model):
    ROLE_CLIENT_ADMIN = 'CLIENT_ADMIN'
    ROLE_CLIENT_USER = 'CLIENT_USER'
    ROLE_AGENT = 'AGENT'
    ROLE_LEAD = 'LEAD'
    ROLE_ADMIN = 'ADMIN'

    ROLE_CHOICES = [
        (ROLE_CLIENT_ADMIN, 'Client Admin'),
        (ROLE_CLIENT_USER, 'Client User'),
        (ROLE_AGENT, 'Agent'),
        (ROLE_LEAD, 'Lead'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    password_hash = models.CharField(max_length=255)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    tenant_id = models.CharField(max_length=100, blank=True, null=True)
    tenant_name = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    custom_permissions = models.JSONField(default=list, blank=True)
    last_login = models.DateTimeField(blank=True, null=True)
    invited_by = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_password(self, raw: str):
        self.password_hash = hash_password(raw)

    def check_password(self, raw: str) -> bool:
        return self.password_hash == hash_password(raw)

    def __str__(self):
        return f"{self.user_name} <{self.email}> [{self.role}]"

    class Meta:
        db_table = 'um_user_profile'
        ordering = ['user_name']
