"""
Celery configuration for Lead Management System.

This module configures Celery for background task processing,
including follow-up reminders, lead scoring updates, and periodic tasks.
"""

import os
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'server.settings')

# Only configure Celery if it's enabled
if getattr(settings, 'CELERY_ENABLED', False):
    from celery import Celery
    
    app = Celery('lead_management')
    
    # Using a string here means the worker doesn't have to serialize
    # the configuration object to child processes.
    app.config_from_object('django.conf:settings', namespace='CELERY')
    
    # Load task modules from all registered Django apps.
    app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
    
    # Configure periodic tasks
    app.conf.beat_schedule = {
        'update-lead-scores-daily': {
            'task': 'leads.tasks.update_lead_scores_task',
            'schedule': 86400.0,  # 24 hours
        },
        'send-follow-up-reminders': {
            'task': 'leads.tasks.send_follow_up_reminders_task',
            'schedule': 3600.0,  # 1 hour
        },
        'check-snooze-expiration': {
            'task': 'leads.tasks.check_snooze_expiration_task',
            'schedule': 1800.0,  # 30 minutes
        },
        'update-agent-performance': {
            'task': 'leads.tasks.update_agent_performance_task',
            'schedule': 3600.0,  # 1 hour
        },
    }
    
    @app.task(bind=True)
    def debug_task(self):
        """Debug task for testing Celery."""
        print(f'Request: {self.request!r}')
else:
    # Create a dummy app when Celery is disabled
    app = None 