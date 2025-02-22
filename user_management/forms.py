from django import forms
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm
from performance.models import CustomUser, SalaryLevel

class UserCreationForm(BaseUserCreationForm):
    class Meta:
        model = CustomUser
        fields = [
            'username',
            'password1',
            'password2',
            'first_name',
            'last_name',
            'email',
            'employee_id',
            'persal_number',
            'role',
            'department',
            'job_title',
            'job_purpose',
            'school_directorate',
            'date_of_appointment',
            'is_on_probation',
            'manager',
            'salary_level'
        ]
        widgets = {
            'date_of_appointment': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = CustomUser.objects.filter(role__in=['MANAGER', 'APPROVER'])
        self.fields['salary_level'].queryset = SalaryLevel.objects.all()
        
        # Make certain fields required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['employee_id'].required = True
        self.fields['persal_number'].required = True
        self.fields['department'].required = True
        self.fields['job_title'].required = True

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'employee_id',
            'persal_number',
            'role',
            'department',
            'job_title',
            'job_purpose',
            'school_directorate',
            'date_of_appointment',
            'is_on_probation',
            'manager',
            'salary_level'
        ]
        widgets = {
            'date_of_appointment': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = CustomUser.objects.filter(role__in=['MANAGER', 'APPROVER'])
        self.fields['salary_level'].queryset = SalaryLevel.objects.all()
        
        # Make certain fields required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['employee_id'].required = True
        self.fields['persal_number'].required = True
        self.fields['department'].required = True
        self.fields['job_title'].required = True 