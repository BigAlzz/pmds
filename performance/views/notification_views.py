"""
Notification views for the performance app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.http import JsonResponse

from ..models import (
    Notification,
    NotificationPreference
)


@login_required
def notification_list(request):
    """
    Display user's notifications and preferences.
    """
    notifications = request.user.notifications.all()
    paginator = Paginator(notifications, 10)  # Show 10 notifications per page
    page = request.GET.get('page')
    notifications = paginator.get_page(page)
    
    return render(request, 'performance/notifications.html', {
        'notifications': notifications,
    })


@login_required
def notification_preferences(request):
    """
    Display and update user's notification preferences.
    """
    if request.method == 'POST':
        prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
        
        # Update preferences from form data
        prefs.email_notifications = request.POST.get('email_notifications') == 'on'
        prefs.review_reminders = request.POST.get('review_reminders') == 'on'
        prefs.plan_updates = request.POST.get('plan_updates') == 'on'
        prefs.feedback_notifications = request.POST.get('feedback_notifications') == 'on'
        prefs.reminder_frequency = request.POST.get('reminder_frequency', 'WEEKLY')
        prefs.save()
        
        messages.success(request, 'Notification preferences updated successfully.')
        return redirect('performance:notification_list')
    
    # Get or create user's preferences
    prefs, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    return render(request, 'performance/notification_preferences.html', {
        'preferences': prefs
    })


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    """
    Mark a single notification as read.
    """
    try:
        notification = request.user.notifications.get(id=notification_id)
        notification.read_at = timezone.now()
        notification.save()
        return redirect('performance:notification_list')
    except Notification.DoesNotExist:
        messages.error(request, 'Notification not found.')
        return redirect('performance:notification_list')


@login_required
@require_POST
def mark_all_notifications_read(request):
    """
    Mark all notifications as read.
    """
    request.user.notifications.filter(read_at__isnull=True).update(read_at=timezone.now())
    messages.success(request, 'All notifications marked as read.')
    return redirect('performance:notification_list')


@login_required
def notification_count(request):
    """
    Return the count of unread notifications (for AJAX requests).
    """
    count = request.user.notifications.filter(read_at__isnull=True).count()
    return JsonResponse({'count': count}) 