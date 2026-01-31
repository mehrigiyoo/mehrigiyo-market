# ============================================
# FILE: config/celery.py - TO'G'RI VERSIYA
# ============================================

from celery import Celery
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


#  CELERY BEAT SCHEDULE
app.conf.beat_schedule = {
    'check-missed-calls-every-30-seconds': {
        'task': 'call.tasks.check_missed_calls',
        'schedule': 30.0,
    },
}

app.conf.timezone = 'UTC'


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')