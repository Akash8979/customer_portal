from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0007_audit_log'),
    ]

    operations = [
        migrations.AddField(
            model_name='comment',
            name='is_internal',
            field=models.BooleanField(default=False),
        ),
    ]
