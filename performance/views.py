"""
This module imports all views from the views package to maintain backward compatibility.
"""

# Import dashboard views
from performance.views.dashboard_views import dashboard, profile

# Import performance agreement views
from performance.views.performance_agreement_views import (
    PerformanceAgreementListView,
    PerformanceAgreementCreateView,
    PerformanceAgreementDetailView,
    PerformanceAgreementUpdateView,
    performance_agreement_submit,
    performance_agreement_approve,
    performance_agreement_reject,
    performance_agreement_delete,
    export_agreement_pdf
)

# Import mid-year review views
from performance.views.midyear_review_views import (
    MidYearReviewListView,
    MidYearReviewCreateView,
    MidYearReviewDetailView,
    MidYearReviewUpdateView,
    midyear_review_delete
)

# Import final review views
from performance.views.final_review_views import (
    FinalReviewListView,
    FinalReviewCreateView,
    FinalReviewDetailView,
    FinalReviewUpdateView,
    FinalReviewDeleteView,
    final_review_delete,
    final_review_approve
)

# Import improvement plan views
from performance.views.improvement_plan_views import (
    ImprovementPlanListView,
    ImprovementPlanCreateView,
    ImprovementPlanDetailView,
    ImprovementPlanUpdateView,
    improvement_plan_delete,
    improvement_plan_item_delete,
    ImprovementPlanItemCreateView,
    ImprovementPlanItemUpdateView
)

# Import personal development plan views
from performance.views.development_plan_views import (
    PersonalDevelopmentPlanListView,
    PersonalDevelopmentPlanCreateView,
    PersonalDevelopmentPlanDetailView,
    PersonalDevelopmentPlanUpdateView,
    development_plan_delete,
    test_development_plans_view
)

# Import feedback views
from performance.views.feedback_views import (
    FeedbackCreateView,
    upload_kra_evidence,
    add_to_improvement_plan
)

# Import notification views
from performance.views.notification_views import (
    notification_list,
    notification_preferences,
    notification_count,
    mark_notification_read,
    mark_all_notifications_read
)