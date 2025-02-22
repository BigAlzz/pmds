"""
Notification utility functions for the performance management system.
"""
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, Notification, NotificationPreference

def notify_user(user, notification_type, title, message, related_object_type=None, related_object_id=None):
    """Helper function to create and send notifications"""
    notification = Notification.objects.create(
        recipient=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_object_type=related_object_type,
        related_object_id=related_object_id
    )
    
    # Send email if enabled for the user
    if notification.recipient.notification_preferences.email_notifications:
        try:
            send_mail(
                subject=notification.title,
                message=notification.message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[notification.recipient.email],
                fail_silently=False,
            )
            notification.email_sent = True
            notification.save()
        except Exception as e:
            # Log the error but don't raise it
            print(f"Failed to send email notification: {str(e)}")
    
    return notification

def notify_manager(employee, notification_type, title, message, related_object_type=None, related_object_id=None):
    """Helper function to notify a user's manager"""
    if employee.manager:
        return notify_user(
            user=employee.manager,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_type=related_object_type,
            related_object_id=related_object_id
        )
    return None 