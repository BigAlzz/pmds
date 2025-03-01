from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    Feedback,
    AuditLog,
    KRAMidYearRating,
    GAFMidYearRating
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
    actions = ['delete_selected']
    
    def has_delete_permission(self, request, obj=None):
        # Import here to avoid circular imports
        from .permissions import can_delete_performance_agreement
        
        # Allow the admin UI to show the delete button on the list view
        if obj is None:
            return request.user.is_superuser or request.user.role == 'HR'
        
        # Check specific object deletion permissions using our permission function
        return can_delete_performance_agreement(request.user, obj)
        
    def delete_selected(self, request, queryset):
        # Import here to avoid circular imports
        from .permissions import can_delete_performance_agreement
        
        # Filter queryset to only include items the user can delete
        deletable_ids = [
            obj.id for obj in queryset 
            if can_delete_performance_agreement(request.user, obj)
        ]
        deletable_queryset = PerformanceAgreement.objects.filter(id__in=deletable_ids)
        
        # Get count before deletion
        count = deletable_queryset.count()
        if count == 0:
            self.message_user(request, "No selected performance agreements could be deleted based on your permissions.", level='warning')
            return
            
        # Perform deletion
        deletable_queryset.delete()
        
        # Show success message
        self.message_user(request, f"Successfully deleted {count} performance agreement(s).")
    
    delete_selected.short_description = "Delete selected performance agreements"

@admin.register(MidYearReview)
class MidYearReviewAdmin(admin.ModelAdmin):
    list_display = ('performance_agreement', 'review_date', 'status')
    list_filter = ('status', 'review_date')
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

@admin.register(KRAMidYearRating)
class KRAMidYearRatingAdmin(admin.ModelAdmin):
    list_display = ('midyear_review', 'kra', 'employee_rating', 'supervisor_rating')
    list_filter = ('employee_rating', 'supervisor_rating')
    search_fields = ('midyear_review__performance_agreement__employee__username', 'kra__description')

@admin.register(GAFMidYearRating)
class GAFMidYearRatingAdmin(admin.ModelAdmin):
    list_display = ('midyear_review', 'gaf', 'employee_rating', 'supervisor_rating')
    list_filter = ('employee_rating', 'supervisor_rating')
    search_fields = ('midyear_review__performance_agreement__employee__username', 'gaf__factor')
