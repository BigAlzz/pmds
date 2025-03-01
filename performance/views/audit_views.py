from django.shortcuts import render
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta

from ..models import AuditTrail, CustomUser
from ..permissions import is_hr, is_admin


@login_required
def audit_trail_list(request):
    """
    View for listing audit trail entries.
    Only HR and Admin users can access this view.
    """
    if not (is_hr(request.user) or is_admin(request.user)):
        return render(request, '403.html', status=403)
    
    # Get filter parameters
    user_id = request.GET.get('user_id')
    action_type = request.GET.get('action_type')
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')
    search_query = request.GET.get('q')
    
    # Start with all audit trail entries
    audit_entries = AuditTrail.objects.all().order_by('-timestamp')
    
    # Apply filters
    if user_id:
        audit_entries = audit_entries.filter(user_id=user_id)
    
    if action_type:
        audit_entries = audit_entries.filter(action=action_type)
    
    if date_from:
        audit_entries = audit_entries.filter(timestamp__gte=date_from)
    
    if date_to:
        # Add one day to include the end date
        end_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date() + timedelta(days=1)
        audit_entries = audit_entries.filter(timestamp__lt=end_date)
    
    if search_query:
        audit_entries = audit_entries.filter(
            Q(details__icontains=search_query) |
            Q(object_repr__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(audit_entries, 20)  # Show 20 entries per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all users for the filter dropdown
    users = CustomUser.objects.all().order_by('first_name', 'last_name')
    
    # Get all action types for the filter dropdown
    action_types = [action[0] for action in AuditTrail.ACTION_CHOICES]
    
    context = {
        'page_obj': page_obj,
        'users': users,
        'action_types': action_types,
        'filters': {
            'user_id': user_id,
            'action_type': action_type,
            'date_from': date_from,
            'date_to': date_to,
            'q': search_query,
        }
    }
    
    return render(request, 'performance/audit_trail_list.html', context)


@login_required
def audit_trail_detail(request, pk):
    """
    View for showing details of an audit trail entry.
    Only HR and Admin users can access this view.
    """
    if not (is_hr(request.user) or is_admin(request.user)):
        return render(request, '403.html', status=403)
    
    audit_entry = AuditTrail.objects.get(pk=pk)
    
    return render(request, 'performance/audit_trail_detail.html', {
        'audit_entry': audit_entry,
    }) 