# Generated by Django 4.0.3 on 2022-03-20 18:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_profile', '0006_userprofile_timezone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='language_code',
            field=models.CharField(choices=[('en', 'English'), ('tr', 'Turkish'), ('ar', 'Arabic'), ('ps', 'Pashto'), ('prs', 'Dari')], default='en', max_length=5),
        ),
    ]