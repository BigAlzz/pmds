from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

class SalaryLevel(models.Model):
    """Model for storing salary level information"""
    LEVEL_CHOICES = [
        ('1', 'Level 1'),
        ('2', 'Level 2'),
        ('3', 'Level 3'),
        ('4', 'Level 4'),
        ('5', 'Level 5'),
        ('6', 'Level 6'),
        ('7', 'Level 7'),
        ('8', 'Level 8'),
        ('9', 'Level 9'),
        ('10', 'Level 10'),
        ('11', 'Level 11'),
        ('12', 'Level 12'),
        ('13', 'Level 13'),
        ('14', 'Level 14'),
        ('15', 'Level 15'),
        ('16', 'Level 16'),
    ]

    level = models.CharField(max_length=5, choices=LEVEL_CHOICES, unique=True)
    typical_titles = models.CharField(max_length=255)
    notes = models.TextField()
    numeric_level = models.IntegerField(editable=False)

    def save(self, *args, **kwargs):
        # Set the numeric level based on the level string
        self.numeric_level = int(self.level)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Level {self.level} - {self.typical_titles}"

    class Meta:
        ordering = ['numeric_level']

class CustomUser(AbstractUser):
    """Custom user model with employee-specific fields"""
    EMPLOYEE = 'EMPLOYEE'
    MANAGER = 'MANAGER'
    HR = 'HR'
    APPROVER = 'APPROVER'
    ROLE_CHOICES = [
        (EMPLOYEE, 'Employee'),
        (MANAGER, 'Manager'),
        (HR, 'HR'),
        (APPROVER, 'Approver'),
    ]
    
    employee_id = models.CharField(max_length=20, unique=True, null=True, blank=True)
    persal_number = models.CharField(max_length=20, unique=True, null=True, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=EMPLOYEE)
    department = models.CharField(max_length=100, null=True, blank=True)
    job_title = models.CharField(max_length=100, null=True, blank=True)
    job_purpose = models.TextField(blank=True)
    school_directorate = models.CharField(max_length=100, blank=True)
    date_of_appointment = models.DateField(null=True, blank=True)
    is_on_probation = models.BooleanField(default=False)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')
    manager_persal_number = models.CharField(max_length=20, blank=True)
    salary_level = models.ForeignKey('SalaryLevel', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_full_name()} ({self.persal_number if self.persal_number else self.username})"

class KeyResponsibilityArea(models.Model):
    """Model for storing individual KRAs and their measurements"""
    performance_agreement = models.ForeignKey('PerformanceAgreement', on_delete=models.CASCADE, related_name='kras')
    description = models.TextField(help_text="Description of the Key Responsibility Area")
    performance_objective = models.TextField(blank=True, null=True, help_text="Performance Objective/Output")
    weighting = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weighting out of 100")
    measurement = models.TextField(help_text="How this KRA will be measured/assessed")
    target_date = models.DateField(null=True, blank=True, help_text="Target date for completion")
    tools = models.TextField(blank=True, help_text="Tools required for this KRA")
    barriers = models.TextField(blank=True, help_text="Potential barriers or challenges")
    evidence_examples = models.TextField(blank=True, help_text="Examples of evidence that can be provided")
    
    # Self Assessment
    employee_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Employee self-rating out of 4")
    employee_comments = models.TextField(blank=True)
    supporting_documents = models.FileField(upload_to='kra_evidence/%Y/%m/', blank=True)
    evidence_uploaded_at = models.DateTimeField(auto_now=True)
    
    # Supervisor Assessment
    supervisor_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Supervisor rating out of 4")
    supervisor_comments = models.TextField(blank=True)
    
    # Final/Agreed Rating
    agreed_rating = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True, help_text="Final agreed rating out of 4")
    
    class Meta:
        ordering = ['performance_agreement', '-weighting']

    def __str__(self):
        return f"KRA: {self.description[:50]}..."

    def calculate_weighted_score(self):
        """Calculate the weighted score for this KRA"""
        if self.agreed_rating:
            return (self.weighting * self.agreed_rating) / 100
        return 0

    def calculate_progress(self):
        """Calculate the progress percentage for this KRA"""
        progress = 0
        
        # Check if evidence is uploaded
        if self.supporting_documents:
            progress += 30
            
        # Check if employee has rated and commented
        if self.employee_rating is not None and self.employee_comments:
            progress += 35
            
        # Check if supervisor has rated and commented
        if self.supervisor_rating is not None and self.supervisor_comments:
            progress += 35
            
        return progress

class PerformanceAgreement(models.Model):
    """Model for storing performance agreements and goals"""
    DRAFT = 'DRAFT'
    PENDING_EMPLOYEE_RATING = 'PENDING_EMPLOYEE_RATING'
    PENDING_SUPERVISOR_RATING = 'PENDING_SUPERVISOR_RATING'
    PENDING_SUPERVISOR_SIGNOFF = 'PENDING_SUPERVISOR_SIGNOFF'
    PENDING_MANAGER_APPROVAL = 'PENDING_MANAGER_APPROVAL'
    PENDING_HR_VERIFICATION = 'PENDING_HR_VERIFICATION'
    COMPLETED = 'COMPLETED'
    REJECTED = 'REJECTED'
    RETURNED_FOR_CORRECTION = 'RETURNED_FOR_CORRECTION'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_EMPLOYEE_RATING, 'Pending Employee Self-Rating'),
        (PENDING_SUPERVISOR_RATING, 'Pending Supervisor Rating'),
        (PENDING_SUPERVISOR_SIGNOFF, 'Pending Supervisor Sign-off'),
        (PENDING_MANAGER_APPROVAL, 'Pending Manager Approval'),
        (PENDING_HR_VERIFICATION, 'Pending HR Verification'),
        (COMPLETED, 'Completed'),
        (REJECTED, 'Rejected'),
        (RETURNED_FOR_CORRECTION, 'Returned for Correction'),
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='supervised_agreements')
    approver = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_agreements')
    pmds_administrator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='administered_agreements')
    hr_verifier = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_agreements')
    
    # Agreement Dates
    agreement_date = models.DateField(default=timezone.now)
    plan_start_date = models.DateField(null=True, blank=True)
    plan_end_date = models.DateField(null=True, blank=True)
    midyear_review_date = models.DateField(null=True, blank=True)
    final_assessment_date = models.DateField(null=True, blank=True)
    
    # Workflow Status
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=DRAFT)
    employee_submitted_date = models.DateTimeField(null=True, blank=True)
    supervisor_reviewed_date = models.DateTimeField(null=True, blank=True)
    supervisor_signoff_date = models.DateTimeField(null=True, blank=True)
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    hr_verification_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    
    # Overall Comments
    employee_comments = models.TextField(blank=True)
    supervisor_comments = models.TextField(blank=True)
    manager_comments = models.TextField(blank=True)
    hr_comments = models.TextField(blank=True)
    
    # Rejection Details
    rejection_reason = models.TextField(blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)
    
    # Return for Correction Details
    return_reason = models.TextField(blank=True)
    return_date = models.DateTimeField(null=True, blank=True)
    
    # Batch Processing for HR
    batch_number = models.CharField(max_length=50, blank=True, help_text="Batch number for HR processing")

    def __str__(self):
        employee_name = self.employee.get_full_name()
        if self.plan_start_date and self.plan_end_date:
            return f"Performance Agreement for {employee_name} ({self.plan_start_date.year}-{self.plan_end_date.year})"
        return f"Performance Agreement for {employee_name}"

    def calculate_total_score(self):
        """Calculate the total weighted score across all KRAs"""
        return sum(kra.calculate_weighted_score() for kra in self.kras.all())

    def validate_weightings(self):
        """Ensure KRA weightings total 100"""
        total_weighting = sum(kra.weighting for kra in self.kras.all())
        return abs(total_weighting - 100) < 0.01  # Allow for small decimal differences

    def can_submit_self_rating(self):
        """Check if employee can submit self-rating"""
        return self.status == self.PENDING_EMPLOYEE_RATING

    def can_submit_supervisor_rating(self):
        """Check if supervisor can submit rating"""
        return self.status == self.PENDING_SUPERVISOR_RATING

    def can_approve(self):
        """Check if PMDS administrator can approve"""
        return self.status == self.PENDING_MANAGER_APPROVAL

    def can_delete(self, user):
        """Check if the agreement can be deleted by the given user"""
        return (user.role == 'HR' and 
                self.status in [self.DRAFT, self.REJECTED])

class GenericAssessmentFactor(models.Model):
    """Model for storing Generic Assessment Factors (GAFs)"""
    GAF_CHOICES = [
        ('GAF1', 'Job knowledge'),
        ('GAF2', 'Technical skills'),
        ('GAF3', 'Acceptance of responsibility'),
        ('GAF4', 'Quality of work'),
        ('GAF5', 'Reliability'),
        ('GAF6', 'Initiative'),
        ('GAF7', 'Communication'),
        ('GAF8', 'Interpersonal relationships'),
        ('GAF9', 'Flexibility'),
        ('GAF10', 'Team work'),
        ('GAF11', 'Planning and execution'),
        ('GAF12', 'Leadership'),
        ('GAF13', 'Delegation and empowerment'),
        ('GAF14', 'Management of financial resources'),
        ('GAF15', 'Management of human resources'),
    ]

    performance_agreement = models.ForeignKey(PerformanceAgreement, on_delete=models.CASCADE, related_name='gafs')
    factor = models.CharField(max_length=50, choices=GAF_CHOICES)
    is_applicable = models.BooleanField(default=True)
    comments = models.TextField(blank=True)
    
    class Meta:
        ordering = ['factor']
        unique_together = ['performance_agreement', 'factor']

    def __str__(self):
        return f"{self.get_factor_display()} - {self.performance_agreement}"

class MidYearReview(models.Model):
    """Model for storing mid-year review data"""
    RATING_CHOICES = [
        (4, 'Performance Significantly Above Expectations (4)'),
        (3, 'Fully Effective Performance (3)'),
        (2, 'Performance Not Fully Effective (2)'),
        (1, 'Unacceptable Performance (1)')
    ]

    performance_agreement = models.ForeignKey(PerformanceAgreement, on_delete=models.CASCADE, related_name='midyear_reviews')
    review_date = models.DateField(default=timezone.now)
    
    # Status tracking
    status = models.CharField(max_length=30, choices=[
        ('DRAFT', 'Draft'),
        ('PENDING_EMPLOYEE_RATING', 'Pending Employee Self-Rating'),
        ('PENDING_SUPERVISOR_RATING', 'Pending Supervisor Rating'),
        ('PENDING_SUPERVISOR_SIGNOFF', 'Pending Supervisor Sign-off'),
        ('PENDING_MANAGER_APPROVAL', 'Pending Manager Approval'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected')
    ], default='DRAFT')

    # Dates
    employee_rating_date = models.DateTimeField(null=True, blank=True)
    supervisor_rating_date = models.DateTimeField(null=True, blank=True)
    supervisor_signoff_date = models.DateTimeField(null=True, blank=True)
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Overall Comments
    employee_overall_comments = models.TextField(blank=True, help_text="Employee's overall comments on the mid-year review")
    supervisor_overall_comments = models.TextField(blank=True, help_text="Supervisor's overall comments on the mid-year review")
    manager_comments = models.TextField(blank=True, help_text="Manager's comments on the mid-year review")
    
    # Evidence Document
    evidence_document = models.FileField(upload_to='midyear_review_evidence/', null=True, blank=True)

    class Meta:
        ordering = ['-review_date']

    def __str__(self):
        return f"Mid-Year Review for {self.performance_agreement.employee.get_full_name()} ({self.review_date})"

    def calculate_overall_rating(self):
        """Calculate the overall rating based on KRA and GAF ratings"""
        kra_ratings = self.kra_ratings.all()
        gaf_ratings = self.gaf_ratings.all()
        
        if not kra_ratings.exists():
            return None
            
        total_kra_score = sum(rating.calculate_weighted_score() for rating in kra_ratings)
        return total_kra_score

    @property
    def can_edit(self):
        """Check if the review can be edited based on status"""
        return self.status != 'COMPLETED'

class KRAMidYearRating(models.Model):
    """Model for storing KRA ratings for mid-year review"""
    midyear_review = models.ForeignKey(MidYearReview, on_delete=models.CASCADE, related_name='kra_ratings')
    kra = models.ForeignKey('KeyResponsibilityArea', on_delete=models.CASCADE)
    
    employee_rating = models.IntegerField(choices=MidYearReview.RATING_CHOICES, null=True, blank=True)
    employee_comments = models.TextField(blank=True)
    employee_evidence = models.TextField(blank=True, help_text="Description of evidence for the rating")
    employee_evidence_file = models.FileField(upload_to='kra_evidence/%Y/%m/%d/', null=True, blank=True)
    
    supervisor_rating = models.IntegerField(choices=MidYearReview.RATING_CHOICES, null=True, blank=True)
    supervisor_comments = models.TextField(blank=True)
    
    agreed_rating = models.IntegerField(choices=MidYearReview.RATING_CHOICES, null=True, blank=True, help_text="Final agreed rating between employee and supervisor")

    def __str__(self):
        return f"KRA Rating: {self.kra.description}"

    def get_evidence_filename(self):
        if self.employee_evidence_file:
            return os.path.basename(self.employee_evidence_file.name)
        return None

    def calculate_weighted_score(self):
        """Calculate the weighted score for this KRA"""
        if self.agreed_rating is not None:
            return (self.agreed_rating * self.kra.weighting) / 100
        elif self.supervisor_rating is not None:
            return (self.supervisor_rating * self.kra.weighting) / 100
        return 0

class GAFMidYearRating(models.Model):
    """Model for storing GAF ratings for mid-year review"""
    midyear_review = models.ForeignKey(MidYearReview, on_delete=models.CASCADE, related_name='gaf_ratings')
    gaf = models.ForeignKey('GenericAssessmentFactor', on_delete=models.CASCADE)
    
    employee_rating = models.IntegerField(choices=MidYearReview.RATING_CHOICES, null=True, blank=True)
    employee_comments = models.TextField(blank=True)
    employee_evidence = models.TextField(blank=True, help_text="Description of evidence for the rating")
    employee_evidence_file = models.FileField(upload_to='gaf_evidence/%Y/%m/%d/', null=True, blank=True)
    
    supervisor_rating = models.IntegerField(choices=MidYearReview.RATING_CHOICES, null=True, blank=True)
    supervisor_comments = models.TextField(blank=True)

    def __str__(self):
        return f"GAF Rating: {self.gaf.get_factor_display()}"

    def get_evidence_filename(self):
        if self.employee_evidence_file:
            return os.path.basename(self.employee_evidence_file.name)
        return None

class ImprovementPlanItem(models.Model):
    """Model for storing individual improvement items"""
    PERFORMANCE_AGREEMENT = 'PA'
    MIDYEAR_REVIEW = 'MYR'
    
    SOURCE_CHOICES = [
        (PERFORMANCE_AGREEMENT, 'Performance Agreement'),
        (MIDYEAR_REVIEW, 'Mid-Year Review'),
    ]

    improvement_plan = models.ForeignKey('ImprovementPlan', on_delete=models.CASCADE, related_name='items')
    area_for_development = models.TextField()
    source_type = models.CharField(max_length=3, choices=SOURCE_CHOICES)
    source_id = models.IntegerField(help_text="ID of the source object (PA or MYR)")
    source_gaf = models.ForeignKey('GenericAssessmentFactor', on_delete=models.SET_NULL, null=True, blank=True)
    interventions = models.TextField(blank=True)
    timeline = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ], default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Improvement Item: {self.area_for_development[:50]}..."
        
    def send_notification(self, notification_type, title, message):
        """Send a notification about this improvement plan item"""
        # Notify the employee
        Notification.objects.create(
            recipient=self.improvement_plan.employee,
            notification_type=notification_type,
            title=title,
            message=message,
            related_object_type='improvement_plan_item',
            related_object_id=self.id
        )
        
        # Notify the supervisor if available
        if self.improvement_plan.supervisor:
            Notification.objects.create(
                recipient=self.improvement_plan.supervisor,
                notification_type=notification_type,
                title=title,
                message=message,
                related_object_type='improvement_plan_item',
                related_object_id=self.id
            )

class ImprovementPlan(models.Model):
    """Model for storing employee improvement plans"""
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='supervised_improvement_plans')
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ], default='DRAFT')
    start_date = models.DateField(auto_now_add=True)
    end_date = models.DateField(null=True, blank=True)
    overall_comments = models.TextField(blank=True)
    approved_by = models.ForeignKey(CustomUser, related_name='approved_plans', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Improvement Plan for {self.employee.get_full_name()}"

    @property
    def can_edit(self):
        """Check if the plan can be edited"""
        return self.status != 'COMPLETED'

    @property
    def display_fields(self):
        """Fields to display in the list view"""
        return ['employee_name', 'status', 'start_date', 'end_date']
        
    @property
    def employee_name(self):
        """Return employee name for display in list"""
        return self.employee.get_full_name() if self.employee else ""

    def send_notification(self, notification_type, title, message):
        """Send a notification to the relevant users"""
        if notification_type == 'PLAN_UPDATE':
            # Notify the employee
            Notification.objects.create(
                recipient=self.employee,
                notification_type=notification_type,
                title=title,
                message=message,
                related_object_type='improvement_plan',
                related_object_id=self.id
            )
            
            # Notify the supervisor if available
            if self.supervisor:
                Notification.objects.create(
                    recipient=self.supervisor,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    related_object_type='improvement_plan',
                    related_object_id=self.id
                )
        elif notification_type == 'APPROVAL':
            # Notify the supervisor
            if self.supervisor:
                Notification.objects.create(
                    recipient=self.supervisor,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    related_object_type='improvement_plan',
                    related_object_id=self.id
                )

    @classmethod
    def get_or_create_current_plan(cls, employee):
        """Get the current improvement plan or create a new one"""
        current_plan = cls.objects.filter(
            employee=employee,
            status__in=['DRAFT', 'IN_PROGRESS']
        ).first()
        
        if not current_plan:
            current_plan = cls.objects.create(
                employee=employee,
                supervisor=employee.manager,
                status='DRAFT'
            )
        
        return current_plan

class PersonalDevelopmentPlan(models.Model):
    """Model for storing personal development plans"""
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    competency_gap = models.TextField()
    development_activities = models.TextField()
    timeline = models.TextField()
    expected_outcome = models.TextField()
    progress = models.IntegerField(help_text="Progress percentage", default=0)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(default=timezone.now)

    # Fields to display in list view - moved to property
    @property
    def display_fields(self):
        """Return fields to display in list view"""
        return ['employee', 'competency_gap', 'progress', 'start_date', 'end_date']

    def __str__(self):
        return f"Development Plan for {self.employee.get_full_name()}"
    
    @property
    def can_edit(self):
        """Check if the plan can be edited"""
        return True

class Feedback(models.Model):
    """Model for storing employee feedback"""
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    feedback = models.TextField()
    anonymous = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Feedback from {self.employee.get_full_name()}"

class AuditLog(models.Model):
    """Model for tracking changes in the system"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    model = models.CharField(max_length=50)
    instance_id = models.IntegerField()
    action = models.CharField(max_length=20, choices=[
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete')
    ])
    timestamp = models.DateTimeField(default=timezone.now)
    changes = models.TextField(help_text="JSON representation of changes")

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.action} {self.model}"

class Notification(models.Model):
    """Model for storing user notifications"""
    NOTIFICATION_TYPES = [
        ('REVIEW_DUE', 'Review Due'),
        ('PLAN_UPDATE', 'Plan Update'),
        ('FEEDBACK', 'Feedback Received'),
        ('APPROVAL', 'Approval Required'),
        ('REMINDER', 'General Reminder'),
    ]

    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    related_object_type = models.CharField(max_length=100, blank=True)  # e.g., 'performance_agreement', 'midyear_review'
    related_object_id = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    email_sent = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.recipient.get_full_name()}"

    def mark_as_read(self):
        self.read_at = timezone.now()
        self.save()

class NotificationPreference(models.Model):
    """Model for storing user notification preferences"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    email_notifications = models.BooleanField(default=True)
    review_reminders = models.BooleanField(default=True)
    plan_updates = models.BooleanField(default=True)
    feedback_notifications = models.BooleanField(default=True)
    reminder_frequency = models.CharField(
        max_length=10,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
        ],
        default='WEEKLY'
    )

    def __str__(self):
        return f"Notification Preferences for {self.user.get_full_name()}"

@receiver(post_save, sender=CustomUser)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationPreference.objects.create(user=instance)

class FinalReview(models.Model):
    """Model for storing year-end/final review data"""
    RATING_CHOICES = [
        (4, 'Performance Significantly Above Expectations (4)'),
        (3, 'Fully Effective Performance (3)'),
        (2, 'Performance Not Fully Effective (2)'),
        (1, 'Unacceptable Performance (1)')
    ]

    performance_agreement = models.ForeignKey(PerformanceAgreement, on_delete=models.CASCADE, related_name='final_reviews')
    review_date = models.DateField(default=timezone.now)
    
    # Status tracking
    status = models.CharField(max_length=30, choices=[
        ('DRAFT', 'Draft'),
        ('PENDING_EMPLOYEE_RATING', 'Pending Employee Self-Rating'),
        ('PENDING_SUPERVISOR_RATING', 'Pending Supervisor Rating'),
        ('PENDING_SUPERVISOR_SIGNOFF', 'Pending Supervisor Sign-off'),
        ('PENDING_MANAGER_APPROVAL', 'Pending Manager Approval'),
        ('COMPLETED', 'Completed'),
        ('REJECTED', 'Rejected')
    ], default='DRAFT')

    # Dates
    employee_rating_date = models.DateTimeField(null=True, blank=True)
    supervisor_rating_date = models.DateTimeField(null=True, blank=True)
    supervisor_signoff_date = models.DateTimeField(null=True, blank=True)
    manager_approval_date = models.DateTimeField(null=True, blank=True)
    completion_date = models.DateTimeField(null=True, blank=True)
    rejection_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Overall Comments
    employee_overall_comments = models.TextField(blank=True, help_text="Employee's overall comments on the final review")
    supervisor_overall_comments = models.TextField(blank=True, help_text="Supervisor's overall comments on the final review")
    manager_comments = models.TextField(blank=True, help_text="Manager's comments on the final review")
    
    # Evidence Document
    evidence_document = models.FileField(upload_to='final_review_evidence/', null=True, blank=True)

    class Meta:
        ordering = ['-review_date']

    def __str__(self):
        return f"Year-End Review for {self.performance_agreement.employee.get_full_name()} - {self.review_date}"

    def calculate_overall_rating(self):
        """Calculate the overall rating based on KRA ratings and weights"""
        kra_ratings = self.kra_ratings.all()
        if not kra_ratings:
            return None
        
        total_weight = 0
        weighted_sum = 0
        
        for rating in kra_ratings:
            if rating.agreed_rating:
                weighted_sum += rating.kra.weighting * rating.agreed_rating
                total_weight += rating.kra.weighting
            elif rating.supervisor_rating:
                weighted_sum += rating.kra.weighting * rating.supervisor_rating
                total_weight += rating.kra.weighting
        
        if total_weight > 0:
            return weighted_sum / total_weight
        return None

    @property
    def can_edit(self):
        """Check if the review can be edited based on status"""
        return self.status != 'COMPLETED'

class KRAFinalRating(models.Model):
    """Model for storing KRA ratings for final review"""
    final_review = models.ForeignKey(FinalReview, on_delete=models.CASCADE, related_name='kra_ratings')
    kra = models.ForeignKey('KeyResponsibilityArea', on_delete=models.CASCADE)
    
    employee_rating = models.IntegerField(choices=FinalReview.RATING_CHOICES, null=True, blank=True)
    employee_comments = models.TextField(blank=True)
    employee_evidence = models.TextField(blank=True, help_text="Description of evidence for the rating")
    employee_evidence_file = models.FileField(upload_to='kra_final_evidence/%Y/%m/%d/', null=True, blank=True)
    
    supervisor_rating = models.IntegerField(choices=FinalReview.RATING_CHOICES, null=True, blank=True)
    supervisor_comments = models.TextField(blank=True)
    
    agreed_rating = models.IntegerField(choices=FinalReview.RATING_CHOICES, null=True, blank=True, help_text="Final agreed rating between employee and supervisor")

    def __str__(self):
        return f"KRA Rating for {self.kra.description[:30]}... in {self.final_review}"

    def get_evidence_filename(self):
        """Get the filename of the evidence file"""
        if self.employee_evidence_file:
            return os.path.basename(self.employee_evidence_file.name)
        return None

    def calculate_weighted_score(self):
        """Calculate the weighted score for this KRA"""
        if self.agreed_rating:
            return (self.kra.weighting * self.agreed_rating) / 100
        elif self.supervisor_rating:
            return (self.kra.weighting * self.supervisor_rating) / 100
        return 0

class GAFFinalRating(models.Model):
    """Model for storing GAF ratings for final review"""
    final_review = models.ForeignKey(FinalReview, on_delete=models.CASCADE, related_name='gaf_ratings')
    gaf = models.ForeignKey('GenericAssessmentFactor', on_delete=models.CASCADE)
    
    employee_rating = models.IntegerField(choices=FinalReview.RATING_CHOICES, null=True, blank=True)
    employee_comments = models.TextField(blank=True)
    employee_evidence = models.TextField(blank=True, help_text="Description of evidence for the rating")
    employee_evidence_file = models.FileField(upload_to='gaf_final_evidence/%Y/%m/%d/', null=True, blank=True)
    
    supervisor_rating = models.IntegerField(choices=FinalReview.RATING_CHOICES, null=True, blank=True)
    supervisor_comments = models.TextField(blank=True)

    def __str__(self):
        return f"GAF Rating for {self.gaf.get_factor_display()} in {self.final_review}"

    def get_evidence_filename(self):
        """Get the filename of the evidence file"""
        if self.employee_evidence_file:
            return os.path.basename(self.employee_evidence_file.name)
        return None

class AuditTrail(models.Model):
    """Model for tracking changes to performance agreements and user activities"""
    ACTION_CREATE = 'CREATE'
    ACTION_UPDATE = 'UPDATE'
    ACTION_DELETE = 'DELETE'
    ACTION_SUBMIT = 'SUBMIT'
    ACTION_APPROVE = 'APPROVE'
    ACTION_REJECT = 'REJECT'
    ACTION_VERIFY = 'VERIFY'
    ACTION_LOGIN = 'LOGIN'
    ACTION_LOGOUT = 'LOGOUT'
    
    ACTION_CHOICES = [
        (ACTION_CREATE, 'Create'),
        (ACTION_UPDATE, 'Update'),
        (ACTION_DELETE, 'Delete'),
        (ACTION_SUBMIT, 'Submit'),
        (ACTION_APPROVE, 'Approve'),
        (ACTION_REJECT, 'Reject'),
        (ACTION_VERIFY, 'Verify'),
        (ACTION_LOGIN, 'Login'),
        (ACTION_LOGOUT, 'Logout'),
    ]
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='audit_trails')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Related object information
    content_type = models.CharField(max_length=50, blank=True, help_text="Type of object affected (e.g., PerformanceAgreement)")
    object_id = models.PositiveIntegerField(null=True, blank=True, help_text="ID of the affected object")
    object_repr = models.CharField(max_length=200, blank=True, help_text="String representation of the affected object")
    
    # Additional details
    details = models.TextField(blank=True, help_text="Additional details about the action")
    
    class Meta:
        ordering = ['-timestamp']
        
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_action_display()} - {self.timestamp}"

# Add signal handlers to track user login/logout
@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    """Track user login"""
    if hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuditTrail.objects.create(
            user=user,
            action=AuditTrail.ACTION_LOGIN,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"User logged in from {ip_address}"
        )

@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    """Track user logout"""
    if user and hasattr(request, 'META'):
        ip_address = request.META.get('REMOTE_ADDR', None)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        AuditTrail.objects.create(
            user=user,
            action=AuditTrail.ACTION_LOGOUT,
            ip_address=ip_address,
            user_agent=user_agent,
            details=f"User logged out from {ip_address}"
        )
