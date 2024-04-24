import os


def env_literal(key, _default=None):
    value = os.environ.get(key, _default)
    if value != _default:
        return eval(str(value))
    return value


CELERY_BROKER_URL = os.environ.get("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_TIMEZONE = os.environ.get("TIME_ZONE")

CELERY_BEAT_SCHEDULE = {}

# commands to run!
# celery -A celery_app multi start periodic celery -B -Q:1 periodic_queue -Q:2 celery -c:1 2 -c:2 5 -l INFO
