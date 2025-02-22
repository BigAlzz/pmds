from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)

class ViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.employee = CustomUser.objects.create_user(
            username='employee',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.manager = CustomUser.objects.create_user(
            username='manager',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        self.hr_user = CustomUser.objects.create_user(
            username='hr',
            password='testpass123',
            role=CustomUser.HR
        )
        
        # Set manager for employee
        self.employee.manager = self.manager
        self.employee.save()

class DashboardViewTests(ViewTestCase):
    def test_dashboard_view_authenticated(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/dashboard.html')

    def test_dashboard_view_unauthenticated(self):
        response = self.client.get(reverse('performance:dashboard'))
        self.assertEqual(response.status_code, 302)  # Redirects to login

class PerformanceAgreementViewTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.manager,
            plan_start_date=timezone.now().date(),
            plan_end_date=timezone.now().date(),
            status=PerformanceAgreement.DRAFT
        )

    def test_agreement_list_view_employee(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:performance_agreement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/performance_agreement_list.html')
        self.assertEqual(len(response.context['agreements']), 1)

    def test_agreement_list_view_manager(self):
        self.client.login(username='manager', password='testpass123')
        response = self.client.get(reverse('performance:performance_agreement_list'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['agreements']), 1)

    def test_agreement_create_view(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:performance_agreement_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/performance_agreement_form.html')

class MidYearReviewViewTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.manager,
            plan_start_date=timezone.now().date(),
            plan_end_date=timezone.now().date()
        )
        self.review = MidYearReview.objects.create(
            performance_agreement=self.agreement,
            self_rating='Good performance',
            supervisor_rating='Meets expectations',
            final_rating='MEETS',
            comments='Test comments'
        )

    def test_review_list_view_employee(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:midyear_review_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/midyear_review_list.html')
        self.assertEqual(len(response.context['reviews']), 1)

    def test_review_create_view(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:midyear_review_create'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/midyear_review_form.html')

class ImprovementPlanViewTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.plan = ImprovementPlan.objects.create(
            employee=self.employee,
            area_for_development='Communication',
            interventions='Training',
            timeline='3 months',
            status='PENDING'
        )

    def test_plan_list_view_employee(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:improvement_plan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/improvement_plan_list.html')
        self.assertEqual(len(response.context['plans']), 1)

class PersonalDevelopmentPlanViewTests(ViewTestCase):
    def setUp(self):
        super().setUp()
        self.plan = PersonalDevelopmentPlan.objects.create(
            employee=self.employee,
            competency_gap='Project Management',
            development_activities='Training',
            timeline='6 months',
            expected_outcome='Certification',
            start_date=timezone.now().date(),
            end_date=timezone.now().date()
        )

    def test_plan_list_view_employee(self):
        self.client.login(username='employee', password='testpass123')
        response = self.client.get(reverse('performance:development_plan_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'performance/development_plan_list.html')
        self.assertEqual(len(response.context['plans']), 1) 