from django.db import migrations
from django.utils import timezone
import datetime
import random


INTERNAL_ROLES = {'AGENT', 'LEAD', 'ADMIN'}

INTERNAL_TEMPLATES = [
    {
        'type': 'TICKET_CREATED',
        'title': 'New ticket submitted',
        'message': 'Client Acme Corp raised ticket #1: "Login page broken on Safari".',
        'link': '/internal/tickets/1',
        'is_read': False,
        'delta': datetime.timedelta(minutes=5),
    },
    {
        'type': 'TICKET_STATUS_CHANGED',
        'title': 'Ticket status updated',
        'message': 'Ticket #2 moved from Open → In Progress.',
        'link': '/internal/tickets/2',
        'is_read': False,
        'delta': datetime.timedelta(hours=2),
    },
    {
        'type': 'TICKET_ASSIGNED',
        'title': 'Ticket assigned to you',
        'message': 'You have been assigned ticket #3: "Export CSV fails for large datasets".',
        'link': '/internal/tickets/3',
        'is_read': False,
        'delta': datetime.timedelta(hours=5),
    },
    {
        'type': 'COMMENT_ADDED',
        'title': 'New comment on ticket #2',
        'message': 'Agent Sam replied: "I have reproduced the issue and will push a fix today."',
        'link': '/internal/tickets/2',
        'is_read': True,
        'delta': datetime.timedelta(days=1),
    },
    {
        'type': 'MENTION',
        'title': 'You were mentioned',
        'message': 'Agent Will mentioned you in ticket #4: "@you can you review the RCA?"',
        'link': '/internal/tickets/4',
        'is_read': True,
        'delta': datetime.timedelta(days=2),
    },
]

CLIENT_TEMPLATES = [
    {
        'type': 'TICKET_CREATED',
        'title': 'Your ticket has been received',
        'message': 'Ticket #1 "Login page broken on Safari" has been opened and assigned to our team.',
        'link': '/client/tickets/1',
        'is_read': False,
        'delta': datetime.timedelta(minutes=10),
    },
    {
        'type': 'TICKET_STATUS_CHANGED',
        'title': 'Ticket status updated',
        'message': 'Your ticket #1 has been moved to In Progress by the support team.',
        'link': '/client/tickets/1',
        'is_read': False,
        'delta': datetime.timedelta(hours=3),
    },
    {
        'type': 'COMMENT_ADDED',
        'title': 'New reply on your ticket',
        'message': 'Support agent replied on ticket #1: "We are investigating this and expect a fix by EOD."',
        'link': '/client/tickets/1',
        'is_read': False,
        'delta': datetime.timedelta(hours=6),
    },
    {
        'type': 'TICKET_STATUS_CHANGED',
        'title': 'Ticket resolved',
        'message': 'Your ticket #2 "Dashboard slow to load" has been marked as Resolved.',
        'link': '/client/tickets/2',
        'is_read': True,
        'delta': datetime.timedelta(days=1),
    },
    {
        'type': 'MENTION',
        'title': 'You were mentioned',
        'message': 'Your colleague mentioned you in ticket #3: "@you please confirm if this issue is resolved."',
        'link': '/client/tickets/3',
        'is_read': True,
        'delta': datetime.timedelta(days=3),
    },
]


def seed_all_users(apps, schema_editor):
    Notification = apps.get_model('portal', 'Notification')
    UserProfile   = apps.get_model('user_management', 'UserProfile')
    now = timezone.now()

    for profile in UserProfile.objects.all():
        is_internal = profile.role in INTERNAL_ROLES
        templates   = INTERNAL_TEMPLATES if is_internal else CLIENT_TEMPLATES
        tenant_id   = profile.tenant_id or ''

        for tmpl in templates:
            Notification.objects.create(
                user_id   = profile.id,
                tenant_id = tenant_id,
                type      = tmpl['type'],
                title     = tmpl['title'],
                message   = tmpl['message'],
                link      = tmpl['link'],
                is_read   = tmpl['is_read'],
                created_at= now - tmpl['delta'],
            )


def unseed_all_users(apps, schema_editor):
    Notification = apps.get_model('portal', 'Notification')
    UserProfile   = apps.get_model('user_management', 'UserProfile')
    ids = list(UserProfile.objects.values_list('id', flat=True))
    Notification.objects.filter(user_id__in=ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0010_seed_notifications'),
        ('user_management', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(seed_all_users, reverse_code=unseed_all_users),
    ]
