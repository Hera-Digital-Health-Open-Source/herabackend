# Authored on 2022-01-03 06:40

import django.contrib.postgres.fields.hstore
from django.contrib.postgres.operations import HStoreExtension
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0010_postgres_hstore_extension'),
    ]

    operations = [
        HStoreExtension(),
    ]
