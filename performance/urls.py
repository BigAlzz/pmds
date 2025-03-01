from django.urls import path
from . import views

# Import audit views
from .views import audit_views

app_name = 'performance'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Profile
    path('profile/', views.profile, name='profile'),

    # Performance Agreements
    path('agreements/', views.PerformanceAgreementListView.as_view(), name='performance_agreement_list'),
    path('agreements/create/', views.PerformanceAgreementCreateView.as_view(), name='performance_agreement_create'),
    path('agreements/<int:pk>/', views.PerformanceAgreementDetailView.as_view(), name='performance_agreement_detail'),
    path('agreements/<int:pk>/edit/', views.PerformanceAgreementUpdateView.as_view(), name='performance_agreement_update'),
    path('agreements/<int:pk>/submit/', views.performance_agreement_submit, name='performance_agreement_submit'),
    path('agreements/<int:pk>/approve/', views.performance_agreement_approve, name='performance_agreement_approve'),
    path('agreements/<int:pk>/reject/', views.performance_agreement_reject, name='performance_agreement_reject'),
    path('agreements/<int:pk>/pdf/', views.export_agreement_pdf, name='export_agreement_pdf'),
    path('agreements/<int:pk>/delete/', views.performance_agreement_delete, name='performance_agreement_delete'),
    path('agreements/<int:pk>/hr-verify/', views.performance_agreement_hr_verify, name='performance_agreement_hr_verify'),
    path('agreements/<int:pk>/return/', views.return_performance_agreement, name='return_performance_agreement'),

    # Mid-Year Reviews
    path('reviews/', views.MidYearReviewListView.as_view(), name='midyear_review_list'),
    path('reviews/create/', views.MidYearReviewCreateView.as_view(), name='midyear_review_create'),
    path('reviews/<int:pk>/', views.MidYearReviewDetailView.as_view(), name='midyear_review_detail'),
    path('reviews/<int:pk>/edit/', views.MidYearReviewUpdateView.as_view(), name='midyear_review_update'),
    path('reviews/<int:pk>/delete/', views.midyear_review_delete, name='midyear_review_delete'),

    # Year-End Reviews
    path('final-reviews/', views.FinalReviewListView.as_view(), name='final_review_list'),
    path('final-reviews/create/', views.FinalReviewCreateView.as_view(), name='final_review_create'),
    path('final-reviews/<int:pk>/', views.FinalReviewDetailView.as_view(), name='final_review_detail'),
    path('final-reviews/<int:pk>/edit/', views.FinalReviewUpdateView.as_view(), name='final_review_update'),
    path('final-reviews/<int:pk>/delete/', views.final_review_delete, name='final_review_delete'),

    # Improvement Plans
    path('improvement-plans/', views.ImprovementPlanListView.as_view(), name='improvement_plan_list'),
    path('improvement-plans/create/', views.ImprovementPlanCreateView.as_view(), name='improvement_plan_create'),
    path('improvement-plans/<int:pk>/', views.ImprovementPlanDetailView.as_view(), name='improvement_plan_detail'),
    path('improvement-plans/<int:pk>/edit/', views.ImprovementPlanUpdateView.as_view(), name='improvement_plan_update'),
    path('improvement-plans/<int:pk>/delete/', views.improvement_plan_delete, name='improvement_plan_delete'),
    path('improvement-plans/<int:plan_id>/add-item/', views.ImprovementPlanItemCreateView.as_view(), name='improvement_plan_item_create'),
    path('improvement-plan-items/<int:pk>/edit/', views.ImprovementPlanItemUpdateView.as_view(), name='improvement_plan_item_update'),
    path('improvement-plan-items/<int:pk>/delete/', views.improvement_plan_item_delete, name='improvement_plan_item_delete'),

    # Personal Development Plans
    path('development-plans/', views.PersonalDevelopmentPlanListView.as_view(), name='development_plan_list'),
    path('development-plans/create/', views.PersonalDevelopmentPlanCreateView.as_view(), name='development_plan_create'),
    path('development-plans/<int:pk>/', views.PersonalDevelopmentPlanDetailView.as_view(), name='development_plan_detail'),
    path('development-plans/<int:pk>/update/', views.PersonalDevelopmentPlanUpdateView.as_view(), name='development_plan_update'),
    path('development-plans/<int:pk>/delete/', views.development_plan_delete, name='development_plan_delete'),
    
    # Test views
    path('test-development-plans/', views.test_development_plans_view, name='test_development_plans'),

    # Feedback
    path('feedback/create/', views.FeedbackCreateView.as_view(), name='feedback_create'),

    # Notifications
    path('notifications/', views.notification_list, name='notification_list'),
    path('notifications/preferences/', views.notification_preferences, name='notification_preferences'),
    path('notifications/count/', views.notification_count, name='notification_count'),
    path('notifications/<int:notification_id>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/read-all/', views.mark_all_notifications_read, name='mark_all_notifications_read'),

    # KRA Evidence Upload
    path('upload-kra-evidence/', views.upload_kra_evidence, name='upload_kra_evidence'),

    # Improvement Plan
    path('improvement-plan/add-item/', views.add_to_improvement_plan, name='add_to_improvement_plan'),

    # Audit Trail URLs
    path('audit-trail/', audit_views.audit_trail_list, name='audit_trail_list'),
    path('audit-trail/<int:pk>/', audit_views.audit_trail_detail, name='audit_trail_detail'),
]
