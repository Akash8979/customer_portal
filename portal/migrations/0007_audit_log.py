from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0006_ticket_history'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id',            models.AutoField(primary_key=True, serialize=False)),
                ('user_id',       models.CharField(max_length=100)),
                ('user_name',     models.CharField(blank=True, max_length=255)),
                ('user_role',     models.CharField(blank=True, max_length=50)),
                ('tenant_id',     models.CharField(blank=True, max_length=100)),
                ('action',        models.CharField(max_length=100)),
                ('resource_type', models.CharField(blank=True, max_length=50)),
                ('resource_id',   models.CharField(blank=True, max_length=100)),
                ('detail',        models.JSONField(blank=True, default=dict)),
                ('ip_address',    models.CharField(blank=True, max_length=50)),
                ('created_at',    models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'portal_audit_log',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['user_id'], name='audit_user_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['action'], name='audit_action_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['resource_type'], name='audit_rtype_idx'),
        ),
        migrations.AddIndex(
            model_name='auditlog',
            index=models.Index(fields=['created_at'], name='audit_created_idx'),
        ),
    ]
