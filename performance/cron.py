from django_cron import CronJobBase, Schedule
from django.core.management import call_command
from django.utils import timezone
from .models import NotificationPreference

class SendNotificationsCronJob(CronJobBase):
    RUN_EVERY_MINS = 60  # Run every hour

    schedule = Schedule(run_every_mins=RUN_EVERY_MINS)
    code = 'performance.send_notifications'  # Unique code for this cron job

    def do(self):
        # Get current time
        now = timezone.now()
        
        # Run for daily notifications
        call_command('send_notifications')
        
        # Run for weekly notifications (on Mondays)
        if now.weekday() == 0:  # Monday
            NotificationPreference.objects.filter(
                reminder_frequency='WEEKLY'
            ).update(last_notification_sent=now)
            
        # Run for monthly notifications (on 1st of month)
        if now.day == 1:
            NotificationPreference.objects.filter(
                reminder_frequency='MONTHLY'
            ).update(last_notification_sent=now) 