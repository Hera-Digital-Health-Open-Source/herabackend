# Generated by Django 4.0.4 on 2023-11-23 11:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Concept',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=255, unique=True)),
                ('name_ar', models.CharField(max_length=255, unique=True)),
                ('name_tr', models.CharField(max_length=255, unique=True)),
                ('name_prs', models.CharField(max_length=255, unique=True)),
                ('name_pus', models.CharField(max_length=255, unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='Section',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=255, unique=True)),
                ('name_ar', models.CharField(max_length=255, unique=True)),
                ('name_tr', models.CharField(max_length=255, unique=True)),
                ('name_prs', models.CharField(max_length=255, unique=True)),
                ('name_pus', models.CharField(max_length=255, unique=True)),
                ('concept', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='concepts.concept')),
            ],
        ),
        migrations.CreateModel(
            name='Article',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title_en', models.CharField(max_length=255, unique=True)),
                ('content_en', models.TextField()),
                ('title_ar', models.CharField(max_length=255, unique=True)),
                ('content_ar', models.TextField()),
                ('title_tr', models.CharField(max_length=255, unique=True)),
                ('content_tr', models.TextField()),
                ('title_prs', models.CharField(max_length=255, unique=True)),
                ('content_prs', models.TextField()),
                ('title_pus', models.CharField(max_length=255, unique=True)),
                ('content_pus', models.TextField()),
                ('section', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='concepts.section')),
            ],
        ),
    ]