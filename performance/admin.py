from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    Feedback,
    AuditLog
)

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'employee_id', 'role', 'department', 'job_title')
    list_filter = ('role', 'department')
    fieldsets = UserAdmin.fieldsets + (
        ('Employee Information', {'fields': ('employee_id', 'role', 'department', 'job_title', 'manager')}),
    )

@admin.register(PerformanceAgreement)
class PerformanceAgreementAdmin(admin.ModelAdmin):
    list_display = ('employee', 'agreement_date', 'status')
    list_filter = ('status', 'agreement_date')
    search_fields = ('employee__username', 'employee__first_name', 'employee__last_name')

@admin.register(MidYearReview)
class MidYearReviewAdmin(admin.ModelAdmin):
    list_display = ('performance_agreement', 'final_rating', 'review_date')
    list_filter = ('final_rating', 'review_date')
    search_fields = ('performance_agreement__employee__username',)

@admin.register(ImprovementPlan)
class ImprovementPlanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'status', 'approved_by', 'approval_date')
    list_filter = ('status', 'approval_date')
    search_fields = ('employee__username', 'area_for_development')

@admin.register(PersonalDevelopmentPlan)
class PersonalDevelopmentPlanAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'progress')
    list_filter = ('start_date', 'end_date')
    search_fields = ('employee__username', 'competency_gap')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('employee', 'anonymous', 'submitted_at')
    list_filter = ('anonymous', 'submitted_at')
    search_fields = ('employee__username', 'feedback')

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'model', 'action', 'timestamp')
    list_filter = ('action', 'model', 'timestamp')
    search_fields = ('user__username', 'changes')
    readonly_fields = ('user', 'model', 'instance_id', 'action', 'timestamp', 'changes')
