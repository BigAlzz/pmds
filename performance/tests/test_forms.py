from django.test import TestCase
from django.utils import timezone
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)
from performance.forms import (
    PerformanceAgreementForm,
    MidYearReviewForm,
    ImprovementPlanForm,
    PersonalDevelopmentPlanForm
)

class PerformanceAgreementFormTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username='supervisor',
            password='testpass123',
            role=CustomUser.MANAGER
        )

    def test_valid_agreement_data(self):
        form_data = {
            'plan_start_date': timezone.now().date(),
            'plan_end_date': timezone.now().date(),
            'midyear_review_date': timezone.now().date(),
            'final_assessment_date': timezone.now().date(),
            'status': PerformanceAgreement.DRAFT
        }
        form = PerformanceAgreementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_dates(self):
        form_data = {
            'plan_start_date': timezone.now().date(),
            'plan_end_date': timezone.now().date() - timezone.timedelta(days=1),  # End date before start date
            'status': PerformanceAgreement.DRAFT
        }
        form = PerformanceAgreementForm(data=form_data)
        self.assertFalse(form.is_valid())

class MidYearReviewFormTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            plan_start_date=timezone.now().date(),
            plan_end_date=timezone.now().date()
        )

    def test_valid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'self_rating': 'Good performance',
            'supervisor_rating': 'Meets expectations',
            'final_rating': 'MEETS',
            'comments': 'Test comments',
            'review_date': timezone.now().date()
        }
        form = MidYearReviewForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'final_rating': 'INVALID_RATING',  # Invalid choice
            'review_date': timezone.now().date()
        }
        form = MidYearReviewForm(data=form_data)
        self.assertFalse(form.is_valid())

class ImprovementPlanFormTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123'
        )

    def test_valid_plan_data(self):
        form_data = {
            'area_for_development': 'Communication skills',
            'interventions': 'Training workshops',
            'timeline': '3 months',
            'status': 'PENDING'
        }
        form = ImprovementPlanForm(data=form_data)
        self.assertTrue(form.is_valid())

class PersonalDevelopmentPlanFormTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123'
        )

    def test_valid_plan_data(self):
        form_data = {
            'competency_gap': 'Project Management',
            'development_activities': 'Training course',
            'timeline': '6 months',
            'expected_outcome': 'Certification',
            'progress': 0,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date()
        }
        form = PersonalDevelopmentPlanForm(data=form_data)
        self.assertTrue(form.is_valid()) 