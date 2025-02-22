from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)

class CustomUserTests(TestCase):
    def setUp(self):
        self.user_data = {
            'username': 'testuser',
            'password': 'testpass123',
            'email': 'test@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'employee_id': 'EMP001',
            'persal_number': 'PER001',
            'role': CustomUser.EMPLOYEE,
            'department': 'IT',
            'job_title': 'Developer'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)

    def test_create_user(self):
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.employee_id, 'EMP001')
        self.assertEqual(self.user.role, CustomUser.EMPLOYEE)
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str_representation(self):
        expected = f"Test User (PER001)"
        self.assertEqual(str(self.user), expected)

class PerformanceAgreementTests(TestCase):
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
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            plan_start_date=timezone.now().date(),
            plan_end_date=timezone.now().date(),
            status=PerformanceAgreement.DRAFT
        )

    def test_performance_agreement_creation(self):
        self.assertEqual(self.agreement.employee, self.employee)
        self.assertEqual(self.agreement.supervisor, self.supervisor)
        self.assertEqual(self.agreement.status, PerformanceAgreement.DRAFT)

    def test_performance_agreement_str(self):
        expected = f"Performance Agreement for {self.employee.get_full_name()} ({self.agreement.plan_start_date.year}-{self.agreement.plan_end_date.year})"
        self.assertEqual(str(self.agreement), expected)

class MidYearReviewTests(TestCase):
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
        self.review = MidYearReview.objects.create(
            performance_agreement=self.agreement,
            self_rating='Good performance',
            supervisor_rating='Meets expectations',
            final_rating='MEETS',
            comments='Test comments',
            review_date=timezone.now().date()
        )

    def test_midyear_review_creation(self):
        self.assertEqual(self.review.performance_agreement, self.agreement)
        self.assertEqual(self.review.final_rating, 'MEETS')

    def test_midyear_review_str(self):
        expected = f"Mid-Year Review for {self.employee.get_full_name()} ({self.review.review_date})"
        self.assertEqual(str(self.review), expected)

    def test_can_edit_property(self):
        self.assertTrue(self.review.can_edit)

class ImprovementPlanTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.plan = ImprovementPlan.objects.create(
            employee=self.employee,
            area_for_development='Communication skills',
            interventions='Training workshops',
            timeline='3 months',
            status='PENDING'
        )

    def test_improvement_plan_creation(self):
        self.assertEqual(self.plan.employee, self.employee)
        self.assertEqual(self.plan.status, 'PENDING')

class PersonalDevelopmentPlanTests(TestCase):
    def setUp(self):
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123'
        )
        self.plan = PersonalDevelopmentPlan.objects.create(
            employee=self.employee,
            competency_gap='Project Management',
            development_activities='Training course',
            timeline='6 months',
            expected_outcome='Certification',
            progress=0,
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

    def test_personal_development_plan_creation(self):
        self.assertEqual(self.plan.employee, self.employee)
        self.assertEqual(self.plan.progress, 0)
        self.assertEqual(self.plan.competency_gap, 'Project Management') 