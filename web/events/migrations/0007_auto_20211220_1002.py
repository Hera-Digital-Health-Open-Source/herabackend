# Generated by Django 3.2.9 on 2021-12-20 10:02

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_alter_notificationevent_read_at'),
    ]

    operations = [
        migrations.AddField(
            model_name='notificationevent',
            name='notification_available_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notificationevent',
            name='notification_expires_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='notificationevent',
            name='push_notification_sent_at',
            field=models.DateTimeField(blank=True, default=None, null=True),
        ),
    ]
