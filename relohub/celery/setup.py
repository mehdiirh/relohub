from __future__ import absolute_import, unicode_literals

import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "relohub.settings")
app = Celery("relohub")
app.config_from_object("django.conf:settings", namespace="CELERY_")
app.autodiscover_tasks()
