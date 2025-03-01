"""
Custom decorators for the Performance Management System.

This module provides decorators for function-based views to enforce RBAC permissions.
"""

from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from functools import wraps
from .models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)
from . import permissions


def role_required(allowed_roles):
    """
    Decorator for views that checks if the user has one of the allowed roles.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            if request.user.is_superuser or request.user.role in allowed_roles:
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied("You don't have permission to access this page.")
        return _wrapped_view
    return decorator


def employee_required(view_func):
    """Decorator for views that require Employee role."""
    return role_required([CustomUser.EMPLOYEE])(view_func)


def manager_required(view_func):
    """Decorator for views that require Manager role."""
    return role_required([CustomUser.MANAGER])(view_func)


def hr_required(view_func):
    """Decorator for views that require HR role."""
    return role_required([CustomUser.HR])(view_func)


def approver_required(view_func):
    """Decorator for views that require Approver role."""
    return role_required([CustomUser.APPROVER])(view_func)


def admin_or_hr_required(view_func):
    """Decorator for views that require Admin or HR role."""
    return role_required([CustomUser.HR])(view_func)


def performance_agreement_permission(permission_type):
    """
    Decorator for views that checks if the user has the required permission for a performance agreement.
    
    Args:
        permission_type: One of 'view', 'create', 'update', 'delete', 'approve'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            # For create permission, no object is needed
            if permission_type == 'create':
                if permissions.can_create_performance_agreement(request.user):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create a performance agreement.")
            
            # For other permissions, get the object
            pk = kwargs.get('pk')
            if not pk:
                raise ValueError("Performance agreement ID (pk) is required.")
            
            agreement = get_object_or_404(PerformanceAgreement, pk=pk)
            
            if permission_type == 'view' and permissions.can_view_performance_agreement(request.user, agreement):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'update' and permissions.can_update_performance_agreement(request.user, agreement):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'delete' and permissions.can_delete_performance_agreement(request.user, agreement):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'approve' and permissions.can_approve_performance_agreement(request.user, agreement):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"You don't have permission to {permission_type} this performance agreement.")
        
        return _wrapped_view
    return decorator


def midyear_review_permission(permission_type):
    """
    Decorator for views that checks if the user has the required permission for a mid-year review.
    
    Args:
        permission_type: One of 'view', 'create', 'update', 'delete'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            # For create permission with performance_agreement_id
            if permission_type == 'create' and 'performance_agreement_id' in kwargs:
                performance_agreement = get_object_or_404(
                    PerformanceAgreement, pk=kwargs['performance_agreement_id']
                )
                if permissions.can_create_midyear_review(request.user, performance_agreement):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create a mid-year review.")
            
            # For other permissions, get the object
            pk = kwargs.get('pk')
            if not pk:
                raise ValueError("Mid-year review ID (pk) is required.")
            
            review = get_object_or_404(MidYearReview, pk=pk)
            
            if permission_type == 'view' and permissions.can_view_midyear_review(request.user, review):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'update' and permissions.can_update_midyear_review(request.user, review):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'delete' and permissions.can_delete_midyear_review(request.user, review):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"You don't have permission to {permission_type} this mid-year review.")
        
        return _wrapped_view
    return decorator


def final_review_permission(permission_type):
    """
    Decorator for views that checks if the user has the required permission for a final review.
    
    Args:
        permission_type: One of 'view', 'create', 'update', 'delete'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            # For create permission with performance_agreement_id
            if permission_type == 'create' and 'performance_agreement_id' in kwargs:
                performance_agreement = get_object_or_404(
                    PerformanceAgreement, pk=kwargs['performance_agreement_id']
                )
                if permissions.can_create_final_review(request.user, performance_agreement):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create a final review.")
            
            # For other permissions, get the object
            pk = kwargs.get('pk')
            if not pk:
                raise ValueError("Final review ID (pk) is required.")
            
            review = get_object_or_404(FinalReview, pk=pk)
            
            if permission_type == 'view' and permissions.can_view_final_review(request.user, review):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'update' and permissions.can_update_final_review(request.user, review):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'delete' and permissions.can_delete_final_review(request.user, review):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"You don't have permission to {permission_type} this final review.")
        
        return _wrapped_view
    return decorator


def improvement_plan_permission(permission_type):
    """
    Decorator for views that checks if the user has the required permission for an improvement plan.
    
    Args:
        permission_type: One of 'view', 'create', 'update', 'delete'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            # For create permission with employee_id
            if permission_type == 'create' and 'employee_id' in kwargs:
                employee = get_object_or_404(CustomUser, pk=kwargs['employee_id'])
                if permissions.can_create_improvement_plan(request.user, employee):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create an improvement plan.")
            elif permission_type == 'create':
                if permissions.can_create_improvement_plan(request.user):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create an improvement plan.")
            
            # For other permissions, get the object
            pk = kwargs.get('pk')
            if not pk:
                raise ValueError("Improvement plan ID (pk) is required.")
            
            plan = get_object_or_404(ImprovementPlan, pk=pk)
            
            if permission_type == 'view' and permissions.can_view_improvement_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'update' and permissions.can_update_improvement_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'delete' and permissions.can_delete_improvement_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"You don't have permission to {permission_type} this improvement plan.")
        
        return _wrapped_view
    return decorator


def development_plan_permission(permission_type):
    """
    Decorator for views that checks if the user has the required permission for a personal development plan.
    
    Args:
        permission_type: One of 'view', 'create', 'update', 'delete'
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return user_passes_test(lambda u: u.is_authenticated)(view_func)(request, *args, **kwargs)
            
            # For create permission, no object is needed
            if permission_type == 'create':
                if permissions.can_create_development_plan(request.user):
                    return view_func(request, *args, **kwargs)
                raise PermissionDenied("You don't have permission to create a personal development plan.")
            
            # For other permissions, get the object
            pk = kwargs.get('pk')
            if not pk:
                raise ValueError("Personal development plan ID (pk) is required.")
            
            plan = get_object_or_404(PersonalDevelopmentPlan, pk=pk)
            
            if permission_type == 'view' and permissions.can_view_development_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'update' and permissions.can_update_development_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            elif permission_type == 'delete' and permissions.can_delete_development_plan(request.user, plan):
                return view_func(request, *args, **kwargs)
            
            raise PermissionDenied(f"You don't have permission to {permission_type} this personal development plan.")
        
        return _wrapped_view
    return decorator 