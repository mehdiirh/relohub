# Generated by Django 5.0.4 on 2024-04-24 21:53

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HTTPProxy",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="is active"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated at"),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True, default=dict, null=True, verbose_name="metadata"
                    ),
                ),
                ("host", models.CharField(max_length=128, verbose_name="host")),
                ("port", models.IntegerField(verbose_name="port")),
                (
                    "username",
                    models.CharField(
                        blank=True, max_length=64, null=True, verbose_name="username"
                    ),
                ),
                (
                    "password",
                    models.CharField(
                        blank=True, max_length=64, null=True, verbose_name="password"
                    ),
                ),
            ],
            options={
                "verbose_name": "HTTP Proxy",
                "verbose_name_plural": "HTTP Proxies",
            },
        ),
        migrations.CreateModel(
            name="LinkedinAccount",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="is active"),
                ),
                (
                    "created_at",
                    models.DateTimeField(auto_now_add=True, verbose_name="created at"),
                ),
                (
                    "updated_at",
                    models.DateTimeField(auto_now=True, verbose_name="updated at"),
                ),
                (
                    "metadata",
                    models.JSONField(
                        blank=True, default=dict, null=True, verbose_name="metadata"
                    ),
                ),
                (
                    "username",
                    models.CharField(
                        db_index=True,
                        max_length=128,
                        unique=True,
                        verbose_name="username",
                    ),
                ),
                ("password", models.CharField(max_length=256, verbose_name="password")),
                (
                    "cookies",
                    models.JSONField(blank=True, null=True, verbose_name="cookies"),
                ),
                (
                    "proxy",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="linkedin.httpproxy",
                        verbose_name="proxy",
                    ),
                ),
            ],
            options={
                "verbose_name": "Linkedin Account",
                "verbose_name_plural": "Linkedin Accounts",
            },
        ),
    ]
