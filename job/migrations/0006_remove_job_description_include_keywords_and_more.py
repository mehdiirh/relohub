# Generated by Django 5.0.4 on 2024-04-26 17:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0005_job_description_include_keywords_and_more"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="job",
            name="description_include_keywords",
        ),
        migrations.RemoveField(
            model_name="job",
            name="found_via_search_keywords",
        ),
        migrations.AddField(
            model_name="job",
            name="points",
            field=models.PositiveIntegerField(default=0, verbose_name="points"),
        ),
    ]