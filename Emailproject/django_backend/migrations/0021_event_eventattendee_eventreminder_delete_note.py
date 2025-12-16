import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('django_backend', '0020_merge_0019_meeting_0019_note'),
    ]

    operations = [
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('description', models.TextField(blank=True, null=True)),
                ('start_datetime', models.DateTimeField()),
                ('end_datetime', models.DateTimeField()),
                ('is_all_day', models.BooleanField(default=False)),
                ('location', models.CharField(blank=True, max_length=255, null=True)),
                ('url', models.URLField(blank=True, null=True)),
                ('color', models.CharField(default='blue', max_length=20)),
                ('repeat_rule', models.CharField(blank=True, max_length=255, null=True)),
                ('timezone', models.CharField(default='UTC', max_length=64)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_events', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventAttendee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('accepted', 'Accepted'), ('declined', 'Declined'), ('maybe', 'Maybe'), ('pending', 'Pending')], default='pending', max_length=20)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_backend.event')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EventReminder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('minutes_before', models.IntegerField()),
                ('event', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='django_backend.event')),
            ],
        ),
        
    ]
