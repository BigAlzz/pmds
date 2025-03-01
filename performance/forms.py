from django import forms
from .models import (
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    KeyResponsibilityArea,
    CustomUser,
    GenericAssessmentFactor,
    KRAMidYearRating,
    GAFMidYearRating,
    KRAFinalRating,
    GAFFinalRating,
    ImprovementPlanItem
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
    """Form for performance agreements"""
    class Meta:
        model = PerformanceAgreement
        fields = [
            'employee',
            'supervisor',
            'approver',
            'plan_start_date',
            'plan_end_date',
            'midyear_review_date',
            'final_assessment_date',
            'employee_comments',
            'supervisor_comments',
            'manager_comments',
            'batch_number'
        ]
        widgets = {
            'plan_start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'plan_end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'midyear_review_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'final_assessment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'supervisor_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'manager_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['supervisor'].queryset = CustomUser.objects.filter(role='MANAGER')
        self.fields['approver'].queryset = CustomUser.objects.filter(role='APPROVER')
        
        # Make certain fields required
        self.fields['employee'].required = True
        self.fields['supervisor'].required = True
        self.fields['approver'].required = True
        self.fields['plan_start_date'].required = True
        self.fields['plan_end_date'].required = True

class KRAMidYearRatingForm(forms.ModelForm):
    kra = forms.ModelChoiceField(queryset=KeyResponsibilityArea.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = KRAMidYearRating
        fields = [
            'kra',
            'employee_rating',
            'employee_comments',
            'employee_evidence',
            'employee_evidence_file',
            'supervisor_rating',
            'supervisor_comments',
            'agreed_rating'
        ]
        widgets = {
            'employee_rating': forms.Select(attrs={'class': 'form-select'}),
            'employee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'}),
            'supervisor_rating': forms.Select(attrs={'class': 'form-select'}),
            'supervisor_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'agreed_rating': forms.Select(attrs={'class': 'form-select'})
        }

class GAFMidYearRatingForm(forms.ModelForm):
    gaf = forms.ModelChoiceField(queryset=GenericAssessmentFactor.objects.all(), widget=forms.HiddenInput())

    class Meta:
        model = GAFMidYearRating
        fields = [
            'gaf',
            'employee_rating',
            'employee_comments',
            'employee_evidence',
            'employee_evidence_file',
            'supervisor_rating',
            'supervisor_comments'
        ]
        widgets = {
            'employee_rating': forms.Select(attrs={'class': 'form-select'}),
            'employee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'}),
            'supervisor_rating': forms.Select(attrs={'class': 'form-select'}),
            'supervisor_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

KRAMidYearRatingFormSet = forms.inlineformset_factory(
    MidYearReview,
    KRAMidYearRating,
    form=KRAMidYearRatingForm,
    extra=0,
    can_delete=False
)

GAFMidYearRatingFormSet = forms.inlineformset_factory(
    MidYearReview,
    GAFMidYearRating,
    form=GAFMidYearRatingForm,
    extra=0,
    can_delete=False
)

class MidYearReviewForm(forms.ModelForm):
    class Meta:
        model = MidYearReview
        fields = [
            'performance_agreement',
            'review_date',
            'employee_overall_comments',
            'supervisor_overall_comments',
            'evidence_document'
        ]
        widgets = {
            'review_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'supervisor_overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidence_document': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == CustomUser.EMPLOYEE:
                # Employees can only see their own agreements
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.filter(employee=user)
            elif user.role == CustomUser.MANAGER:
                # Managers can see agreements of their employees
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.filter(employee__manager=user)
            elif user.role == CustomUser.HR:
                # HR can see all agreements
                pass
            else:
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.none()

class ImprovementPlanForm(forms.ModelForm):
    class Meta:
        model = ImprovementPlan
        fields = [
            'status',
            'end_date',
            'overall_comments'
        ]
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

class ImprovementPlanItemForm(forms.ModelForm):
    class Meta:
        model = ImprovementPlanItem
        fields = [
            'area_for_development',
            'interventions',
            'timeline',
            'status'
        ]
        widgets = {
            'area_for_development': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'interventions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'timeline': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'})
        }

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
        widgets = {
            'competency_gap': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'development_activities': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'timeline': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'expected_outcome': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'progress': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100, 'value': 0}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make progress optional
        self.fields['progress'].required = False
        # Set default value for progress
        if not self.instance.pk:  # If this is a new instance
            self.initial['progress'] = 0

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        # Check that all required fields are provided
        required_fields = ['competency_gap', 'development_activities', 'timeline', 'expected_outcome', 'start_date', 'end_date']
        for field in required_fields:
            if not cleaned_data.get(field):
                self.add_error(field, f'This field is required.')
        
        # Validate date range if both dates are provided
        if start_date and end_date and start_date > end_date:
            self.add_error('end_date', 'End date must be after start date.')
        
        # Set default progress if not provided
        if 'progress' not in cleaned_data or cleaned_data['progress'] is None:
            cleaned_data['progress'] = 0
            
        return cleaned_data

class KRAFinalRatingForm(forms.ModelForm):
    class Meta:
        model = KRAFinalRating
        fields = [
            'kra',
            'employee_rating',
            'employee_comments',
            'employee_evidence',
            'employee_evidence_file',
            'supervisor_rating',
            'supervisor_comments',
            'agreed_rating'
        ]
        widgets = {
            'employee_rating': forms.Select(attrs={'class': 'form-select'}),
            'employee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'}),
            'supervisor_rating': forms.Select(attrs={'class': 'form-select'}),
            'supervisor_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'agreed_rating': forms.Select(attrs={'class': 'form-select'})
        }

class GAFFinalRatingForm(forms.ModelForm):
    class Meta:
        model = GAFFinalRating
        fields = [
            'gaf',
            'employee_rating',
            'employee_comments',
            'employee_evidence',
            'employee_evidence_file',
            'supervisor_rating',
            'supervisor_comments'
        ]
        widgets = {
            'employee_rating': forms.Select(attrs={'class': 'form-select'}),
            'employee_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employee_evidence_file': forms.FileInput(attrs={'class': 'form-control', 'accept': '.pdf,.doc,.docx,.txt,.jpg,.jpeg,.png'}),
            'supervisor_rating': forms.Select(attrs={'class': 'form-select'}),
            'supervisor_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 3})
        }

KRAFinalRatingFormSet = forms.inlineformset_factory(
    FinalReview,
    KRAFinalRating,
    form=KRAFinalRatingForm,
    extra=0,
    can_delete=False
)

GAFFinalRatingFormSet = forms.inlineformset_factory(
    FinalReview,
    GAFFinalRating,
    form=GAFFinalRatingForm,
    extra=0,
    can_delete=False
)

class FinalReviewForm(forms.ModelForm):
    class Meta:
        model = FinalReview
        fields = [
            'performance_agreement',
            'review_date',
            'employee_overall_comments',
            'supervisor_overall_comments',
            'evidence_document'
        ]
        widgets = {
            'review_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'employee_overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'supervisor_overall_comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidence_document': forms.FileInput(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            if user.role == CustomUser.EMPLOYEE:
                # Employees can only see their own agreements
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.filter(employee=user)
            elif user.role == CustomUser.MANAGER:
                # Managers can see agreements of their employees
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.filter(employee__manager=user)
            elif user.role == CustomUser.HR:
                # HR can see all agreements
                pass
            else:
                self.fields['performance_agreement'].queryset = PerformanceAgreement.objects.none() 