"""
Role-Based Access Control (RBAC) permissions for the Performance Management System.

This module provides permission checking functions for different user roles:
- Employee: Regular user who can manage their own records
- Manager/Supervisor: Can manage records of their subordinates
- HR: Can view all records and manage system settings
- Approver: Can approve/reject performance agreements and reviews
"""

from .models import CustomUser, PerformanceAgreement, MidYearReview, FinalReview, ImprovementPlan, PersonalDevelopmentPlan


def is_employee(user):
    """Check if user has Employee role."""
    return user.is_authenticated and user.role == CustomUser.EMPLOYEE


def is_manager(user):
    """Check if user has Manager role."""
    return user.is_authenticated and user.role == CustomUser.MANAGER


def is_hr(user):
    """Check if user has HR role."""
    return user.is_authenticated and user.role == CustomUser.HR


def is_approver(user):
    """Check if user has Approver role."""
    return user.is_authenticated and user.role == CustomUser.APPROVER


def is_admin(user):
    """Check if user is a superuser/admin."""
    return user.is_authenticated and user.is_superuser


# Performance Agreement Permissions
def can_view_performance_agreement(user, agreement):
    """Check if user can view a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can view all agreements
    if user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]:
        return True
    
    # Employee can view their own agreements
    if agreement.employee == user:
        return True
    
    # Manager can view agreements of their subordinates
    if user.role == CustomUser.MANAGER and agreement.employee in user.subordinates.all():
        return True
    
    # Supervisor can view agreements they supervise
    if agreement.supervisor == user:
        return True
    
    return False


def can_create_performance_agreement(user):
    """Check if user can create a performance agreement."""
    # Only employees, managers, and HR can create agreements
    return user.is_authenticated and user.role in [CustomUser.EMPLOYEE, CustomUser.MANAGER, CustomUser.HR]


def can_update_performance_agreement(user, agreement):
    """Check if user can update a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin can update any agreement
    if user.is_superuser:
        return True
    
    # HR can update any agreement for verification and sending back with comments
    if user.role == CustomUser.HR:
        return True
    
    # Employee can update their own agreements if in DRAFT status
    if agreement.employee == user and agreement.status == PerformanceAgreement.DRAFT:
        return True
    
    # Manager can update agreements of their subordinates if in appropriate status
    if (user.role == CustomUser.MANAGER and 
        agreement.employee in user.subordinates.all() and
        agreement.status in [PerformanceAgreement.DRAFT, PerformanceAgreement.PENDING_MANAGER_APPROVAL]):
        return True
    
    # Supervisor can update agreements they supervise if in appropriate status
    if (agreement.supervisor == user and 
        agreement.status in [PerformanceAgreement.PENDING_SUPERVISOR_RATING, 
                            PerformanceAgreement.PENDING_SUPERVISOR_SIGNOFF]):
        return True
    
    return False


def can_delete_performance_agreement(user, agreement):
    """Check if user can delete a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can delete any agreement that is not in COMPLETED status
    if user.is_superuser and agreement.status != PerformanceAgreement.COMPLETED:
        return True
    
    # HR can delete agreements that are not in COMPLETED status
    if user.role == CustomUser.HR and agreement.status != PerformanceAgreement.COMPLETED:
        return True
    
    # Employee can delete their own agreements if in DRAFT status
    if agreement.employee == user and agreement.status == PerformanceAgreement.DRAFT:
        return True
    
    return False


def can_approve_performance_agreement(user, agreement):
    """Check if user can approve a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can approve any agreement in the appropriate status
    if (user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]) and \
       agreement.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL:
        return True
    
    # Manager can approve agreements of their subordinates if in appropriate status
    if (user.role == CustomUser.MANAGER and 
        agreement.employee in user.subordinates.all() and
        agreement.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL):
        return True
    
    return False


# Mid-Year Review Permissions
def can_view_midyear_review(user, review):
    """Check if user can view a mid-year review."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can view all reviews
    if user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]:
        return True
    
    # Employee can view their own reviews
    if review.performance_agreement.employee == user:
        return True
    
    # Manager can view reviews of their subordinates
    if (user.role == CustomUser.MANAGER and 
        review.performance_agreement.employee in user.subordinates.all()):
        return True
    
    # Supervisor can view reviews they supervise
    if review.performance_agreement.supervisor == user:
        return True
    
    return False


def can_create_midyear_review(user, performance_agreement):
    """Check if user can create a mid-year review for a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can create reviews for any agreement
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can create their own reviews
    if performance_agreement.employee == user:
        return True
    
    # Supervisor can create reviews for agreements they supervise
    if performance_agreement.supervisor == user:
        return True
    
    return False


def can_update_midyear_review(user, review):
    """Check if user can update a mid-year review."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can update any review
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can update their own reviews if in appropriate status
    if (review.performance_agreement.employee == user and 
        review.status in ['DRAFT', 'PENDING_EMPLOYEE_RATING']):
        return True
    
    # Supervisor can update reviews they supervise if in appropriate status
    if (review.performance_agreement.supervisor == user and 
        review.status in ['PENDING_SUPERVISOR_RATING', 'PENDING_SUPERVISOR_SIGNOFF']):
        return True
    
    return False


def can_delete_midyear_review(user, review):
    """Check if user can delete a mid-year review."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can delete any review
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can delete their own reviews if in DRAFT status
    if review.performance_agreement.employee == user and review.status == 'DRAFT':
        return True
    
    return False


# Final Review Permissions
def can_view_final_review(user, review):
    """Check if user can view a final review."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can view all reviews
    if user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]:
        return True
    
    # Employee can view their own reviews
    if review.performance_agreement.employee == user:
        return True
    
    # Manager can view reviews of their subordinates
    if (user.role == CustomUser.MANAGER and 
        review.performance_agreement.employee in user.subordinates.all()):
        return True
    
    # Supervisor can view reviews they supervise
    if review.performance_agreement.supervisor == user:
        return True
    
    return False


def can_create_final_review(user, performance_agreement):
    """Check if user can create a final review for a performance agreement."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can create reviews for any agreement
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can create their own reviews
    if performance_agreement.employee == user:
        return True
    
    # Supervisor can create reviews for agreements they supervise
    if performance_agreement.supervisor == user:
        return True
    
    return False


def can_update_final_review(user, review):
    """Check if user can update a final review."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can update any review
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can update their own reviews if in appropriate status
    if (review.performance_agreement.employee == user and 
        review.status in ['DRAFT', 'PENDING_EMPLOYEE_RATING']):
        return True
    
    # Supervisor can update reviews they supervise if in appropriate status
    if (review.performance_agreement.supervisor == user and 
        review.status in ['PENDING_SUPERVISOR_RATING', 'PENDING_SUPERVISOR_SIGNOFF']):
        return True
    
    return False


def can_delete_final_review(user, review):
    """Check if user can delete a final review."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can delete any review
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can delete their own reviews if in DRAFT status
    if review.performance_agreement.employee == user and review.status == 'DRAFT':
        return True
    
    return False


# Improvement Plan Permissions
def can_view_improvement_plan(user, plan):
    """Check if user can view an improvement plan."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can view all plans
    if user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]:
        return True
    
    # Employee can view their own plans
    if plan.employee == user:
        return True
    
    # Manager can view plans of their subordinates
    if user.role == CustomUser.MANAGER and plan.employee in user.subordinates.all():
        return True
    
    # Supervisor can view plans they supervise
    if plan.supervisor == user:
        return True
    
    return False


def can_create_improvement_plan(user, employee=None):
    """Check if user can create an improvement plan."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can create plans for any employee
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Supervisor can create plans for employees they supervise
    if user.role == CustomUser.MANAGER and employee and employee in user.subordinates.all():
        return True
    
    return False


def can_update_improvement_plan(user, plan):
    """Check if user can update an improvement plan."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can update any plan
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Supervisor can update plans they supervise
    if plan.supervisor == user:
        return True
    
    return False


def can_delete_improvement_plan(user, plan):
    """Check if user can delete an improvement plan."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can delete any plan
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Supervisor can delete plans they supervise if in DRAFT status
    if plan.supervisor == user and plan.status == 'DRAFT':
        return True
    
    return False


# Personal Development Plan Permissions
def can_view_development_plan(user, plan):
    """Check if user can view a personal development plan."""
    if not user.is_authenticated:
        return False
    
    # Admin, HR, and Approvers can view all plans
    if user.is_superuser or user.role in [CustomUser.HR, CustomUser.APPROVER]:
        return True
    
    # Employee can view their own plans
    if plan.employee == user:
        return True
    
    # Manager can view plans of their subordinates
    if user.role == CustomUser.MANAGER and plan.employee in user.subordinates.all():
        return True
    
    return False


def can_create_development_plan(user):
    """Check if user can create a personal development plan."""
    # Any authenticated user can create their own development plan
    return user.is_authenticated


def can_update_development_plan(user, plan):
    """Check if user can update a personal development plan."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can update any plan
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can update their own plans
    if plan.employee == user:
        return True
    
    return False


def can_delete_development_plan(user, plan):
    """Check if user can delete a personal development plan."""
    if not user.is_authenticated:
        return False
    
    # Admin and HR can delete any plan
    if user.is_superuser or user.role == CustomUser.HR:
        return True
    
    # Employee can delete their own plans
    if plan.employee == user:
        return True
    
    return False 