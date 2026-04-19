from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('portal', '0005_remove_new_status'),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketHistory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ticket_id', models.IntegerField(db_index=True)),
                ('user_id', models.IntegerField(blank=True, null=True)),
                ('action', models.CharField(max_length=100)),
                ('field_name', models.CharField(blank=True, max_length=100, null=True)),
                ('old_value', models.TextField(blank=True, null=True)),
                ('new_value', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'db_table': 'portal_ticket_history',
                'ordering': ['-created_at'],
            },
        ),
    ]
