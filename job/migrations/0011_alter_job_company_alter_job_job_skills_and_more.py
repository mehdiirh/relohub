# Generated by Django 5.0.4 on 2024-04-30 13:49

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0010_alter_jobtitle_other_names"),
    ]

    operations = [
        migrations.AlterField(
            model_name="job",
            name="company",
            field=models.ForeignKey(
                blank=True,
                limit_choices_to={"is_active": True},
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to="job.company",
                verbose_name="company",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="job_skills",
            field=models.ManyToManyField(
                limit_choices_to={"is_active": True},
                related_name="jobs",
                to="job.jobskill",
                verbose_name="job skills",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="job_titles",
            field=models.ManyToManyField(
                limit_choices_to={"is_active": True, "parent__isnull": True},
                related_name="jobs",
                to="job.jobtitle",
                verbose_name="job titles",
            ),
        ),
        migrations.AlterField(
            model_name="job",
            name="location",
            field=models.ForeignKey(
                limit_choices_to={"is_active": True},
                on_delete=django.db.models.deletion.CASCADE,
                related_name="jobs",
                to="job.joblocation",
                verbose_name="location",
            ),
        ),
    ]