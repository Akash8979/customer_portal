from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0008_comment_is_internal'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id',         models.AutoField(primary_key=True, serialize=False)),
                ('user_id',    models.IntegerField(db_index=True)),
                ('tenant_id',  models.CharField(blank=True, default='', max_length=100)),
                ('type',       models.CharField(max_length=40, choices=[
                    ('TICKET_CREATED',        'Ticket Created'),
                    ('TICKET_STATUS_CHANGED', 'Ticket Status Changed'),
                    ('TICKET_ASSIGNED',       'Ticket Assigned'),
                    ('TICKET_ESCALATED',      'Ticket Escalated'),
                    ('COMMENT_ADDED',         'Comment Added'),
                    ('MENTION',               'Mention'),
                ])),
                ('title',      models.CharField(max_length=255)),
                ('message',    models.TextField()),
                ('link',       models.CharField(blank=True, default='', max_length=500)),
                ('is_read',    models.BooleanField(default=False, db_index=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
            ],
            options={
                'db_table': 'portal_notification',
                'ordering': ['-created_at'],
            },
        ),
    ]
