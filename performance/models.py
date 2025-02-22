from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_save
from django.dispatch import receiver

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
    ROLE_CHOICES = [
        (EMPLOYEE, 'Employee'),
        (MANAGER, 'Manager'),
        (HR, 'HR'),
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
    salary_level = models.ForeignKey(SalaryLevel, on_delete=models.SET_NULL, null=True, blank=True)

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

class PerformanceAgreement(models.Model):
    """Model for storing performance agreements and goals"""
    DRAFT = 'DRAFT'
    PENDING_EMPLOYEE_RATING = 'PENDING_EMPLOYEE_RATING'
    PENDING_SUPERVISOR_RATING = 'PENDING_SUPERVISOR_RATING'
    PENDING_AGREEMENT = 'PENDING_AGREEMENT'
    PENDING_ADMIN_APPROVAL = 'PENDING_ADMIN_APPROVAL'
    COMPLETED = 'COMPLETED'
    REJECTED = 'REJECTED'

    STATUS_CHOICES = [
        (DRAFT, 'Draft'),
        (PENDING_EMPLOYEE_RATING, 'Pending Employee Self-Rating'),
        (PENDING_SUPERVISOR_RATING, 'Pending Supervisor Rating'),
        (PENDING_AGREEMENT, 'Pending Rating Agreement'),
        (PENDING_ADMIN_APPROVAL, 'Pending PMDS Administrator Approval'),
        (COMPLETED, 'Completed'),
        (REJECTED, 'Rejected'),
    ]

    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    supervisor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='supervised_agreements')
    pmds_administrator = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='administered_agreements')
    
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
    agreement_reached_date = models.DateTimeField(null=True, blank=True)
    admin_approved_date = models.DateTimeField(null=True, blank=True)
    
    # Overall Comments
    employee_comments = models.TextField(blank=True)
    supervisor_comments = models.TextField(blank=True)
    admin_comments = models.TextField(blank=True)
    
    # Rejection Details
    rejection_reason = models.TextField(blank=True)
    rejected_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='rejected_agreements')
    rejected_date = models.DateTimeField(null=True, blank=True)

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
        return self.status == self.PENDING_ADMIN_APPROVAL

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
    performance_agreement = models.ForeignKey(PerformanceAgreement, on_delete=models.CASCADE)
    self_rating = models.TextField()
    supervisor_rating = models.TextField()
    final_rating = models.CharField(max_length=20, choices=[
        ('EXCEEDS', 'Exceeds Expectations'),
        ('MEETS', 'Meets Expectations'),
        ('NEEDS_IMPROVEMENT', 'Needs Improvement'),
        ('UNSATISFACTORY', 'Unsatisfactory')
    ])
    comments = models.TextField()
    review_date = models.DateField(default=timezone.now)

    # Fields to display in list view
    display_fields = ['review_date', 'final_rating']

    @property
    def can_edit(self):
        """Check if the review can be edited"""
        return True  # You can customize this based on your business logic

    def __str__(self):
        return f"Mid-Year Review for {self.performance_agreement.employee.get_full_name()} ({self.review_date})"

class ImprovementPlan(models.Model):
    """Model for storing employee improvement plans"""
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    area_for_development = models.TextField()
    interventions = models.TextField()
    timeline = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('PENDING', 'Pending'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ], default='PENDING')
    approved_by = models.ForeignKey(CustomUser, related_name='approved_plans', on_delete=models.SET_NULL, null=True, blank=True)
    approval_date = models.DateField(null=True, blank=True)

    # Fields to display in list view
    display_fields = ['area_for_development', 'status']

    def __str__(self):
        return f"Improvement Plan for {self.employee.get_full_name()}"

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

    # Fields to display in list view
    display_fields = ['competency_gap', 'progress']

    def __str__(self):
        return f"Development Plan for {self.employee.get_full_name()}"

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
        return f"{self.get_notification_type_display()} for {self.recipient.get_full_name()}"

    def mark_as_read(self):
        if not self.read_at:
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
        max_length=20,
        choices=[
            ('DAILY', 'Daily'),
            ('WEEKLY', 'Weekly'),
            ('MONTHLY', 'Monthly'),
        ],
        default='WEEKLY'
    )

    def __str__(self):
        return f"Notification preferences for {self.user.get_full_name()}"

@receiver(post_save, sender=CustomUser)
def create_notification_preferences(sender, instance, created, **kwargs):
    """Create notification preferences for new users"""
    if created:
        NotificationPreference.objects.create(user=instance)
