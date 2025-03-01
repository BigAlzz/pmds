"""
Custom mixins for the Performance Management System.

This module provides mixins for class-based views to enforce RBAC permissions.
"""

from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import (
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)
from . import permissions


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to require specific user roles."""
    allowed_roles = []

    def test_func(self):
        """Test if the user has one of the allowed roles."""
        if self.request.user.is_superuser:
            return True
        return self.request.user.role in self.allowed_roles


class PerformanceAgreementPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to enforce permissions for performance agreement views."""
    permission_type = 'view'  # Default permission type

    def get_object(self, queryset=None):
        """Get the object and store it for permission checking."""
        obj = super().get_object(queryset)
        self.object = obj
        return obj

    def test_func(self):
        """Test if the user has the required permission for the object."""
        if not hasattr(self, 'object'):
            # For list views or create views
            if self.permission_type == 'create':
                return permissions.can_create_performance_agreement(self.request.user)
            return True

        if self.permission_type == 'view':
            return permissions.can_view_performance_agreement(self.request.user, self.object)
        elif self.permission_type == 'update':
            return permissions.can_update_performance_agreement(self.request.user, self.object)
        elif self.permission_type == 'delete':
            return permissions.can_delete_performance_agreement(self.request.user, self.object)
        elif self.permission_type == 'approve':
            return permissions.can_approve_performance_agreement(self.request.user, self.object)
        
        return False


class MidYearReviewPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to enforce permissions for mid-year review views."""
    permission_type = 'view'  # Default permission type

    def get_object(self, queryset=None):
        """Get the object and store it for permission checking."""
        obj = super().get_object(queryset)
        self.object = obj
        return obj

    def test_func(self):
        """Test if the user has the required permission for the object."""
        if not hasattr(self, 'object'):
            # For list views or create views with performance_agreement_id in kwargs
            if self.permission_type == 'create' and 'performance_agreement_id' in self.kwargs:
                performance_agreement = get_object_or_404(
                    PerformanceAgreement, pk=self.kwargs['performance_agreement_id']
                )
                return permissions.can_create_midyear_review(self.request.user, performance_agreement)
            return True

        if self.permission_type == 'view':
            return permissions.can_view_midyear_review(self.request.user, self.object)
        elif self.permission_type == 'update':
            return permissions.can_update_midyear_review(self.request.user, self.object)
        elif self.permission_type == 'delete':
            return permissions.can_delete_midyear_review(self.request.user, self.object)
        
        return False


class FinalReviewPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to enforce permissions for final review views."""
    permission_type = 'view'  # Default permission type

    def get_object(self, queryset=None):
        """Get the object and store it for permission checking."""
        obj = super().get_object(queryset)
        self.object = obj
        return obj

    def test_func(self):
        """Test if the user has the required permission for the object."""
        if not hasattr(self, 'object'):
            # For list views or create views with performance_agreement_id in kwargs
            if self.permission_type == 'create' and 'performance_agreement_id' in self.kwargs:
                performance_agreement = get_object_or_404(
                    PerformanceAgreement, pk=self.kwargs['performance_agreement_id']
                )
                return permissions.can_create_final_review(self.request.user, performance_agreement)
            return True

        if self.permission_type == 'view':
            return permissions.can_view_final_review(self.request.user, self.object)
        elif self.permission_type == 'update':
            return permissions.can_update_final_review(self.request.user, self.object)
        elif self.permission_type == 'delete':
            return permissions.can_delete_final_review(self.request.user, self.object)
        
        return False


class ImprovementPlanPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to enforce permissions for improvement plan views."""
    permission_type = 'view'  # Default permission type

    def get_object(self, queryset=None):
        """Get the object and store it for permission checking."""
        obj = super().get_object(queryset)
        self.object = obj
        return obj

    def test_func(self):
        """Test if the user has the required permission for the object."""
        if not hasattr(self, 'object'):
            # For list views or create views with employee_id in kwargs
            if self.permission_type == 'create' and 'employee_id' in self.kwargs:
                from .models import CustomUser
                employee = get_object_or_404(CustomUser, pk=self.kwargs['employee_id'])
                return permissions.can_create_improvement_plan(self.request.user, employee)
            elif self.permission_type == 'create':
                return permissions.can_create_improvement_plan(self.request.user)
            return True

        if self.permission_type == 'view':
            return permissions.can_view_improvement_plan(self.request.user, self.object)
        elif self.permission_type == 'update':
            return permissions.can_update_improvement_plan(self.request.user, self.object)
        elif self.permission_type == 'delete':
            return permissions.can_delete_improvement_plan(self.request.user, self.object)
        
        return False


class DevelopmentPlanPermissionMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Mixin to enforce permissions for personal development plan views."""
    permission_type = 'view'  # Default permission type

    def get_object(self, queryset=None):
        """Get the object and store it for permission checking."""
        obj = super().get_object(queryset)
        self.object = obj
        return obj

    def test_func(self):
        """Test if the user has the required permission for the object."""
        if not hasattr(self, 'object'):
            # For list views or create views
            if self.permission_type == 'create':
                return permissions.can_create_development_plan(self.request.user)
            return True

        if self.permission_type == 'view':
            return permissions.can_view_development_plan(self.request.user, self.object)
        elif self.permission_type == 'update':
            return permissions.can_update_development_plan(self.request.user, self.object)
        elif self.permission_type == 'delete':
            return permissions.can_delete_development_plan(self.request.user, self.object)
        
        return False 