from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    KeyResponsibilityArea,
    GenericAssessmentFactor,
    KRAMidYearRating,
    GAFMidYearRating,
    KRAFinalRating,
    GAFFinalRating,
    SalaryLevel,
    NotificationPreference,
    ImprovementPlanItem
)
from datetime import timedelta
import time

class CustomUserTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.user_data = {
            'username': f'testuser_{self.timestamp}',
            'password': 'testpass123',
            'email': f'test_{self.timestamp}@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'employee_id': f'EMP{self.timestamp}',
            'persal_number': f'PER{self.timestamp}',
            'role': CustomUser.EMPLOYEE,
            'department': 'IT',
            'job_title': 'Developer'
        }
        self.user = CustomUser.objects.create_user(**self.user_data)
        
        # Create a manager with unique values
        self.manager = CustomUser.objects.create_user(
            username=f'manager_{self.timestamp}',
            password='testpass123',
            email=f'manager_{self.timestamp}@example.com',
            first_name='Manager',
            last_name='User',
            employee_id=f'EMP{self.timestamp+1}',
            persal_number=f'PER{self.timestamp+1}',
            role=CustomUser.MANAGER
        )
        
        # Set manager for employee
        self.user.manager = self.manager
        self.user.save()

    def test_create_user(self):
        self.assertEqual(self.user.username, f'testuser_{self.timestamp}')
        self.assertEqual(self.user.employee_id, f'EMP{self.timestamp}')
        self.assertEqual(self.user.role, CustomUser.EMPLOYEE)
        self.assertTrue(self.user.check_password('testpass123'))

    def test_user_str_representation(self):
        expected = f"Test User (PER{self.timestamp})"
        self.assertEqual(str(self.user), expected)
        
    def test_user_manager_relationship(self):
        self.assertEqual(self.user.manager, self.manager)
        self.assertIn(self.user, self.manager.subordinates.all())
        
    def test_user_roles(self):
        # Test different roles
        hr_user = CustomUser.objects.create_user(
            username=f'hruser_{self.timestamp}',
            password='testpass123',
            role=CustomUser.HR
        )
        approver = CustomUser.objects.create_user(
            username=f'approver_{self.timestamp}',
            password='testpass123',
            role=CustomUser.APPROVER
        )
        
        self.assertEqual(hr_user.role, CustomUser.HR)
        self.assertEqual(approver.role, CustomUser.APPROVER)

class SalaryLevelTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        # Create a salary level with a unique value
        self.level_value = f'5{self.timestamp % 1000}'
        self.salary_level = SalaryLevel.objects.create(
            level=self.level_value,
            typical_titles='Senior Developer',
            notes='Technical specialist role'
        )
    
    def test_salary_level_creation(self):
        self.assertEqual(self.salary_level.level, self.level_value)
        self.assertEqual(self.salary_level.typical_titles, 'Senior Developer')
        self.assertEqual(self.salary_level.numeric_level, int(self.level_value))
        
    def test_salary_level_str(self):
        expected = f"Level {self.level_value} - Senior Developer"
        self.assertEqual(str(self.salary_level), expected)
        
    def test_salary_level_ordering(self):
        # Create new levels with unique values and clear ordering
        level3_value = f'3{self.timestamp % 1000}'
        level7_value = f'7{self.timestamp % 1000}'
        
        level3 = SalaryLevel.objects.create(
            level=level3_value,
            typical_titles='Junior Developer', 
            notes='Entry level'
        )
        
        level7 = SalaryLevel.objects.create(
            level=level7_value,
            typical_titles='Team Lead', 
            notes='Management role'
        )
        
        # Get all levels created in this test and verify the ordering
        levels = list(SalaryLevel.objects.filter(
            level__in=[level3_value, self.level_value, level7_value]
        ).order_by('numeric_level'))
        
        # Verify the correct order by checking the numeric_level values
        self.assertEqual(len(levels), 3)
        self.assertEqual(levels[0].level, level3_value)
        self.assertEqual(levels[1].level, self.level_value)
        self.assertEqual(levels[2].level, level7_value)

class PerformanceAgreementTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_pa_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_pa_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        self.manager = CustomUser.objects.create_user(
            username=f'manager_pa_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        
        # Set relationships
        self.employee.manager = self.supervisor
        self.employee.save()
        self.supervisor.manager = self.manager
        self.supervisor.save()
        
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            approver=self.manager,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date(),
            status=PerformanceAgreement.DRAFT
        )
        
        # Create KRAs
        self.kra1 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Software Development",
            performance_objective="Develop high-quality code",
            weighting=60,
            measurement="Code quality metrics"
        )
        
        self.kra2 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Documentation",
            performance_objective="Create comprehensive documentation",
            weighting=40,
            measurement="Documentation completeness"
        )

    def test_performance_agreement_creation(self):
        self.assertEqual(self.agreement.employee, self.employee)
        self.assertEqual(self.agreement.supervisor, self.supervisor)
        self.assertEqual(self.agreement.approver, self.manager)
        self.assertEqual(self.agreement.status, PerformanceAgreement.DRAFT)

    def test_performance_agreement_str(self):
        expected = f"Performance Agreement for {self.employee.get_full_name()} ({self.agreement.plan_start_date.year}-{self.agreement.plan_end_date.year})"
        self.assertEqual(str(self.agreement), expected)
        
    def test_kra_relationship(self):
        self.assertEqual(self.agreement.kras.count(), 2)
        self.assertIn(self.kra1, self.agreement.kras.all())
        self.assertIn(self.kra2, self.agreement.kras.all())
        
    def test_workflow_status_transitions(self):
        # Test status transitions
        self.agreement.status = PerformanceAgreement.PENDING_EMPLOYEE_RATING
        self.agreement.employee_submitted_date = timezone.now()
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.PENDING_EMPLOYEE_RATING)
        self.assertIsNotNone(self.agreement.employee_submitted_date)
        
        # Test supervisor review
        self.agreement.status = PerformanceAgreement.PENDING_SUPERVISOR_RATING
        self.agreement.supervisor_reviewed_date = timezone.now()
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.PENDING_SUPERVISOR_RATING)
        self.assertIsNotNone(self.agreement.supervisor_reviewed_date)
        
        # Test supervisor signoff
        self.agreement.status = PerformanceAgreement.PENDING_SUPERVISOR_SIGNOFF
        self.agreement.supervisor_signoff_date = timezone.now()
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.PENDING_SUPERVISOR_SIGNOFF)
        self.assertIsNotNone(self.agreement.supervisor_signoff_date)
        
        # Test manager approval
        self.agreement.status = PerformanceAgreement.PENDING_MANAGER_APPROVAL
        self.agreement.manager_approval_date = timezone.now()
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.PENDING_MANAGER_APPROVAL)
        self.assertIsNotNone(self.agreement.manager_approval_date)
        
        # Test completion
        self.agreement.status = PerformanceAgreement.COMPLETED
        self.agreement.completion_date = timezone.now()
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.COMPLETED)
        self.assertIsNotNone(self.agreement.completion_date)
        
    def test_rejection_workflow(self):
        # Test rejection
        self.agreement.status = PerformanceAgreement.REJECTED
        self.agreement.rejection_date = timezone.now()
        self.agreement.rejection_reason = "Needs more specific KRAs"
        self.agreement.save()
        
        self.assertEqual(self.agreement.status, PerformanceAgreement.REJECTED)
        self.assertIsNotNone(self.agreement.rejection_date)
        self.assertEqual(self.agreement.rejection_reason, "Needs more specific KRAs")

class MidYearReviewTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        # Create users
        self.employee = CustomUser.objects.create_user(
            username=f'employee_myr_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_myr_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        
        # Set relationships
        self.employee.manager = self.supervisor
        self.employee.save()
        
        # Create performance agreement
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            agreement_date=timezone.now().date(),
            status='DRAFT'
        )
        
        # Create KRAs
        self.kra1 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Software Development",
            weighting=60,
            measurement="Code quality metrics"
        )
        
        self.kra2 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Documentation",
            weighting=40,
            measurement="Documentation completeness"
        )
        
        # Create GAFs
        self.gaf = GenericAssessmentFactor.objects.create(
            performance_agreement=self.agreement,
            factor="GAF1",
            is_applicable=True
        )
        
        self.review = MidYearReview.objects.create(
            performance_agreement=self.agreement,
            review_date=timezone.now().date(),
            status='DRAFT'
        )
        
        # Create KRA ratings
        self.kra_rating1 = KRAMidYearRating.objects.create(
            midyear_review=self.review,
            kra=self.kra1,
            employee_rating=3,
            employee_comments="Good progress",
            supervisor_rating=3,
            supervisor_comments="Agree with assessment",
            agreed_rating=3
        )
        
        self.kra_rating2 = KRAMidYearRating.objects.create(
            midyear_review=self.review,
            kra=self.kra2,
            employee_rating=4,
            employee_comments="Excellent documentation",
            supervisor_rating=3,
            supervisor_comments="Good but some areas need improvement",
            agreed_rating=3
        )
        
        # Create GAF rating
        self.gaf_rating = GAFMidYearRating.objects.create(
            midyear_review=self.review,
            gaf=self.gaf,
            employee_rating=3,
            employee_comments="Good communication skills",
            supervisor_rating=3,
            supervisor_comments="Agree with assessment"
        )

    def test_midyear_review_creation(self):
        self.assertEqual(self.review.performance_agreement, self.agreement)
        self.assertEqual(self.review.status, 'DRAFT')

    def test_midyear_review_str(self):
        expected = f"Mid-Year Review for {self.employee.get_full_name()} ({self.review.review_date})"
        self.assertEqual(str(self.review), expected)

    def test_can_edit_property(self):
        self.assertTrue(self.review.can_edit)
        
        # Test that completed reviews can't be edited
        self.review.status = 'COMPLETED'
        self.review.save()
        self.assertFalse(self.review.can_edit)
        
    def test_kra_ratings_relationship(self):
        self.assertEqual(self.review.kra_ratings.count(), 2)
        self.assertIn(self.kra_rating1, self.review.kra_ratings.all())
        self.assertIn(self.kra_rating2, self.review.kra_ratings.all())
        
    def test_gaf_ratings_relationship(self):
        self.assertEqual(self.review.gaf_ratings.count(), 1)
        self.assertIn(self.gaf_rating, self.review.gaf_ratings.all())
        
    def test_calculate_overall_rating(self):
        # Test calculation of overall rating
        overall_rating = self.review.calculate_overall_rating()
        
        # Expected: (60% * 3) + (40% * 3) = 3
        self.assertEqual(overall_rating, 3)
        
    def test_workflow_status_transitions(self):
        # Test status transitions
        self.review.status = 'PENDING_EMPLOYEE_RATING'
        self.review.employee_rating_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_EMPLOYEE_RATING')
        self.assertIsNotNone(self.review.employee_rating_date)
        
        # Test supervisor rating
        self.review.status = 'PENDING_SUPERVISOR_RATING'
        self.review.supervisor_rating_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_SUPERVISOR_RATING')
        self.assertIsNotNone(self.review.supervisor_rating_date)
        
        # Test supervisor signoff
        self.review.status = 'PENDING_SUPERVISOR_SIGNOFF'
        self.review.supervisor_signoff_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_SUPERVISOR_SIGNOFF')
        self.assertIsNotNone(self.review.supervisor_signoff_date)
        
        # Test manager approval
        self.review.status = 'PENDING_MANAGER_APPROVAL'
        self.review.manager_approval_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_MANAGER_APPROVAL')
        self.assertIsNotNone(self.review.manager_approval_date)
        
        # Test completion
        self.review.status = 'COMPLETED'
        self.review.completion_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'COMPLETED')
        self.assertIsNotNone(self.review.completion_date)
        
    def test_rejection_workflow(self):
        # Test rejection
        self.review.status = 'REJECTED'
        self.review.rejection_date = timezone.now()
        self.review.rejection_reason = "Ratings need justification"
        self.review.save()
        
        self.assertEqual(self.review.status, 'REJECTED')
        self.assertEqual(self.review.rejection_reason, "Ratings need justification")

class FinalReviewTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        # Create users
        self.employee = CustomUser.objects.create_user(
            username=f'employee_fr_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_fr_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        
        # Set relationships
        self.employee.manager = self.supervisor
        self.employee.save()
        
        # Create performance agreement
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            agreement_date=timezone.now().date(),
            status='DRAFT'
        )
        
        # Create KRAs
        self.kra1 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Software Development",
            weighting=60,
            measurement="Code quality metrics"
        )
        
        self.kra2 = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Documentation",
            weighting=40,
            measurement="Documentation completeness"
        )
        
        # Create GAFs
        self.gaf = GenericAssessmentFactor.objects.create(
            performance_agreement=self.agreement,
            factor="GAF1",
            is_applicable=True
        )
        
        self.review = FinalReview.objects.create(
            performance_agreement=self.agreement,
            review_date=timezone.now().date(),
            status='DRAFT'
        )
        
        # Create KRA ratings
        self.kra_rating1 = KRAFinalRating.objects.create(
            final_review=self.review,
            kra=self.kra1,
            employee_rating=3,
            employee_comments="Good progress",
            supervisor_rating=3,
            supervisor_comments="Agree with assessment",
            agreed_rating=3
        )
        
        self.kra_rating2 = KRAFinalRating.objects.create(
            final_review=self.review,
            kra=self.kra2,
            employee_rating=4,
            employee_comments="Excellent documentation",
            supervisor_rating=3,
            supervisor_comments="Good but some areas need improvement",
            agreed_rating=3
        )
        
        # Create GAF rating
        self.gaf_rating = GAFFinalRating.objects.create(
            final_review=self.review,
            gaf=self.gaf,
            employee_rating=3,
            employee_comments="Good communication skills",
            supervisor_rating=3,
            supervisor_comments="Agree with assessment"
        )

    def test_final_review_creation(self):
        self.assertEqual(self.review.performance_agreement, self.agreement)
        self.assertEqual(self.review.status, 'DRAFT')

    def test_final_review_str(self):
        expected = f"Year-End Review for {self.employee.get_full_name()} - {self.review.review_date}"
        self.assertEqual(str(self.review), expected)

    def test_can_edit_property(self):
        self.assertTrue(self.review.can_edit)
        
        # Test that completed reviews can't be edited
        self.review.status = 'COMPLETED'
        self.review.save()
        self.assertFalse(self.review.can_edit)
        
    def test_kra_ratings_relationship(self):
        self.assertEqual(self.review.kra_ratings.count(), 2)
        
    def test_calculate_overall_rating(self):
        # Test calculation of overall rating
        overall_rating = self.review.calculate_overall_rating()
        
        # Expected: (60% * 3) + (40% * 3) = 3
        self.assertEqual(overall_rating, 3)
        
    def test_workflow_status_transitions(self):
        # Test status transitions
        self.review.status = 'PENDING_EMPLOYEE_RATING'
        self.review.employee_rating_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_EMPLOYEE_RATING')
        self.assertIsNotNone(self.review.employee_rating_date)
        
        # Test supervisor rating
        self.review.status = 'PENDING_SUPERVISOR_RATING'
        self.review.supervisor_rating_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_SUPERVISOR_RATING')
        self.assertIsNotNone(self.review.supervisor_rating_date)
        
        # Test supervisor signoff
        self.review.status = 'PENDING_SUPERVISOR_SIGNOFF'
        self.review.supervisor_signoff_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_SUPERVISOR_SIGNOFF')
        self.assertIsNotNone(self.review.supervisor_signoff_date)
        
        # Test manager approval
        self.review.status = 'PENDING_MANAGER_APPROVAL'
        self.review.manager_approval_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'PENDING_MANAGER_APPROVAL')
        self.assertIsNotNone(self.review.manager_approval_date)
        
        # Test completion
        self.review.status = 'COMPLETED'
        self.review.completion_date = timezone.now()
        self.review.save()
        
        self.assertEqual(self.review.status, 'COMPLETED')
        self.assertIsNotNone(self.review.completion_date)
        
    def test_rejection_workflow(self):
        # Test rejection
        self.review.status = 'REJECTED'
        self.review.rejection_date = timezone.now()
        self.review.rejection_reason = "Ratings need justification"
        self.review.save()
        
        self.assertEqual(self.review.status, 'REJECTED')
        self.assertIsNotNone(self.review.rejection_date)
        self.assertEqual(self.review.rejection_reason, "Ratings need justification")

class ImprovementPlanTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_ip_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_ip_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        
        # Set relationships
        self.employee.manager = self.supervisor
        self.employee.save()
        
        # Create the improvement plan with correct fields
        self.plan = ImprovementPlan.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            status='DRAFT',
            overall_comments='Initial improvement plan'
        )
        
        # Create an improvement plan item
        self.plan_item = ImprovementPlanItem.objects.create(
            improvement_plan=self.plan,
            area_for_development='Communication skills',
            interventions='Training workshops',
            timeline='3 months',
            source_type=ImprovementPlanItem.PERFORMANCE_AGREEMENT,
            source_id=1
        )

    def test_improvement_plan_creation(self):
        self.assertEqual(self.plan.employee, self.employee)
        self.assertEqual(self.plan.supervisor, self.supervisor)
        self.assertEqual(self.plan.status, 'DRAFT')
        
        # Test the plan item
        self.assertEqual(self.plan_item.area_for_development, 'Communication skills')
        self.assertEqual(self.plan_item.interventions, 'Training workshops')
        self.assertEqual(self.plan_item.timeline, '3 months')
        
    def test_improvement_plan_str(self):
        expected = f"Improvement Plan for {self.employee.get_full_name()}"
        self.assertEqual(str(self.plan), expected)
        
    def test_get_or_create_current_plan(self):
        # Test the class method
        plan = ImprovementPlan.get_or_create_current_plan(self.employee)
        self.assertEqual(plan, self.plan)  # Should return existing plan
        
        # Test with a new employee
        new_employee = CustomUser.objects.create_user(
            username=f'newemployee_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        new_plan = ImprovementPlan.get_or_create_current_plan(new_employee)
        self.assertEqual(new_plan.employee, new_employee)
        self.assertEqual(new_plan.status, 'DRAFT')

class PersonalDevelopmentPlanTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_pdp_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.plan = PersonalDevelopmentPlan.objects.create(
            employee=self.employee,
            competency_gap='Project Management',
            development_activities='Training course',
            timeline='6 months',
            expected_outcome='Certification',
            progress=0,
            start_date=timezone.now().date(),
            end_date=(timezone.now() + timedelta(days=180)).date()
        )

    def test_personal_development_plan_creation(self):
        self.assertEqual(self.plan.employee, self.employee)
        self.assertEqual(self.plan.progress, 0)
        self.assertEqual(self.plan.competency_gap, 'Project Management')
        
    def test_personal_development_plan_str(self):
        expected = f"Development Plan for {self.employee.get_full_name()}"
        self.assertEqual(str(self.plan), expected)
        
    def test_display_fields(self):
        self.assertIn('competency_gap', self.plan.display_fields)
        self.assertIn('progress', self.plan.display_fields)

class NotificationPreferenceTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.user = CustomUser.objects.create_user(
            username=f'user_np_{self.timestamp}',
            password='testpass123',
            email=f'user_np_{self.timestamp}@example.com'
        )
        
    def test_notification_preference_creation(self):
        # Test that preferences are automatically created
        prefs = NotificationPreference.objects.get(user=self.user)
        self.assertEqual(prefs.user, self.user)
        self.assertTrue(prefs.email_notifications)
        self.assertTrue(prefs.review_reminders)
        self.assertEqual(prefs.reminder_frequency, 'WEEKLY')
        
    def test_notification_preference_str(self):
        prefs = NotificationPreference.objects.get(user=self.user)
        expected = f"Notification Preferences for {self.user.get_full_name()}"
        self.assertEqual(str(prefs), expected) 