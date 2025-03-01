from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    Notification,
    NotificationPreference
)

class Command(BaseCommand):
    help = 'Sends periodic notifications based on user preferences and due dates'

    def handle(self, *args, **options):
        self.stdout.write('Starting notification check...')
        
        # Get all users with their notification preferences
        users = CustomUser.objects.filter(
            notification_preferences__isnull=False,
            is_active=True
        )

        for user in users:
            preferences = user.notification_preferences
            
            # Skip if user has disabled all notifications
            if not any([
                preferences.review_reminders,
                preferences.plan_updates,
                preferences.feedback_notifications
            ]):
                continue

            # Check Performance Agreement due dates
            if preferences.review_reminders:
                self._check_performance_agreements(user)
                self._check_midyear_reviews(user)

            # Check Improvement Plan updates
            if preferences.plan_updates:
                self._check_improvement_plans(user)
                self._check_development_plans(user)

        self.stdout.write(self.style.SUCCESS('Successfully sent notifications'))

    def _check_performance_agreements(self, user):
        # Check agreements that are due in the next week
        due_date = timezone.now().date() + timezone.timedelta(days=7)
        agreements = PerformanceAgreement.objects.filter(
            Q(employee=user) | Q(employee__manager=user),
            status__in=['DRAFT', 'PENDING_APPROVAL'],
            agreement_date__lte=due_date
        )

        for agreement in agreements:
            Notification.objects.create(
                recipient=user,
                notification_type='REVIEW_DUE',
                title='Performance Agreement Due Soon',
                message=f'Performance agreement for {agreement.employee.get_full_name()} is due by {agreement.agreement_date}',
                related_object_type='performance_agreement',
                related_object_id=agreement.id
            )

    def _check_midyear_reviews(self, user):
        # Check reviews that need attention
        reviews = MidYearReview.objects.filter(
            Q(performance_agreement__employee=user) | Q(performance_agreement__employee__manager=user),
            status__in=['DRAFT', 'PENDING_EMPLOYEE_RATING', 'PENDING_SUPERVISOR_RATING']
        )

        for review in reviews:
            Notification.objects.create(
                recipient=user,
                notification_type='REVIEW_DUE',
                title='Mid-Year Review Needs Attention',
                message=f'Mid-year review for {review.performance_agreement.employee.get_full_name()} needs to be completed',
                related_object_type='midyear_review',
                related_object_id=review.id
            )

    def _check_improvement_plans(self, user):
        # Check improvement plans that need updates
        plans = ImprovementPlan.objects.filter(
            Q(employee=user) | Q(employee__manager=user),
            status='IN_PROGRESS'
        )

        for plan in plans:
            Notification.objects.create(
                recipient=user,
                notification_type='PLAN_UPDATE',
                title='Improvement Plan Update Required',
                message=f'Please update the improvement plan for {plan.employee.get_full_name()}',
                related_object_type='improvement_plan',
                related_object_id=plan.id
            )

    def _check_development_plans(self, user):
        # Check development plans that need updates
        plans = PersonalDevelopmentPlan.objects.filter(
            Q(employee=user) | Q(employee__manager=user),
            end_date__gt=timezone.now().date(),
            progress__lt=100
        )

        for plan in plans:
            Notification.objects.create(
                recipient=user,
                notification_type='PLAN_UPDATE',
                title='Development Plan Update Required',
                message=f'Please update the development plan for {plan.employee.get_full_name()}',
                related_object_type='development_plan',
                related_object_id=plan.id
            ) 