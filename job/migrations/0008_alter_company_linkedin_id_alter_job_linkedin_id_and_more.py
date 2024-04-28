# Generated by Django 5.0.4 on 2024-04-26 18:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0007_jobskill_job_job_skills"),
    ]

    operations = [
        migrations.AlterField(
            model_name="company",
            name="linkedin_id",
            field=models.CharField(
                db_index=True, max_length=32, unique=True, verbose_name="linkedin ID"
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="linkedin_id",
            field=models.CharField(
                db_index=True, max_length=32, unique=True, verbose_name="linkedin ID"
            ),
        ),
        migrations.AlterField(
            model_name="jobskill",
            name="linkedin_id",
            field=models.CharField(
                db_index=True, max_length=32, unique=True, verbose_name="linkedin ID"
            ),
        ),
        migrations.AlterField(
            model_name="jobtitle",
            name="linkedin_id",
            field=models.CharField(
                db_index=True, max_length=32, unique=True, verbose_name="linkedin ID"
            ),
        ),
    ]