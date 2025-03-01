from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import timedelta
from performance.models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    KeyResponsibilityArea,
    GenericAssessmentFactor,
    SalaryLevel
)
from performance.forms import (
    PerformanceAgreementForm,
    MidYearReviewForm,
    FinalReviewForm,
    ImprovementPlanForm,
    PersonalDevelopmentPlanForm,
    KRAForm,
    KRAInlineFormSet,
    KRAMidYearRatingForm,
    GAFMidYearRatingForm,
    KRAFinalRatingForm,
    GAFFinalRatingForm,
    UserProfileForm
)
import time

class PerformanceAgreementFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_form_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_form_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        self.manager = CustomUser.objects.create_user(
            username=f'manager_form_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        
        # Set relationships
        self.employee.manager = self.supervisor
        self.employee.save()
        self.supervisor.manager = self.manager
        self.supervisor.save()

    def test_valid_agreement_data(self):
        form_data = {
            'employee': self.employee.id,
            'supervisor': self.supervisor.id,
            'approver': self.manager.id,
            'plan_start_date': timezone.now().date(),
            'plan_end_date': (timezone.now() + timedelta(days=365)).date(),
            'midyear_review_date': (timezone.now() + timedelta(days=180)).date(),
            'final_assessment_date': (timezone.now() + timedelta(days=350)).date(),
            'employee_comments': 'Initial employee comments',
            'supervisor_comments': 'Initial supervisor comments',
            'manager_comments': 'Initial manager comments',
            'status': 'DRAFT',
            'batch_number': f'BATCH-{self.timestamp}'  # Add batch number
        }
        form = PerformanceAgreementForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_invalid_dates(self):
        form_data = {
            'employee': self.employee.id,
            'supervisor': self.supervisor.id,
            'plan_start_date': timezone.now().date(),
            'plan_end_date': timezone.now().date() - timedelta(days=1),  # End date before start date
            'status': 'DRAFT'
        }
        form = PerformanceAgreementForm(data=form_data)
        self.assertFalse(form.is_valid())
        
    def test_missing_required_fields(self):
        form_data = {
            'employee': self.employee.id,
            # Missing supervisor
            'plan_start_date': timezone.now().date(),
            'plan_end_date': (timezone.now() + timedelta(days=365)).date(),
        }
        form = PerformanceAgreementForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('supervisor', form.errors)
        
    def test_form_with_instance(self):
        agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date(),
            status='DRAFT'
        )
        
        form = PerformanceAgreementForm(instance=agreement)
        self.assertEqual(form.initial['employee'], self.employee.id)
        self.assertEqual(form.initial['supervisor'], self.supervisor.id)

class KRAFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_kra_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.supervisor = CustomUser.objects.create_user(
            username=f'supervisor_kra_{self.timestamp}',
            password='testpass123',
            role=CustomUser.MANAGER
        )
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date(),
            status='DRAFT'
        )

    def test_valid_kra_data(self):
        form_data = {
            'description': 'Software Development',
            'performance_objective': 'Develop high-quality code',
            'weighting': 60,
            'measurement': 'Code quality metrics',
            'target_date': (timezone.now() + timedelta(days=180)).date(),
            'tools': 'IDE, Git',
            'barriers': 'Technical complexity',
            'evidence_examples': 'Code reviews, test coverage'
        }
        form = KRAForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_weighting(self):
        form_data = {
            'description': 'Software Development',
            'performance_objective': 'Develop high-quality code',
            'weighting': 101,  # Over 100
            'measurement': 'Code quality metrics',
            'target_date': (timezone.now() + timedelta(days=180)).date(),
            'tools': 'IDE, Git',
            'barriers': 'Technical complexity',
            'evidence_examples': 'Code reviews, test coverage'
        }
        form = KRAForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weighting', form.errors)
        
    def test_missing_required_fields(self):
        form_data = {
            'description': 'Software Development',
            # Missing weighting and measurement
        }
        form = KRAForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('weighting', form.errors)
        self.assertIn('measurement', form.errors)

class MidYearReviewFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
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
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date(),
            status='COMPLETED'
        )
        
        # Create KRAs
        self.kra = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Software Development",
            weighting=60,
            measurement="Code quality metrics"
        )
        
        # Create GAFs
        self.gaf = GenericAssessmentFactor.objects.create(
            performance_agreement=self.agreement,
            factor="GAF1",
            is_applicable=True
        )

    def test_valid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'review_date': timezone.now().date(),
            'employee_overall_comments': 'My self-assessment comments',
            'supervisor_overall_comments': 'Supervisor assessment comments',
            'status': 'DRAFT'
        }
        
        # Create a test file for evidence
        test_file = SimpleUploadedFile("test_evidence.pdf", b"file_content", content_type="application/pdf")
        form_files = {
            'evidence_document': test_file
        }
        
        form = MidYearReviewForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    def test_invalid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'status': 'INVALID_STATUS',  # Invalid choice
            'review_date': timezone.now().date()
        }
        form = MidYearReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)
        
    def test_missing_required_fields(self):
        form_data = {
            # Missing performance_agreement
            'review_date': timezone.now().date()
        }
        form = MidYearReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('performance_agreement', form.errors)

class KRAMidYearRatingFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_kra_rating_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date()
        )
        self.review = MidYearReview.objects.create(
            performance_agreement=self.agreement,
            review_date=timezone.now().date()
        )
        self.kra = KeyResponsibilityArea.objects.create(
            performance_agreement=self.agreement,
            description="Software Development",
            weighting=60,
            measurement="Code quality metrics"
        )

    def test_valid_rating_data(self):
        form_data = {
            'kra': self.kra.id,
            'employee_rating': 3,
            'employee_comments': 'Good progress',
            'employee_evidence': 'Completed all tasks',
            'supervisor_rating': 3,
            'supervisor_comments': 'Agree with assessment',
            'agreed_rating': 3
        }
        
        # Create a test file for evidence
        test_file = SimpleUploadedFile("test_evidence.pdf", b"file_content", content_type="application/pdf")
        form_files = {
            'employee_evidence_file': test_file
        }
        
        form = KRAMidYearRatingForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())
        
    def test_invalid_rating_value(self):
        form_data = {
            'kra': self.kra.id,
            'employee_rating': 5,  # Invalid rating (should be 1-4)
            'employee_comments': 'Good progress'
        }
        form = KRAMidYearRatingForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('employee_rating', form.errors)

class FinalReviewFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
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
        self.agreement = PerformanceAgreement.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            plan_start_date=timezone.now().date(),
            plan_end_date=(timezone.now() + timedelta(days=365)).date(),
            status='COMPLETED'
        )

    def test_valid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'review_date': timezone.now().date(),
            'employee_overall_comments': 'My self-assessment comments',
            'supervisor_overall_comments': 'Supervisor assessment comments',
            'status': 'DRAFT'
        }
        
        # Create a test file for evidence
        test_file = SimpleUploadedFile("test_evidence.pdf", b"file_content", content_type="application/pdf")
        form_files = {
            'evidence_document': test_file
        }
        
        form = FinalReviewForm(data=form_data, files=form_files)
        self.assertTrue(form.is_valid())

    def test_invalid_review_data(self):
        form_data = {
            'performance_agreement': self.agreement.id,
            'review_date': timezone.now().date(),
            'employee_overall_comments': '',  # Empty required field
            'supervisor_overall_comments': ''  # Empty required field
        }
        form = FinalReviewForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('employee_overall_comments', form.errors)
        self.assertIn('supervisor_overall_comments', form.errors)

class ImprovementPlanFormTests(TestCase):
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
        
        # Create an improvement plan for testing
        self.plan = ImprovementPlan.objects.create(
            employee=self.employee,
            supervisor=self.supervisor,
            status='DRAFT',
            overall_comments='Initial improvement plan'
        )

    def test_valid_plan_data(self):
        form_data = {
            'status': 'IN_PROGRESS',
            'end_date': (timezone.now() + timedelta(days=90)).date(),
            'overall_comments': 'Plan to improve communication skills'
        }
        form = ImprovementPlanForm(data=form_data, instance=self.plan)
        self.assertTrue(form.is_valid())
        
    def test_missing_required_fields(self):
        form_data = {
            # Missing status
            'overall_comments': 'Plan to improve communication skills'
        }
        form = ImprovementPlanForm(data=form_data, instance=self.plan)
        self.assertFalse(form.is_valid())
        self.assertIn('status', form.errors)

class PersonalDevelopmentPlanFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.employee = CustomUser.objects.create_user(
            username=f'employee_pdp_{self.timestamp}',
            password='testpass123',
            role=CustomUser.EMPLOYEE
        )
        
        # Create a plan for testing
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

    def test_valid_plan_data(self):
        form_data = {
            'employee': self.employee.id,
            'competency_gap': 'Leadership Skills',
            'development_activities': 'Mentoring program',
            'timeline': '3 months',
            'expected_outcome': 'Team leadership skills',
            'progress': 25,
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timedelta(days=90)).date()
        }
        form = PersonalDevelopmentPlanForm(data=form_data)
        self.assertTrue(form.is_valid())
        
    def test_invalid_dates(self):
        form_data = {
            'employee': self.employee.id,
            'competency_gap': 'Project Management',
            'development_activities': 'Training course',
            'timeline': '6 months',
            'expected_outcome': 'Certification',
            'progress': 0,
            'start_date': timezone.now().date(),
            'end_date': timezone.now().date() - timedelta(days=1)  # End date before start date
        }
        form = PersonalDevelopmentPlanForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('end_date', form.errors)  # Verify the specific error field
        
    def test_invalid_progress_value(self):
        form_data = {
            'employee': self.employee.id,
            'competency_gap': 'Project Management',
            'development_activities': 'Training course',
            'timeline': '6 months',
            'expected_outcome': 'Certification',
            'progress': 101,  # Progress over 100%
            'start_date': timezone.now().date(),
            'end_date': (timezone.now() + timedelta(days=180)).date()
        }
        form = PersonalDevelopmentPlanForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('progress', form.errors)  # Verify the specific error field

class UserProfileFormTests(TestCase):
    def setUp(self):
        # Use a timestamp to ensure unique values
        self.timestamp = int(time.time())
        
        self.user = CustomUser.objects.create_user(
            username=f'user_profile_{self.timestamp}',
            password='testpass123',
            email=f'user_profile_{self.timestamp}@example.com',
            employee_id=f'EMP{self.timestamp}',
            persal_number=f'PER{self.timestamp}'
        )
        
        # Create a salary level for testing
        self.salary_level = SalaryLevel.objects.create(
            level=f'5{self.timestamp % 1000}',
            typical_titles='Senior Developer',
            notes='Technical specialist role'
        )

    def test_valid_profile_data(self):
        form_data = {
            'first_name': 'Updated',
            'last_name': 'User',
            'email': 'updated@example.com',
            'employee_id': 'EMP001',
            'persal_number': 'PER001',
            'department': 'IT',
            'job_title': 'Developer',
            'job_purpose': 'Software development',
            'school_directorate': 'Technology',
            'date_of_appointment': timezone.now().date(),
            'is_on_probation': False,
            'salary_level': self.salary_level.id
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertTrue(form.is_valid())
        
    def test_duplicate_persal_number(self):
        # Create another user with a different persal number
        other_user = CustomUser.objects.create_user(
            username='otheruser',
            password='testpass123',
            persal_number='PER002'
        )
        
        # Try to update our user with the other user's persal number
        form_data = {
            'first_name': 'Test',
            'last_name': 'User',
            'email': 'test@example.com',
            'persal_number': 'PER002'  # Already exists
        }
        form = UserProfileForm(data=form_data, instance=self.user)
        self.assertFalse(form.is_valid())
        self.assertIn('persal_number', form.errors) 