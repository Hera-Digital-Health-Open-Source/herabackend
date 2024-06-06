# Authored on 2022-01-03 06:40

import django.contrib.postgres.fields.hstore
from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0009_alter_notificationschedule_push_time_to_live'),
    ]

    operations = [
        HStoreExtension(),
    ]
