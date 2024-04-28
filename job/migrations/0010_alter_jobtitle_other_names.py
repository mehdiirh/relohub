# Generated by Django 5.0.4 on 2024-04-27 17:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("job", "0009_jobtitle_other_names_jobtitle_parent"),
    ]

    operations = [
        migrations.AlterField(
            model_name="jobtitle",
            name="other_names",
            field=models.TextField(
                blank=True,
                help_text="semicolon separated names",
                max_length=512,
                null=True,
                verbose_name="other names",
            ),
        ),
    ]
