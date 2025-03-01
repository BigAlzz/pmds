"""
This module imports all views from separate view files to maintain backward compatibility.
"""

# Import dashboard views
from .dashboard_views import dashboard, profile

# Import performance agreement views
from .performance_agreement_views import (
    PerformanceAgreementListView,
    PerformanceAgreementCreateView,
    PerformanceAgreementDetailView,
    PerformanceAgreementUpdateView,
    performance_agreement_submit,
    performance_agreement_approve,
    performance_agreement_reject,
    performance_agreement_delete,
    export_agreement_pdf,
    performance_agreement_hr_verify,
    return_performance_agreement
)

# Import mid-year review views
from .midyear_review_views import (
    MidYearReviewListView,
    MidYearReviewCreateView,
    MidYearReviewDetailView,
    MidYearReviewUpdateView,
    midyear_review_delete
)

# Import final review views
from .final_review_views import (
    FinalReviewListView,
    FinalReviewCreateView,
    FinalReviewDetailView,
    FinalReviewUpdateView,
    FinalReviewDeleteView,
    final_review_delete,
    final_review_approve
)

# Import improvement plan views
from .improvement_plan_views import (
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
from .development_plan_views import (
    PersonalDevelopmentPlanListView,
    PersonalDevelopmentPlanCreateView,
    PersonalDevelopmentPlanDetailView,
    PersonalDevelopmentPlanUpdateView,
    development_plan_delete,
    test_development_plans_view
)

# Import feedback views
from .feedback_views import (
    FeedbackCreateView,
    upload_kra_evidence,
    add_to_improvement_plan
)

# Import notification views
from .notification_views import (
    notification_list,
    notification_preferences,
    notification_count,
    mark_notification_read,
    mark_all_notifications_read
) 