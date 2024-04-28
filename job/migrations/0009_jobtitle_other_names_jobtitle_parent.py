# Generated by Django 5.0.4 on 2024-04-27 16:18

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0008_alter_company_linkedin_id_alter_job_linkedin_id_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="jobtitle",
            name="other_names",
            field=models.CharField(
                blank=True,
                help_text="semicolon separated names",
                max_length=512,
                null=True,
                verbose_name="other names",
            ),
        ),
        migrations.AddField(
            model_name="jobtitle",
            name="parent",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="children",
                to="job.jobtitle",
                verbose_name="parent",
            ),
        ),
    ]