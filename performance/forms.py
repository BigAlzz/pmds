from django import forms
from .models import (
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    KeyResponsibilityArea,
    CustomUser,
    GenericAssessmentFactor
)

class UserProfileForm(forms.ModelForm):
    """Form for user profile information"""
    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'employee_id',
            'persal_number',
            'department',
            'job_title',
            'job_purpose',
            'school_directorate',
            'date_of_appointment',
            'is_on_probation',
            'salary_level'
        ]
        labels = {
            'school_directorate': 'School/Directorate/Sub-Directorate'
        }
        widgets = {
            'date_of_appointment': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'salary_level': forms.Select(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'employee_id': forms.TextInput(attrs={'class': 'form-control'}),
            'persal_number': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'job_title': forms.TextInput(attrs={'class': 'form-control'}),
            'job_purpose': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'school_directorate': forms.TextInput(attrs={'class': 'form-control'}),
            'is_on_probation': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def clean(self):
        cleaned_data = super().clean()
        required_fields = ['first_name', 'last_name', 'email', 'employee_id', 'department', 'job_title']
        
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, 'This field is required to create performance agreements.')
        
        return cleaned_data

class KRAForm(forms.ModelForm):
    class Meta:
        model = KeyResponsibilityArea
        fields = [
            'description',
            'performance_objective',
            'weighting',
            'measurement',
            'target_date',
            'tools',
            'barriers',
            'evidence_examples'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Key Responsibility Area based on job description'}),
            'performance_objective': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Performance Objective/Output'}),
            'weighting': forms.NumberInput(attrs={'min': 0, 'max': 100, 'step': 0.01}),
            'measurement': forms.Textarea(attrs={'rows': 3, 'placeholder': 'How will this KRA be measured/assessed?'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'tools': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Tools required for this KRA'}),
            'barriers': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Potential barriers or challenges'}),
            'evidence_examples': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Examples of evidence that can be provided'})
        }

class KRAInlineFormSet(forms.models.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_weighting = sum(form.cleaned_data.get('weighting', 0) for form in self.forms if not form.cleaned_data.get('DELETE', False))
        if abs(total_weighting - 100) > 0.01:  # Allow for small decimal differences
            raise forms.ValidationError("Total weightings must add up to 100%")

KRAFormSet = forms.inlineformset_factory(
    PerformanceAgreement,
    KeyResponsibilityArea,
    form=KRAForm,
    formset=KRAInlineFormSet,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

class GAFForm(forms.ModelForm):
    class Meta:
        model = GenericAssessmentFactor
        fields = ['factor', 'is_applicable', 'comments']
        widgets = {
            'factor': forms.HiddenInput(),
            'comments': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Additional comments about this factor', 'class': 'form-control'}),
            'is_applicable': forms.CheckboxInput(attrs={'class': 'form-check-input'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance and instance.performance_agreement.status == 'COMPLETED':
            for field in self.fields.values():
                field.widget.attrs['disabled'] = 'disabled'
                field.widget.attrs['readonly'] = 'readonly'

GAFFormSet = forms.inlineformset_factory(
    PerformanceAgreement,
    GenericAssessmentFactor,
    form=GAFForm,
    extra=15,  # Create forms for all GAF choices
    can_delete=False,  # Cannot delete GAFs
    max_num=15,  # Maximum 15 GAFs
)

class PerformanceAgreementForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=PerformanceAgreement.STATUS_CHOICES,
        initial=PerformanceAgreement.DRAFT,
        widget=forms.Select(attrs={
            'class': 'form-select form-control',
            'style': 'width: 100%;'
        })
    )

    class Meta:
        model = PerformanceAgreement
        fields = [
            'plan_start_date',
            'plan_end_date',
            'midyear_review_date',
            'final_assessment_date',
            'status'
        ]
        widgets = {
            'plan_start_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'plan_end_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'midyear_review_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
            'final_assessment_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'placeholder': 'YYYY-MM-DD'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:  # If this is a new instance
            self.initial['status'] = PerformanceAgreement.DRAFT
        self.fields['status'].required = True
        self.fields['status'].label = 'Agreement Status'

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('plan_start_date')
        end_date = cleaned_data.get('plan_end_date')

        if start_date and end_date and end_date < start_date:
            raise forms.ValidationError("End date cannot be before start date")

        return cleaned_data

class MidYearReviewForm(forms.ModelForm):
    class Meta:
        model = MidYearReview
        fields = [
            'performance_agreement',
            'self_rating',
            'supervisor_rating',
            'final_rating',
            'comments',
            'review_date'
        ]

class ImprovementPlanForm(forms.ModelForm):
    class Meta:
        model = ImprovementPlan
        fields = [
            'area_for_development',
            'interventions',
            'timeline',
            'status'
        ]

class PersonalDevelopmentPlanForm(forms.ModelForm):
    class Meta:
        model = PersonalDevelopmentPlan
        fields = [
            'competency_gap',
            'development_activities',
            'timeline',
            'expected_outcome',
            'progress',
            'start_date',
            'end_date'
        ] 