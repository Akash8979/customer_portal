from django.db import migrations
from django.utils import timezone
import datetime


def seed_notifications(apps, schema_editor):
    Notification = apps.get_model('portal', 'Notification')
    now = timezone.now()

    # user_id=14 is Tina Rahman (AGENT, internal) — tenant_id='' for internal users
    entries = [
        {
            'user_id':   14,
            'tenant_id': '',
            'type':      'TICKET_CREATED',
            'title':     'New ticket submitted',
            'message':   'Client Acme Corp raised ticket #1: "Login page broken on Safari".',
            'link':      '/internal/tickets/1',
            'is_read':   False,
            'created_at': now - datetime.timedelta(minutes=5),
        },
        {
            'user_id':   14,
            'tenant_id': '',
            'type':      'TICKET_STATUS_CHANGED',
            'title':     'Ticket status updated',
            'message':   'Ticket #1 moved from Open → In Progress.',
            'link':      '/internal/tickets/1',
            'is_read':   False,
            'created_at': now - datetime.timedelta(hours=1),
        },
        {
            'user_id':   14,
            'tenant_id': '',
            'type':      'TICKET_ASSIGNED',
            'title':     'Ticket assigned to you',
            'message':   'You have been assigned ticket #2: "Export CSV fails for large datasets".',
            'link':      '/internal/tickets/2',
            'is_read':   False,
            'created_at': now - datetime.timedelta(hours=3),
        },
        {
            'user_id':   14,
            'tenant_id': '',
            'type':      'COMMENT_ADDED',
            'title':     'New comment on ticket #1',
            'message':   'Agent Sarah replied: "I have reproduced the issue and will push a fix today."',
            'link':      '/internal/tickets/1',
            'is_read':   True,
            'created_at': now - datetime.timedelta(days=1),
        },
        {
            'user_id':   14,
            'tenant_id': '',
            'type':      'MENTION',
            'title':     'You were mentioned',
            'message':   'Agent Will mentioned you in ticket #3: "@you can you review the RCA?"',
            'link':      '/internal/tickets/3',
            'is_read':   True,
            'created_at': now - datetime.timedelta(days=2),
        },
    ]

    for entry in entries:
        Notification.objects.create(**entry)


def unseed_notifications(apps, schema_editor):
    Notification = apps.get_model('portal', 'Notification')
    Notification.objects.filter(user_id=14, type__in=[
        'TICKET_CREATED', 'TICKET_STATUS_CHANGED', 'TICKET_ASSIGNED',
        'COMMENT_ADDED', 'MENTION',
    ]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0009_notification'),
    ]

    operations = [
        migrations.RunPython(seed_notifications, reverse_code=unseed_notifications),
    ]
