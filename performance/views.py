from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.http import JsonResponse, HttpResponse
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.template.loader import get_template
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django import forms
from .models import (
    CustomUser,
    PerformanceAgreement,
    MidYearReview,
    ImprovementPlan,
    PersonalDevelopmentPlan,
    Feedback,
    Notification,
    NotificationPreference,
    KeyResponsibilityArea,
    GenericAssessmentFactor,
    KRAMidYearRating,
    GAFMidYearRating,
    ImprovementPlanItem,
    FinalReview,
    KRAFinalRating,
    GAFFinalRating
)
from .forms import (
    PerformanceAgreementForm,
    MidYearReviewForm,
    ImprovementPlanForm,
    PersonalDevelopmentPlanForm,
    KRAFormSet,
    GAFFormSet,
    UserProfileForm,
    KRAMidYearRatingForm,
    GAFMidYearRatingForm,
    KRAMidYearRatingFormSet,
    GAFMidYearRatingFormSet,
    FinalReviewForm,
    KRAFinalRatingFormSet,
    GAFFinalRatingFormSet,
    KRAFinalRatingForm,
    GAFFinalRatingForm,
    ImprovementPlanItemForm
)
from .notifications import notify_user
from django.db.models import Q
from django.core.exceptions import PermissionDenied

# Dashboard views
@login_required
def dashboard(request):
    print(f"Dashboard - Current user: {request.user.username}, Role: {request.user.role}, ID: {request.user.id}")
    
    context = {
        'performance_agreements': PerformanceAgreement.objects.filter(employee=request.user),
        'reviews': MidYearReview.objects.filter(performance_agreement__employee=request.user),
        'final_reviews': FinalReview.objects.filter(performance_agreement__employee=request.user),
        'improvement_plans': ImprovementPlan.objects.filter(employee=request.user),
        'development_plans': PersonalDevelopmentPlan.objects.filter(employee=request.user),
    }
    print(f"Development plans for user: {context['development_plans'].count()}")
    return render(request, 'performance/dashboard.html', context)

@login_required
def profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('performance:profile')
    else:
        form = UserProfileForm(instance=request.user)
    
    return render(request, 'performance/profile.html', {
        'form': form,
        'user': request.user
    })

# Performance Agreement views
class PerformanceAgreementListView(LoginRequiredMixin, ListView):
    model = PerformanceAgreement
    template_name = 'performance/performance_agreement_list.html'
    context_object_name = 'agreements'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PerformanceAgreement.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PerformanceAgreement.objects.filter(employee__manager=self.request.user)
        return PerformanceAgreement.objects.filter(employee=self.request.user)

class PerformanceAgreementCreateView(LoginRequiredMixin, CreateView):
    model = PerformanceAgreement
    form_class = PerformanceAgreementForm
    template_name = 'performance/performance_agreement_form.html'
    success_url = reverse_lazy('performance:performance_agreement_list')

    def dispatch(self, request, *args, **kwargs):
        # Check if user profile is complete
        required_fields = ['first_name', 'last_name', 'email', 'employee_id', 'department', 'job_title']
        for field in required_fields:
            if not getattr(request.user, field):
                messages.warning(request, 'Please complete your profile before creating a performance agreement.')
                return redirect('performance:profile')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['kra_formset'] = KRAFormSet(self.request.POST)
            context['gaf_formset'] = GAFFormSet(self.request.POST)
        else:
            context['kra_formset'] = KRAFormSet()
            # Create GAF instances with proper display values
            initial_gafs = []
            for factor, display in GenericAssessmentFactor.GAF_CHOICES:
                initial_gafs.append({
                    'factor': factor,
                    'is_applicable': False,
                })
            context['gaf_formset'] = GAFFormSet(
                initial=initial_gafs
            )
        context['user_profile'] = self.request.user
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']
        
        if kra_formset.is_valid() and gaf_formset.is_valid():
            self.object = form.save(commit=False)
            self.object.employee = self.request.user
            self.object.supervisor = self.request.user.manager
            self.object.save()
            
            kra_formset.instance = self.object
            kra_ratings = kra_formset.save(commit=False)
            for rating in kra_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            gaf_formset.instance = self.object
            gaf_ratings = gaf_formset.save(commit=False)
            for rating in gaf_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            messages.success(self.request, 'Performance Agreement created successfully!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class PerformanceAgreementDetailView(LoginRequiredMixin, DetailView):
    model = PerformanceAgreement
    template_name = 'performance/performance_agreement_detail.html'
    context_object_name = 'agreement'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PerformanceAgreement.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PerformanceAgreement.objects.filter(employee__manager=self.request.user)
        return PerformanceAgreement.objects.filter(employee=self.request.user)

class PerformanceAgreementUpdateView(LoginRequiredMixin, UpdateView):
    model = PerformanceAgreement
    form_class = PerformanceAgreementForm
    template_name = 'performance/performance_agreement_form.html'
    success_url = reverse_lazy('performance:performance_agreement_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PerformanceAgreement.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PerformanceAgreement.objects.filter(
                Q(supervisor=self.request.user) | 
                Q(employee__manager=self.request.user)
            )
        return PerformanceAgreement.objects.filter(employee=self.request.user)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        if self.request.user.role == CustomUser.HR:
            # HR can edit all fields
            pass
        elif self.request.user.role == CustomUser.MANAGER:
            # Manager can edit supervisor comments and some fields
            for field in list(form.fields.keys()):
                if field not in ['supervisor_comments', 'manager_comments', 'status', 'plan_start_date', 'plan_end_date']:
                    form.fields[field].disabled = True
        else:
            # Employee can only edit their comments and submit
            for field in list(form.fields.keys()):
                if field not in ['employee_comments']:
                    form.fields[field].disabled = True
        return form

    def form_valid(self, form):
        agreement = form.instance
        user = self.request.user
        
        # Check if the form has a 'submit_action' field to determine the action
        submit_action = self.request.POST.get('submit_action', 'save')
        
        # Handle different submission actions
        if submit_action == 'submit_for_signoff':
            # Both employee and supervisor have entered their information, submit for supervisor sign-off
            agreement.status = PerformanceAgreement.PENDING_SUPERVISOR_SIGNOFF
            agreement.employee_submitted_date = timezone.now()
            agreement.supervisor_reviewed_date = timezone.now()
            messages.success(self.request, 'Performance Agreement submitted for supervisor sign-off.')
        
        elif submit_action == 'supervisor_signoff':
            # Supervisor is signing off on the agreement
            if user == agreement.supervisor:
                agreement.status = PerformanceAgreement.PENDING_MANAGER_APPROVAL
                agreement.supervisor_signoff_date = timezone.now()
                messages.success(self.request, 'Performance Agreement signed off and submitted for manager approval.')
            else:
                messages.error(self.request, 'Only the supervisor can sign off on this agreement.')
        
        elif submit_action == 'manager_approve':
            # Manager is approving the agreement
            if user.role == CustomUser.MANAGER and user == agreement.supervisor.manager:
                agreement.status = PerformanceAgreement.COMPLETED
                agreement.manager_approval_date = timezone.now()
                agreement.completion_date = timezone.now()
                messages.success(self.request, 'Performance Agreement approved and completed.')
            else:
                messages.error(self.request, 'Only the manager can approve this agreement.')
        
        elif submit_action == 'reject':
            # Rejecting the agreement (can be done by supervisor or manager)
            rejection_reason = self.request.POST.get('rejection_reason', '')
            if user == agreement.supervisor or (user.role == CustomUser.MANAGER and user == agreement.supervisor.manager):
                agreement.status = PerformanceAgreement.REJECTED
                agreement.rejection_date = timezone.now()
                agreement.rejection_reason = rejection_reason
                messages.success(self.request, 'Performance Agreement has been rejected.')
            else:
                messages.error(self.request, 'You do not have permission to reject this agreement.')
        
        else:
            # Just saving the form without changing status
            messages.success(self.request, 'Performance Agreement saved successfully.')

        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        agreement = self.get_object()
        context['can_approve'] = (
            self.request.user.role == CustomUser.MANAGER and 
            agreement.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL and
            self.request.user == agreement.supervisor.manager
        )
        return context

@login_required
def performance_agreement_submit(request, pk):
    """Submit performance agreement for supervisor approval"""
    if request.method == 'POST':
        agreement = get_object_or_404(PerformanceAgreement, pk=pk)
        
        # Verify user is the agreement owner
        if agreement.employee != request.user:
            messages.error(request, 'You do not have permission to submit this agreement.')
            return redirect('performance:performance_agreement_detail', pk=pk)
        
        # Update status
        agreement.status = PerformanceAgreement.PENDING_AGREEMENT
        agreement.employee_submitted_date = timezone.now()
        agreement.save()
        
        # Notify supervisor
        if agreement.supervisor:
            notify_user(
                user=agreement.supervisor,
                notification_type='APPROVAL',
                title='Performance Agreement Needs Approval',
                message=f'A performance agreement from {agreement.employee.get_full_name()} needs your approval.',
                related_object_type='performance_agreement',
                related_object_id=agreement.id
            )
        
        messages.success(request, 'Performance agreement submitted for approval.')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    return redirect('performance:performance_agreement_detail', pk=pk)

# Mid-Year Review views
class MidYearReviewListView(LoginRequiredMixin, ListView):
    model = MidYearReview
    template_name = 'performance/midyear_review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return MidYearReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return MidYearReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return MidYearReview.objects.filter(performance_agreement__employee=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mid-Year Reviews'
        context['create_url'] = 'midyear_review_create'
        context['detail_url'] = 'midyear_review_detail'
        context['update_url'] = 'midyear_review_update'
        context['headers'] = ['Review Date', 'Final Rating']
        return context

class MidYearReviewCreateView(LoginRequiredMixin, CreateView):
    model = MidYearReview
    form_class = MidYearReviewForm
    template_name = 'performance/midyear_review_form.html'
    success_url = reverse_lazy('performance:midyear_review_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the performance agreement if it's in POST data or GET parameters
        performance_agreement_id = None
        if self.request.POST:
            performance_agreement_id = self.request.POST.get('performance_agreement')
        elif 'performance_agreement' in self.request.GET:
            performance_agreement_id = self.request.GET.get('performance_agreement')
            
        performance_agreement = None
        if performance_agreement_id:
            try:
                performance_agreement = PerformanceAgreement.objects.select_related(
                    'employee', 'supervisor'
                ).prefetch_related(
                    'kras', 
                    'gafs'
                ).get(id=performance_agreement_id)
                
                # Set the performance agreement in the form's initial data
                if not self.request.POST:  # Only set initial data if not a POST request
                    context['form'].initial = {
                        'performance_agreement': performance_agreement,
                        'review_date': timezone.now().date()
                    }
            except PerformanceAgreement.DoesNotExist:
                pass

        if self.request.POST:
            context['kra_formset'] = KRAMidYearRatingFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object if hasattr(self, 'object') else None
            )
            context['gaf_formset'] = GAFMidYearRatingFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object if hasattr(self, 'object') else None
            )
        else:
            # Initialize empty formsets
            context['kra_formset'] = KRAMidYearRatingFormSet(
                instance=self.object if hasattr(self, 'object') else None,
                queryset=KRAMidYearRating.objects.none()
            )
            context['gaf_formset'] = GAFMidYearRatingFormSet(
                instance=self.object if hasattr(self, 'object') else None,
                queryset=GAFMidYearRating.objects.none()
            )

            # If we have a performance agreement, pre-populate the formsets
            if performance_agreement:
                # Create KRA formset with initial data
                kra_forms = []
                for kra in performance_agreement.kras.all():
                    form_data = {
                        'kra': kra.id,
                        'employee_rating': None,
                        'supervisor_rating': None,
                        'employee_comments': '',
                        'supervisor_comments': '',
                        'employee_evidence': ''
                    }
                    form = KRAMidYearRatingForm(initial=form_data)
                    form.fields['kra'].initial = kra.id
                    form.fields['kra'].queryset = KeyResponsibilityArea.objects.filter(id=kra.id)
                    kra_forms.append(form)
                context['kra_formset'].forms = kra_forms
                context['kra_formset'].extra = 0

                # Create GAF formset with initial data - only for applicable GAFs
                gaf_forms = []
                applicable_gafs = performance_agreement.gafs.filter(is_applicable=True)
                for gaf in applicable_gafs:
                    form_data = {
                        'gaf': gaf.id,
                        'employee_rating': None,
                        'supervisor_rating': None,
                        'employee_comments': '',
                        'supervisor_comments': '',
                        'employee_evidence': ''
                    }
                    form = GAFMidYearRatingForm(initial=form_data)
                    form.fields['gaf'].initial = gaf.id
                    form.fields['gaf'].queryset = GenericAssessmentFactor.objects.filter(id=gaf.id)
                    gaf_forms.append(form)
                context['gaf_formset'].forms = gaf_forms
                context['gaf_formset'].extra = 0

                # Add management form data
                context['kra_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(kra_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
                context['gaf_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(gaf_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
        
        # Add performance agreement to context if it exists
        if performance_agreement:
            context['performance_agreement'] = performance_agreement

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']

        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Save the main form first to get the instance
            self.object = form.save()
            
            # Save KRA ratings
            kra_formset.instance = self.object
            kra_ratings = kra_formset.save(commit=False)
            for rating in kra_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            # Save GAF ratings
            gaf_formset.instance = self.object
            gaf_ratings = gaf_formset.save(commit=False)
            for rating in gaf_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            messages.success(self.request, 'Mid-year review created successfully.')
            return redirect(self.success_url)
        else:
            # Print formset errors for debugging
            if not kra_formset.is_valid():
                for i, form in enumerate(kra_formset.forms):
                    if form.errors:
                        print(f"KRA Form {i} errors: {form.errors}")
            if not gaf_formset.is_valid():
                for i, form in enumerate(gaf_formset.forms):
                    if form.errors:
                        print(f"GAF Form {i} errors: {form.errors}")
            return self.form_invalid(form)

class MidYearReviewDetailView(LoginRequiredMixin, DetailView):
    model = MidYearReview
    template_name = 'performance/midyear_review_detail.html'
    context_object_name = 'review'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return MidYearReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return MidYearReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return MidYearReview.objects.filter(performance_agreement__employee=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.object.can_edit
        context['is_employee'] = self.request.user == self.object.performance_agreement.employee
        context['is_supervisor'] = self.request.user == self.object.performance_agreement.supervisor
        return context

class MidYearReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = MidYearReview
    form_class = MidYearReviewForm
    template_name = 'performance/midyear_review_form.html'
    success_url = reverse_lazy('performance:midyear_review_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure the performance agreement is in the context
        performance_agreement = self.object.performance_agreement
        context['performance_agreement'] = performance_agreement
        
        if self.request.POST:
            context['kra_formset'] = KRAMidYearRatingFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
            context['gaf_formset'] = GAFMidYearRatingFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
        else:
            # Get existing KRA ratings for this review
            existing_kra_ratings = KRAMidYearRating.objects.filter(midyear_review=self.object)
            existing_kra_ids = existing_kra_ratings.values_list('kra_id', flat=True)
            
            # Get existing GAF ratings for this review
            existing_gaf_ratings = GAFMidYearRating.objects.filter(midyear_review=self.object)
            existing_gaf_ids = existing_gaf_ratings.values_list('gaf_id', flat=True)
            
            # Check if we need to add ratings for any new KRAs that might have been added to the agreement
            if performance_agreement:
                # Identify KRAs in the agreement that don't have ratings yet
                missing_kras = performance_agreement.kras.exclude(id__in=existing_kra_ids)
                
                # Create new ratings for missing KRAs
                for kra in missing_kras:
                    KRAMidYearRating.objects.create(
                        midyear_review=self.object,
                        kra=kra
                    )
                
                # Identify applicable GAFs in the agreement that don't have ratings yet
                missing_gafs = performance_agreement.gafs.filter(
                    is_applicable=True
                ).exclude(id__in=existing_gaf_ids)
                
                # Create new ratings for missing GAFs
                for gaf in missing_gafs:
                    GAFMidYearRating.objects.create(
                        midyear_review=self.object,
                        gaf=gaf
                    )
            
            # Initialize formsets with updated instances
            context['kra_formset'] = KRAMidYearRatingFormSet(instance=self.object)
            context['gaf_formset'] = GAFMidYearRatingFormSet(instance=self.object)
            
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']

        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Save the main form first to get the instance
            self.object = form.save(commit=False)
            
            # Get the current user and status
            user = self.request.user
            current_status = self.object.status
            
            # Check if the form has a 'submit_action' field to determine the action
            submit_action = self.request.POST.get('submit_action', 'save')
            
            # Handle different submission actions
            if submit_action == 'submit_for_signoff':
                # Both employee and supervisor ratings have been entered, submit for supervisor sign-off
                self.object.status = 'PENDING_SUPERVISOR_SIGNOFF'
                self.object.employee_rating_date = timezone.now()
                self.object.supervisor_rating_date = timezone.now()
                messages.success(self.request, 'Mid-year review submitted for supervisor sign-off.')
            
            elif submit_action == 'supervisor_signoff':
                # Supervisor is signing off on the review
                if user == self.object.performance_agreement.supervisor:
                    self.object.status = 'PENDING_MANAGER_APPROVAL'
                    self.object.supervisor_signoff_date = timezone.now()
                    messages.success(self.request, 'Mid-year review signed off and submitted for manager approval.')
                else:
                    messages.error(self.request, 'Only the supervisor can sign off on this review.')
            
            elif submit_action == 'manager_approve':
                # Manager is approving the review
                if user.role == CustomUser.MANAGER and user == self.object.performance_agreement.supervisor.manager:
                    self.object.status = 'COMPLETED'
                    self.object.manager_approval_date = timezone.now()
                    self.object.completion_date = timezone.now()
                    messages.success(self.request, 'Mid-year review approved and completed.')
                else:
                    messages.error(self.request, 'Only the manager can approve this review.')
            
            elif submit_action == 'reject':
                # Rejecting the review (can be done by supervisor or manager)
                rejection_reason = self.request.POST.get('rejection_reason', '')
                if user == self.object.performance_agreement.supervisor or (user.role == CustomUser.MANAGER and user == self.object.performance_agreement.supervisor.manager):
                    self.object.status = 'REJECTED'
                    self.object.rejection_date = timezone.now()
                    self.object.rejection_reason = rejection_reason
                    messages.success(self.request, 'Mid-year review has been rejected.')
                else:
                    messages.error(self.request, 'You do not have permission to reject this review.')
            
            else:
                # Just saving the form without changing status
                messages.success(self.request, 'Mid-year review saved successfully.')
            
            # Save the main object first
            self.object.save()
            
            # Now save the formsets with the updated instance
            kra_formset.instance = self.object
            kra_ratings = kra_formset.save(commit=False)
            for rating in kra_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            # Save any deleted KRA ratings
            for obj in kra_formset.deleted_objects:
                obj.delete()
            
            # Save GAF ratings
            gaf_formset.instance = self.object
            gaf_ratings = gaf_formset.save(commit=False)
            for rating in gaf_ratings:
                rating.midyear_review = self.object
                rating.save()
            
            # Save any deleted GAF ratings
            for obj in gaf_formset.deleted_objects:
                obj.delete()
            
            # For 'save' action, redirect back to the same page instead of the list view
            if submit_action == 'save':
                return redirect('performance:midyear_review_update', pk=self.object.pk)
            
            return redirect(self.success_url)
        else:
            # Print formset errors for debugging
            if not kra_formset.is_valid():
                for i, form in enumerate(kra_formset.forms):
                    if form.errors:
                        print(f"KRA Form {i} errors: {form.errors}")
            if not gaf_formset.is_valid():
                for i, form in enumerate(gaf_formset.forms):
                    if form.errors:
                        print(f"GAF Form {i} errors: {form.errors}")
            return self.form_invalid(form)

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return MidYearReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return MidYearReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return MidYearReview.objects.filter(performance_agreement__employee=self.request.user)

@login_required
def midyear_review_delete(request, pk):
    """Delete a mid-year review"""
    review = get_object_or_404(MidYearReview, pk=pk)
    
    # Check if user has permission to delete
    if not (request.user == review.performance_agreement.employee or 
            request.user == review.performance_agreement.supervisor or 
            request.user.role == CustomUser.HR):
        messages.error(request, 'You do not have permission to delete this review.')
        return redirect('performance:midyear_review_list')
    
    # Only allow deletion of draft reviews
    if review.status != 'DRAFT':
        messages.error(request, 'Only draft reviews can be deleted.')
        return redirect('performance:midyear_review_list')
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Mid-year review deleted successfully.')
        return redirect('performance:midyear_review_list')
    
    return redirect('performance:midyear_review_list')

# Improvement Plan views
class ImprovementPlanListView(LoginRequiredMixin, ListView):
    model = ImprovementPlan
    template_name = 'performance/improvement_plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return ImprovementPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return ImprovementPlan.objects.filter(employee__manager=self.request.user)
        return ImprovementPlan.objects.filter(employee=self.request.user)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Improvement Plans'
        context['item_name'] = 'Improvement Plan'
        context['create_url'] = 'improvement_plan_create'
        context['detail_url'] = 'improvement_plan_detail'
        context['update_url'] = 'improvement_plan_update'
        return context

class ImprovementPlanCreateView(LoginRequiredMixin, CreateView):
    model = ImprovementPlan
    form_class = ImprovementPlanForm
    template_name = 'performance/improvement_plan_form.html'
    success_url = reverse_lazy('performance:improvement_plan_list')

    def form_valid(self, form):
        print("Form is valid, saving development plan...")
        print(f"Form data: {form.cleaned_data}")
        print(f"Current user: {self.request.user.username}, ID: {self.request.user.id}")
        
        # Set the employee to the current user
        form.instance.employee = self.request.user
        
        # Ensure progress is set if not provided
        if 'progress' not in form.cleaned_data or form.cleaned_data['progress'] is None:
            form.instance.progress = 0
            
        # Save the form
        response = super().form_valid(form)
        print(f"Development plan saved with ID: {form.instance.id}")
        
        # Redirect to the list view
        return response

    def form_invalid(self, form):
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        for field, errors in form.errors.items():
            print(f"Field '{field}' errors: {errors}")
        return super().form_invalid(form)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("Rendering development plan form...")
        return context

class ImprovementPlanDetailView(LoginRequiredMixin, DetailView):
    model = ImprovementPlan
    template_name = 'performance/improvement_plan_detail.html'
    context_object_name = 'plan'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return ImprovementPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return ImprovementPlan.objects.filter(employee__manager=self.request.user)
        return ImprovementPlan.objects.filter(employee=self.request.user)

class ImprovementPlanUpdateView(LoginRequiredMixin, UpdateView):
    model = ImprovementPlan
    form_class = ImprovementPlanForm
    template_name = 'performance/improvement_plan_form.html'
    success_url = reverse_lazy('performance:improvement_plan_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return ImprovementPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return ImprovementPlan.objects.filter(employee__manager=self.request.user)
        return ImprovementPlan.objects.filter(employee=self.request.user)
    
    def form_valid(self, form):
        old_status = self.get_object().status
        response = super().form_valid(form)
        
        # Check if status changed to COMPLETED
        if old_status != 'COMPLETED' and form.instance.status == 'COMPLETED':
            # Send completion notification
            self.object.send_notification(
                'PLAN_UPDATE',
                'Improvement Plan Completed',
                f'The improvement plan for {self.object.employee.get_full_name()} has been marked as completed.'
            )
        elif form.has_changed():
            # Send update notification
            self.object.send_notification(
                'PLAN_UPDATE',
                'Improvement Plan Updated',
                f'The improvement plan for {self.object.employee.get_full_name()} has been updated.'
            )
        
        return response

class ImprovementPlanItemCreateView(LoginRequiredMixin, CreateView):
    model = ImprovementPlanItem
    template_name = 'performance/improvement_plan_item_form.html'
    form_class = ImprovementPlanItemForm
    
    def get_success_url(self):
        return reverse_lazy('performance:improvement_plan_detail', kwargs={'pk': self.object.improvement_plan.pk})
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Pre-populate the form with the improvement plan
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        if 'plan_id' in self.kwargs:
            kwargs['initial']['improvement_plan'] = self.kwargs['plan_id']
        return kwargs
    
    def form_valid(self, form):
        # Set the improvement plan
        if 'plan_id' in self.kwargs:
            plan = get_object_or_404(ImprovementPlan, pk=self.kwargs['plan_id'])
            # Check permissions
            if not (self.request.user == plan.employee or 
                    self.request.user == plan.supervisor or 
                    self.request.user.role == CustomUser.HR):
                raise PermissionDenied
            form.instance.improvement_plan = plan
        
        response = super().form_valid(form)
        
        # Send notification
        self.object.send_notification(
            'PLAN_UPDATE',
            'New Improvement Item Added',
            f'A new improvement item has been added to the plan for {self.object.improvement_plan.employee.get_full_name()}.'
        )
        
        return response

class ImprovementPlanItemUpdateView(LoginRequiredMixin, UpdateView):
    model = ImprovementPlanItem
    template_name = 'performance/improvement_plan_item_form.html'
    form_class = ImprovementPlanItemForm
    
    def get_success_url(self):
        return reverse_lazy('performance:improvement_plan_detail', kwargs={'pk': self.object.improvement_plan.pk})
    
    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return ImprovementPlanItem.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return ImprovementPlanItem.objects.filter(improvement_plan__employee__manager=self.request.user)
        return ImprovementPlanItem.objects.filter(improvement_plan__employee=self.request.user)
    
    def form_valid(self, form):
        old_status = self.get_object().status
        response = super().form_valid(form)
        
        # Check if status changed to COMPLETED
        if old_status != 'COMPLETED' and form.instance.status == 'COMPLETED':
            # Send completion notification
            self.object.send_notification(
                'PLAN_UPDATE',
                'Improvement Item Completed',
                f'An improvement item has been marked as completed for {self.object.improvement_plan.employee.get_full_name()}.'
            )
        elif form.has_changed():
            # Send update notification
            self.object.send_notification(
                'PLAN_UPDATE',
                'Improvement Item Updated',
                f'An improvement item has been updated for {self.object.improvement_plan.employee.get_full_name()}.'
            )
        
        return response

# Personal Development Plan views
class PersonalDevelopmentPlanListView(LoginRequiredMixin, ListView):
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        user = self.request.user
        print(f"Current user: {user.username}, Role: {user.role}, ID: {user.id}")
        
        if user.role == 'HR':
            queryset = PersonalDevelopmentPlan.objects.all()
            print(f"HR user, showing all plans. Count: {queryset.count()}")
        elif user.role == 'MANAGER':
            queryset = PersonalDevelopmentPlan.objects.filter(employee__manager=user)
            print(f"Manager user, showing employee plans. Count: {queryset.count()}")
        else:
            queryset = PersonalDevelopmentPlan.objects.filter(employee=user)
            print(f"Regular user, showing own plans. Count: {queryset.count()}")
            
        print(f"Plans in queryset: {list(queryset.values('id', 'employee__username', 'competency_gap'))}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Development Plans'
        context['item_name'] = 'Development Plan'
        context['create_url'] = 'development_plan_create'
        context['detail_url'] = 'development_plan_detail'
        context['update_url'] = 'development_plan_update'
        context['delete_url'] = 'development_plan_delete'
        print(f"Context data: {context.keys()}")
        print(f"Plans in context: {context['plans']}")
        return context

class PersonalDevelopmentPlanCreateView(LoginRequiredMixin, CreateView):
    model = PersonalDevelopmentPlan
    form_class = PersonalDevelopmentPlanForm
    template_name = 'performance/development_plan_form.html'
    success_url = reverse_lazy('performance:development_plan_list')

    def form_valid(self, form):
        print("Form is valid, saving development plan...")
        print(f"Form data: {form.cleaned_data}")
        print(f"Current user: {self.request.user.username}, ID: {self.request.user.id}")
        
        # Set the employee to the current user
        form.instance.employee = self.request.user
        
        # Ensure progress is set if not provided
        if 'progress' not in form.cleaned_data or form.cleaned_data['progress'] is None:
            form.instance.progress = 0
            
        # Save the form
        response = super().form_valid(form)
        print(f"Development plan saved with ID: {form.instance.id}")
        
        # Redirect to the list view
        return response

    def form_invalid(self, form):
        print(f"Form errors: {form.errors}")
        print(f"Form data: {form.data}")
        for field, errors in form.errors.items():
            print(f"Field '{field}' errors: {errors}")
        return super().form_invalid(form)
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        print("Rendering development plan form...")
        return context

class PersonalDevelopmentPlanDetailView(LoginRequiredMixin, DetailView):
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_detail.html'
    context_object_name = 'plan'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PersonalDevelopmentPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PersonalDevelopmentPlan.objects.filter(employee__manager=self.request.user)
        return PersonalDevelopmentPlan.objects.filter(employee=self.request.user)

class PersonalDevelopmentPlanUpdateView(LoginRequiredMixin, UpdateView):
    model = PersonalDevelopmentPlan
    form_class = PersonalDevelopmentPlanForm
    template_name = 'performance/development_plan_form.html'
    success_url = reverse_lazy('performance:development_plan_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PersonalDevelopmentPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PersonalDevelopmentPlan.objects.filter(employee__manager=self.request.user)
        return PersonalDevelopmentPlan.objects.filter(employee=self.request.user)

class PersonalDevelopmentPlanDeleteView(LoginRequiredMixin, DeleteView):
    model = PersonalDevelopmentPlan
    template_name = 'performance/confirm_delete.html'
    success_url = reverse_lazy('performance:development_plan_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Development Plan'
        context['item_name'] = 'Development Plan'
        return context
        
    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PersonalDevelopmentPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PersonalDevelopmentPlan.objects.filter(employee__manager=self.request.user)
        return PersonalDevelopmentPlan.objects.filter(employee=self.request.user)

@login_required
def development_plan_delete(request, pk):
    plan = get_object_or_404(PersonalDevelopmentPlan, pk=pk)
    
    # Check permissions
    if request.user.role != CustomUser.HR and request.user != plan.employee and (request.user.role == CustomUser.MANAGER and plan.employee.manager != request.user):
        messages.error(request, "You don't have permission to delete this development plan.")
        return redirect('performance:development_plan_list')
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, "Development plan deleted successfully.")
        return redirect('performance:development_plan_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': plan,
        'object_name': 'Development Plan',
        'cancel_url': 'performance:development_plan_list'
    })

# Feedback views
class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    template_name = 'performance/feedback_form.html'
    fields = ['feedback', 'anonymous']
    success_url = reverse_lazy('performance:dashboard')

    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    return render(request, 'performance/notifications.html', {
        'notifications': notifications
    })

@login_required
def notification_count(request):
    count = Notification.objects.filter(recipient=request.user, read_at__isnull=True).count()
    return JsonResponse({'count': count})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.mark_as_read()
    return JsonResponse({'status': 'success'})

@login_required
def notification_preferences(request):
    preferences, created = NotificationPreference.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        preferences.email_notifications = request.POST.get('email_notifications') == 'on'
        preferences.review_reminders = request.POST.get('review_reminders') == 'on'
        preferences.plan_updates = request.POST.get('plan_updates') == 'on'
        preferences.feedback_notifications = request.POST.get('feedback_notifications') == 'on'
        preferences.reminder_frequency = request.POST.get('reminder_frequency')
        preferences.save()
        return redirect('performance:notification_preferences')
    
    return render(request, 'performance/notification_preferences.html', {
        'preferences': preferences
    })

@login_required
def mark_all_notifications_read(request):
    Notification.objects.filter(recipient=request.user, read_at__isnull=True).update(read_at=timezone.now())
    return JsonResponse({'status': 'success'})

@login_required
@require_POST
def upload_kra_evidence(request):
    """Handle KRA evidence file uploads"""
    try:
        kra_id = request.POST.get('kra_id')
        evidence_file = request.FILES.get('evidence')
        
        if not kra_id or not evidence_file:
            return JsonResponse({'success': False, 'error': 'Missing required data'})
            
        kra = get_object_or_404(KeyResponsibilityArea, id=kra_id)
        
        # Check permissions
        if kra.performance_agreement.employee != request.user:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
            
        # Save the evidence file
        kra.supporting_documents = evidence_file
        kra.save()
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def performance_agreement_approve(request, pk):
    """Approve performance agreement"""
    if request.method == 'POST':
        agreement = get_object_or_404(PerformanceAgreement, pk=pk)
        
        # Verify user is the supervisor
        if agreement.supervisor != request.user:
            messages.error(request, 'You do not have permission to approve this agreement.')
            return redirect('performance:performance_agreement_detail', pk=pk)
        
        # Update status
        agreement.status = PerformanceAgreement.COMPLETED
        agreement.supervisor_reviewed_date = timezone.now()
        agreement.save()
        
        # Notify employee
        notify_user(
            user=agreement.employee,
            notification_type='APPROVAL',
            title='Performance Agreement Approved',
            message=f'Your performance agreement has been approved by {agreement.supervisor.get_full_name()}.',
            related_object_type='performance_agreement',
            related_object_id=agreement.id
        )
        
        messages.success(request, 'Performance agreement approved successfully.')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    return redirect('performance:performance_agreement_detail', pk=pk)

@login_required
def performance_agreement_reject(request, pk):
    """Reject performance agreement"""
    if request.method == 'POST':
        agreement = get_object_or_404(PerformanceAgreement, pk=pk)
        
        # Verify user is the supervisor
        if agreement.supervisor != request.user:
            messages.error(request, 'You do not have permission to reject this agreement.')
            return redirect('performance:performance_agreement_detail', pk=pk)
        
        # Get rejection reason
        rejection_reason = request.POST.get('rejection_reason')
        if not rejection_reason:
            messages.error(request, 'Please provide a reason for rejection.')
            return redirect('performance:performance_agreement_detail', pk=pk)
        
        # Update status
        agreement.status = PerformanceAgreement.REJECTED
        agreement.rejection_reason = rejection_reason
        agreement.rejected_by = request.user
        agreement.rejected_date = timezone.now()
        agreement.save()
        
        # Notify employee
        notify_user(
            user=agreement.employee,
            notification_type='APPROVAL',
            title='Performance Agreement Rejected',
            message=f'Your performance agreement has been rejected by {agreement.supervisor.get_full_name()}. Reason: {rejection_reason}',
            related_object_type='performance_agreement',
            related_object_id=agreement.id
        )
        
        messages.warning(request, 'Performance agreement has been rejected.')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    return redirect('performance:performance_agreement_detail', pk=pk)

@login_required
def export_agreement_pdf(request, pk):
    """Export performance agreement as PDF"""
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    # Check permissions
    if not (request.user == agreement.employee or 
            request.user == agreement.supervisor or 
            request.user.role == CustomUser.HR):
        messages.error(request, 'You do not have permission to export this agreement.')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    # Create the HttpResponse object with PDF headers
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="performance_agreement_{pk}.pdf"'
    
    # Create the PDF object using ReportLab
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Get styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30
    )
    
    # Add title
    elements.append(Paragraph('Performance Agreement', title_style))
    elements.append(Spacer(1, 12))
    
    # Add employee and supervisor information
    employee_data = [
        ['Employee Information', 'Supervisor Information'],
        [f'Name: {agreement.employee.get_full_name()}', f'Name: {agreement.supervisor.get_full_name()}'],
        [f'ID: {agreement.employee.employee_id}', f'ID: {agreement.supervisor.employee_id}'],
        [f'Department: {agreement.employee.department}', f'Department: {agreement.supervisor.department}'],
        [f'Job Title: {agreement.employee.job_title}', f'Job Title: {agreement.supervisor.job_title}']
    ]
    
    t = Table(employee_data, colWidths=[4*inch, 4*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Add agreement details
    elements.append(Paragraph('Agreement Details', styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    agreement_data = [
        ['Status', agreement.get_status_display()],
        ['Period', f"{agreement.plan_start_date.strftime('%B %d, %Y')} - {agreement.plan_end_date.strftime('%B %d, %Y')}"],
        ['Mid-Year Review', agreement.midyear_review_date.strftime('%B %d, %Y')],
        ['Final Assessment', agreement.final_assessment_date.strftime('%B %d, %Y')]
    ]
    
    t = Table(agreement_data, colWidths=[2*inch, 6*inch])
    t.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Add KRAs
    elements.append(Paragraph('Key Result Areas (KRAs)', styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    kra_data = [['Description', 'Objective', 'Weight', 'Standards', 'Target Date']]
    for kra in agreement.kras.all():
        kra_data.append([
            kra.description,
            kra.performance_objective,
            f"{kra.weighting}%",
            kra.measurement,
            kra.target_date.strftime('%B %d, %Y')
        ])
    
    t = Table(kra_data, colWidths=[2*inch, 2*inch, 1*inch, 2*inch, 1*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 20))
    
    # Add GAFs
    elements.append(Paragraph('Generic Assessment Factors (GAFs)', styles['Heading2']))
    elements.append(Spacer(1, 12))
    
    gaf_data = [['Factor', 'Comments']]
    for gaf in agreement.gafs.filter(is_applicable=True):
        gaf_data.append([
            gaf.get_factor_display(),
            gaf.comments or 'No comments provided.'
        ])
    
    t = Table(gaf_data, colWidths=[3*inch, 5*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(t)
    
    # Build PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    response.write(pdf)
    
    return response

@login_required
def performance_agreement_delete(request, pk):
    """Delete a performance agreement if user is HR and agreement is not completed"""
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    # Only HR can delete agreements
    if request.user.role != 'HR':
        messages.error(request, 'Only HR administrators can delete performance agreements.')
        return redirect('performance:performance_agreement_list')
    
    # Cannot delete completed or approved agreements
    if agreement.status not in [PerformanceAgreement.DRAFT, PerformanceAgreement.REJECTED]:
        messages.error(request, 'Cannot delete agreements that have been submitted or approved.')
        return redirect('performance:performance_agreement_list')
    
    if request.method == 'POST':
        agreement.delete()
        messages.success(request, f'Performance agreement for {agreement.employee.get_full_name()} has been deleted.')
        return redirect('performance:performance_agreement_list')
    
    return redirect('performance:performance_agreement_list')

@login_required
@require_POST
def add_to_improvement_plan(request):
    """Add a comment/rating to the improvement plan"""
    source_type = request.POST.get('source_type')
    source_id = request.POST.get('source_id')
    gaf_id = request.POST.get('gaf_id')
    comment = request.POST.get('comment')
    
    if not all([source_type, source_id, gaf_id, comment]):
        return JsonResponse({'success': False, 'error': 'Missing required fields'})
    
    try:
        # Get the employee based on the source
        employee = None
        if source_type == ImprovementPlanItem.PERFORMANCE_AGREEMENT:
            source = PerformanceAgreement.objects.get(id=source_id)
            employee = source.employee
        elif source_type == ImprovementPlanItem.MIDYEAR_REVIEW:
            source = MidYearReview.objects.get(id=source_id)
            employee = source.performance_agreement.employee
        else:
            return JsonResponse({'success': False, 'error': 'Invalid source type'})
        
        # Check if user is the supervisor
        if request.user != employee.manager:
            return JsonResponse({'success': False, 'error': 'Permission denied'})
        
        # Get or create improvement plan
        plan = ImprovementPlan.get_or_create_current_plan(employee)
        
        # Create improvement plan item
        item = ImprovementPlanItem.objects.create(
            improvement_plan=plan,
            area_for_development=comment,
            source_type=source_type,
            source_id=source_id,
            source_gaf_id=gaf_id
        )
        
        # Send notification
        source_name = "Performance Agreement" if source_type == ImprovementPlanItem.PERFORMANCE_AGREEMENT else "Mid-Year Review"
        item.send_notification(
            'PLAN_UPDATE',
            'New Improvement Item Added',
            f'A new improvement item has been added to your plan from your {source_name}.'
        )
        
        return JsonResponse({
            'success': True,
            'item_id': item.id,
            'message': 'Added to improvement plan successfully'
        })
        
    except (PerformanceAgreement.DoesNotExist, MidYearReview.DoesNotExist) as e:
        return JsonResponse({'success': False, 'error': str(e)})

def handle_review_completion(review):
    """Create improvement plan items from a completed review"""
    plan = ImprovementPlan.get_or_create_current_plan(review.performance_agreement.employee)
    
    # Check KRA ratings
    for kra_rating in review.kra_ratings.all():
        if (kra_rating.supervisor_rating and 
            kra_rating.supervisor_rating <= 2 and 
            kra_rating.supervisor_comments):
            
            ImprovementPlanItem.objects.create(
                improvement_plan=plan,
                area_for_development=kra_rating.supervisor_comments,
                source_type=ImprovementPlanItem.MIDYEAR_REVIEW,
                source_id=review.id,
                source_kra=kra_rating.kra
            )
    
    # Check GAF ratings
    for gaf_rating in review.gaf_ratings.all():
        if (gaf_rating.supervisor_rating and 
            gaf_rating.supervisor_rating <= 2 and 
            gaf_rating.supervisor_comments):
            
            ImprovementPlanItem.objects.create(
                improvement_plan=plan,
                area_for_development=gaf_rating.supervisor_comments,
                source_type=ImprovementPlanItem.MIDYEAR_REVIEW,
                source_id=review.id,
                source_gaf=gaf_rating.gaf
            )

# Final Review views
class FinalReviewListView(LoginRequiredMixin, ListView):
    model = FinalReview
    template_name = 'performance/final_review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return FinalReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return FinalReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return FinalReview.objects.filter(performance_agreement__employee=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Year-End Reviews'
        context['create_url'] = 'final_review_create'
        context['detail_url'] = 'final_review_detail'
        context['update_url'] = 'final_review_update'
        context['headers'] = ['Review Date', 'Final Rating']
        return context

class FinalReviewCreateView(LoginRequiredMixin, CreateView):
    model = FinalReview
    form_class = FinalReviewForm
    template_name = 'performance/final_review_form.html'
    success_url = reverse_lazy('performance:final_review_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get the performance agreement if it's in POST data or GET parameters
        performance_agreement_id = None
        if self.request.POST:
            performance_agreement_id = self.request.POST.get('performance_agreement')
        elif 'performance_agreement' in self.request.GET:
            performance_agreement_id = self.request.GET.get('performance_agreement')
            
        performance_agreement = None
        if performance_agreement_id:
            try:
                performance_agreement = PerformanceAgreement.objects.select_related(
                    'employee', 'supervisor'
                ).prefetch_related(
                    'kras', 
                    'gafs'
                ).get(id=performance_agreement_id)
                
                # Set the performance agreement in the form's initial data
                if not self.request.POST:  # Only set initial data if not a POST request
                    context['form'].initial = {
                        'performance_agreement': performance_agreement,
                        'review_date': timezone.now().date()
                    }
            except PerformanceAgreement.DoesNotExist:
                pass

        if self.request.POST:
            context['kra_formset'] = KRAFinalRatingFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object if hasattr(self, 'object') else None
            )
            context['gaf_formset'] = GAFFinalRatingFormSet(
                self.request.POST,
                self.request.FILES,
                instance=self.object if hasattr(self, 'object') else None
            )
        else:
            # Initialize empty formsets
            context['kra_formset'] = KRAFinalRatingFormSet(
                instance=self.object if hasattr(self, 'object') else None,
                queryset=KRAFinalRating.objects.none()
            )
            context['gaf_formset'] = GAFFinalRatingFormSet(
                instance=self.object if hasattr(self, 'object') else None,
                queryset=GAFFinalRating.objects.none()
            )
            
            # If we have a performance agreement, pre-populate the formsets
            if performance_agreement:
                # Create a form for each KRA in the performance agreement
                kra_forms = []
                for kra in performance_agreement.kras.all():
                    form = KRAFinalRatingForm(initial={'kra': kra})
                    form.fields['kra'].widget = forms.HiddenInput()
                    kra_forms.append(form)
                
                # Create a form for each APPLICABLE GAF in the performance agreement
                gaf_forms = []
                for gaf in performance_agreement.gafs.filter(is_applicable=True):
                    form = GAFFinalRatingForm(initial={'gaf': gaf})
                    form.fields['gaf'].widget = forms.HiddenInput()
                    gaf_forms.append(form)
                
                # Replace the formset forms with our pre-populated ones
                context['kra_formset'].forms = kra_forms
                context['gaf_formset'].forms = gaf_forms
                
                # Add management form data
                context['kra_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(kra_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
                context['gaf_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(gaf_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
        
        # Add performance agreement to context if it exists
        if performance_agreement:
            context['performance_agreement'] = performance_agreement

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']

        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Save the main form first to get the instance
            self.object = form.save()
            
            # Save KRA ratings
            kra_formset.instance = self.object
            kra_ratings = kra_formset.save(commit=False)
            for rating in kra_ratings:
                rating.final_review = self.object
                rating.save()
            
            # Save GAF ratings
            gaf_formset.instance = self.object
            gaf_ratings = gaf_formset.save(commit=False)
            for rating in gaf_ratings:
                rating.final_review = self.object
                rating.save()
            
            messages.success(self.request, 'Year-end review created successfully.')
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

class FinalReviewDetailView(LoginRequiredMixin, DetailView):
    model = FinalReview
    template_name = 'performance/final_review_detail.html'
    context_object_name = 'review'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kra_ratings'] = self.object.kra_ratings.all().select_related('kra')
        
        # Only include GAFs that are applicable
        applicable_gaf_ids = self.object.performance_agreement.gafs.filter(is_applicable=True).values_list('id', flat=True)
        context['gaf_ratings'] = self.object.gaf_ratings.filter(gaf_id__in=applicable_gaf_ids).select_related('gaf')
        
        return context

class FinalReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = FinalReview
    form_class = FinalReviewForm
    template_name = 'performance/final_review_form.html'
    success_url = reverse_lazy('performance:final_review_list')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Ensure the performance agreement is in the context
        performance_agreement = self.object.performance_agreement
        context['performance_agreement'] = performance_agreement
        
        if self.request.POST:
            context['kra_formset'] = KRAFinalRatingFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
            context['gaf_formset'] = GAFFinalRatingFormSet(
                self.request.POST, 
                self.request.FILES, 
                instance=self.object
            )
        else:
            # For existing reviews, only include GAFs that were already rated or are applicable
            kra_ratings = self.object.kra_ratings.all()
            gaf_ratings = self.object.gaf_ratings.all()
            
            # If no ratings exist yet, create them based on the performance agreement
            if not kra_ratings.exists():
                context['kra_formset'] = KRAFinalRatingFormSet(instance=self.object)
                kra_forms = []
                for kra in performance_agreement.kras.all():
                    form = KRAFinalRatingForm(initial={'kra': kra, 'final_review': self.object})
                    form.fields['kra'].widget = forms.HiddenInput()
                    kra_forms.append(form)
                context['kra_formset'].forms = kra_forms
                context['kra_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(kra_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
            else:
                context['kra_formset'] = KRAFinalRatingFormSet(instance=self.object)
            
            if not gaf_ratings.exists():
                context['gaf_formset'] = GAFFinalRatingFormSet(instance=self.object)
                gaf_forms = []
                for gaf in performance_agreement.gafs.filter(is_applicable=True):
                    form = GAFFinalRatingForm(initial={'gaf': gaf, 'final_review': self.object})
                    form.fields['gaf'].widget = forms.HiddenInput()
                    gaf_forms.append(form)
                context['gaf_formset'].forms = gaf_forms
                context['gaf_formset'].management_form.initial = {
                    'TOTAL_FORMS': len(gaf_forms),
                    'INITIAL_FORMS': 0,
                    'MIN_NUM_FORMS': 0,
                    'MAX_NUM_FORMS': 1000
                }
            else:
                context['gaf_formset'] = GAFFinalRatingFormSet(instance=self.object)
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']

        if kra_formset.is_valid() and gaf_formset.is_valid():
            self.object = form.save()
            kra_formset.save()
            gaf_formset.save()
            
            # Get the current user and status
            user = self.request.user
            current_status = self.object.status
            
            # Check if the form has a 'submit_action' field to determine the action
            submit_action = self.request.POST.get('submit_action', 'save')
            
            # Handle different submission actions
            if submit_action == 'submit_for_signoff':
                # Both employee and supervisor ratings have been entered, submit for supervisor sign-off
                self.object.status = 'PENDING_SUPERVISOR_SIGNOFF'
                self.object.employee_rating_date = timezone.now()
                self.object.supervisor_rating_date = timezone.now()
                messages.success(self.request, 'Year-end review submitted for supervisor sign-off.')
            
            elif submit_action == 'supervisor_signoff':
                # Supervisor is signing off on the review
                if user == self.object.performance_agreement.supervisor:
                    self.object.status = 'PENDING_MANAGER_APPROVAL'
                    self.object.supervisor_signoff_date = timezone.now()
                    messages.success(self.request, 'Year-end review signed off and submitted for manager approval.')
                else:
                    messages.error(self.request, 'Only the supervisor can sign off on this review.')
            
            elif submit_action == 'manager_approve':
                # Manager is approving the review
                if user.role == CustomUser.MANAGER and user == self.object.performance_agreement.supervisor.manager:
                    self.object.status = 'COMPLETED'
                    self.object.manager_approval_date = timezone.now()
                    self.object.completion_date = timezone.now()
                    messages.success(self.request, 'Year-end review approved and completed.')
                else:
                    messages.error(self.request, 'Only the manager can approve this review.')
            
            elif submit_action == 'reject':
                # Rejecting the review (can be done by supervisor or manager)
                rejection_reason = self.request.POST.get('rejection_reason', '')
                if user == self.object.performance_agreement.supervisor or (user.role == CustomUser.MANAGER and user == self.object.performance_agreement.supervisor.manager):
                    self.object.status = 'REJECTED'
                    self.object.rejection_date = timezone.now()
                    self.object.rejection_reason = rejection_reason
                    messages.success(self.request, 'Year-end review has been rejected.')
                else:
                    messages.error(self.request, 'You do not have permission to reject this review.')
            
            else:
                # Just saving the form without changing status
                messages.success(self.request, 'Year-end review saved successfully.')
            
            self.object.save()
            return redirect(self.success_url)
        else:
            return self.form_invalid(form)

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return FinalReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return FinalReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return FinalReview.objects.filter(performance_agreement__employee=self.request.user)

@login_required
def final_review_delete(request, pk):
    review = get_object_or_404(FinalReview, pk=pk)
    
    # Check permissions
    if request.user.role != CustomUser.HR and request.user != review.performance_agreement.employee and request.user != review.performance_agreement.supervisor:
        messages.error(request, "You don't have permission to delete this review.")
        return redirect('performance:final_review_list')
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Year-end review deleted successfully.')
        return redirect('performance:final_review_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': review,
        'object_name': f"Year-End Review for {review.performance_agreement.employee.get_full_name()}",
        'cancel_url': 'performance:final_review_list'
    })

@login_required
def test_development_plans_view(request):
    """A test view to directly render development plans"""
    plans = PersonalDevelopmentPlan.objects.all()
    print(f"Test view - Plans found: {plans.count()}")
    
    for plan in plans:
        print(f"Plan ID: {plan.id}")
        print(f"Employee: {plan.employee.get_full_name()}")
        print(f"Display fields: {plan.display_fields}")
        for field in plan.display_fields:
            value = getattr(plan, field)
            print(f"  {field}: {value}")
    
    context = {
        'title': 'Test Development Plans',
        'plans': plans,
        'object_list': plans,  # Add this to match the generic list template
        'create_url': 'development_plan_create',
        'detail_url': 'development_plan_detail',
        'update_url': 'development_plan_update',
        'delete_url': 'development_plan_delete',
        'item_name': 'Development Plan',
    }
    
    # Try both templates
    if request.GET.get('use_generic') == '1':
        template_name = 'performance/generic_list.html'
    else:
        template_name = 'performance/test_development_plans.html'
        
    print(f"Using template: {template_name}")
    return render(request, template_name, context)
