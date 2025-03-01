"""
Context processors for the Performance Management System.

This module provides context processors to make role information available in templates.
"""

from .models import CustomUser


def user_roles(request):
    """
    Add user role information to the template context.
    """
    context = {
        'is_employee': False,
        'is_manager': False,
        'is_hr': False,
        'is_approver': False,
        'is_admin': False,
        'user_role': None,
    }
    
    if request.user.is_authenticated:
        context['is_employee'] = request.user.role == CustomUser.EMPLOYEE
        context['is_manager'] = request.user.role == CustomUser.MANAGER
        context['is_hr'] = request.user.role == CustomUser.HR
        context['is_approver'] = request.user.role == CustomUser.APPROVER
        context['is_admin'] = request.user.is_superuser
        context['user_role'] = request.user.role
    
    return context 