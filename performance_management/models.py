from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
    
    employee_id = models.CharField(max_length=20, unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=EMPLOYEE)
    department = models.CharField(max_length=100)
    job_title = models.CharField(max_length=100)
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

class PerformanceAgreement(models.Model):
    """Model for storing performance agreements and goals"""
    employee = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    agreement_date = models.DateField(default=timezone.now)
    kras = models.TextField(help_text="Key Result Areas")
    gafs = models.TextField(help_text="General Areas for Focus")
    objectives = models.TextField()
    status = models.CharField(max_length=20, choices=[
        ('DRAFT', 'Draft'),
        ('PENDING_APPROVAL', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed')
    ], default='DRAFT')

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
