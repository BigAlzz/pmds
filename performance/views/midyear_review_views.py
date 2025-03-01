"""
Mid-Year Review views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django import forms

from ..models import (
    CustomUser,
    MidYearReview,
    PerformanceAgreement,
    KRAMidYearRating,
    GAFMidYearRating,
    KeyResponsibilityArea,
    GenericAssessmentFactor
)
from ..forms import (
    MidYearReviewForm,
    KRAMidYearRatingForm,
    GAFMidYearRatingForm,
    KRAMidYearRatingFormSet,
    GAFMidYearRatingFormSet
)
from ..notifications import notify_user
from ..mixins import MidYearReviewPermissionMixin
from ..decorators import midyear_review_permission


class MidYearReviewListView(LoginRequiredMixin, ListView):
    """
    Display a list of mid-year reviews based on user role.
    """
    model = MidYearReview
    template_name = 'performance/midyear_review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == CustomUser.HR:
            # Admin and HR can see all reviews
            return MidYearReview.objects.all()
        elif user.role == CustomUser.MANAGER:
            # Managers can see reviews of their subordinates and their own
            return MidYearReview.objects.filter(
                Q(performance_agreement__employee=user) | 
                Q(performance_agreement__employee__in=user.subordinates.all())
            )
        elif user.role == CustomUser.APPROVER:
            # Approvers can see reviews pending their approval and their own
            return MidYearReview.objects.filter(
                Q(performance_agreement__employee=user) | 
                Q(status='PENDING_MANAGER_APPROVAL')
            )
        else:
            # Regular employees can only see their own reviews
            return MidYearReview.objects.filter(performance_agreement__employee=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Mid-Year Reviews'
        context['item_name'] = 'Mid-Year Review'
        context['create_url'] = 'midyear_review_create'
        context['detail_url'] = 'midyear_review_detail'
        context['update_url'] = 'midyear_review_update'
        context['delete_url'] = 'midyear_review_delete'
        return context


class MidYearReviewCreateView(MidYearReviewPermissionMixin, CreateView):
    """
    Create a new mid-year review.
    """
    model = MidYearReview
    form_class = MidYearReviewForm
    template_name = 'performance/midyear_review_form.html'
    success_url = reverse_lazy('performance:midyear_review_list')
    permission_type = 'create'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['kra_formset'] = KRAMidYearRatingFormSet(self.request.POST, prefix='kra')
            context['gaf_formset'] = GAFMidYearRatingFormSet(self.request.POST, prefix='gaf')
        else:
            context['kra_formset'] = KRAMidYearRatingFormSet(prefix='kra')
            context['gaf_formset'] = GAFMidYearRatingFormSet(prefix='gaf')
            
            # If performance_agreement_id or performance_agreement is in GET parameters, pre-populate the form
            pa_id = self.request.GET.get('performance_agreement_id') or self.request.GET.get('performance_agreement')
            if pa_id:
                try:
                    pa = PerformanceAgreement.objects.get(id=pa_id)
                    context['form'].fields['performance_agreement'].initial = pa.id
                    
                    # Add the performance agreement to the context
                    context['performance_agreement'] = pa
                    
                    # Pre-populate KRA formset
                    kras = pa.kras.all()
                    # Create a new formset with the correct number of forms
                    KRAFormSet = forms.inlineformset_factory(
                        MidYearReview,
                        KRAMidYearRating,
                        form=KRAMidYearRatingForm,
                        extra=len(kras),
                        can_delete=False
                    )
                    context['kra_formset'] = KRAFormSet(prefix='kra')
                    
                    # Pre-populate the KRA forms
                    for i, kra in enumerate(kras):
                        if i < len(context['kra_formset'].forms):
                            context['kra_formset'].forms[i].initial = {
                                'kra': kra.id
                            }
                            # Set the queryset for the kra field
                            context['kra_formset'].forms[i].fields['kra'].queryset = KeyResponsibilityArea.objects.filter(
                                performance_agreement=pa
                            )
                    
                    # Pre-populate GAF formset
                    gafs = pa.gafs.filter(is_applicable=True)
                    # Create a new formset with the correct number of forms
                    GAFFormSet = forms.inlineformset_factory(
                        MidYearReview,
                        GAFMidYearRating,
                        form=GAFMidYearRatingForm,
                        extra=len(gafs),
                        can_delete=False
                    )
                    context['gaf_formset'] = GAFFormSet(prefix='gaf')
                    
                    # Pre-populate the GAF forms
                    for i, gaf in enumerate(gafs):
                        if i < len(context['gaf_formset'].forms):
                            context['gaf_formset'].forms[i].initial = {
                                'gaf': gaf.id
                            }
                            # Set the queryset for the gaf field
                            context['gaf_formset'].forms[i].fields['gaf'].queryset = GenericAssessmentFactor.objects.filter(
                                performance_agreement=pa,
                                is_applicable=True
                            )
                except PerformanceAgreement.DoesNotExist:
                    pass
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']
        
        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Save the review
            self.object = form.save()
            
            # Save the KRA ratings
            kra_formset.instance = self.object
            kra_formset.save()
            
            # Save the GAF ratings
            gaf_formset.instance = self.object
            gaf_formset.save()
            
            # Set initial status based on user role
            if self.request.user == self.object.performance_agreement.supervisor:
                # If created by supervisor, set status to pending employee rating
                self.object.status = 'PENDING_EMPLOYEE_RATING'
                self.object.save()
                
                # Notify employee
                notify_user(
                    self.object.performance_agreement.employee,
                    'REVIEW_DUE',
                    'Mid-Year Review Needs Your Input',
                    f'A mid-year review has been created and needs your self-rating.',
                    'midyear_review',
                    self.object.id
                )
                
                messages.success(self.request, 'Mid-year review created and sent to employee for self-rating.')
            else:
                # If created by employee, set status to pending supervisor rating
                self.object.status = 'PENDING_SUPERVISOR_RATING'
                self.object.employee_rating_date = timezone.now()
                self.object.save()
                
                # Notify supervisor
                if self.object.performance_agreement.supervisor:
                    notify_user(
                        self.object.performance_agreement.supervisor,
                        'REVIEW_DUE',
                        'Mid-Year Review Needs Your Rating',
                        f'A mid-year review from {self.object.performance_agreement.employee.get_full_name()} needs your rating.',
                        'midyear_review',
                        self.object.id
                    )
                
                messages.success(self.request, 'Mid-year review created and submitted for supervisor rating.')
            
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class MidYearReviewDetailView(MidYearReviewPermissionMixin, DetailView):
    """
    Display details of a mid-year review.
    """
    model = MidYearReview
    template_name = 'performance/midyear_review_detail.html'
    context_object_name = 'review'
    permission_type = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kra_ratings'] = KRAMidYearRating.objects.filter(midyear_review=self.object)
        context['gaf_ratings'] = GAFMidYearRating.objects.filter(midyear_review=self.object)
        return context


class MidYearReviewUpdateView(MidYearReviewPermissionMixin, UpdateView):
    """
    Update an existing mid-year review.
    """
    model = MidYearReview
    form_class = MidYearReviewForm
    template_name = 'performance/midyear_review_form.html'
    success_url = reverse_lazy('performance:midyear_review_list')
    permission_type = 'update'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['kra_formset'] = KRAMidYearRatingFormSet(
                self.request.POST, 
                prefix='kra',
                queryset=KRAMidYearRating.objects.filter(midyear_review=self.object)
            )
            context['gaf_formset'] = GAFMidYearRatingFormSet(
                self.request.POST, 
                prefix='gaf',
                queryset=GAFMidYearRating.objects.filter(midyear_review=self.object)
            )
        else:
            context['kra_formset'] = KRAMidYearRatingFormSet(
                prefix='kra',
                queryset=KRAMidYearRating.objects.filter(midyear_review=self.object)
            )
            context['gaf_formset'] = GAFMidYearRatingFormSet(
                prefix='gaf',
                queryset=GAFMidYearRating.objects.filter(midyear_review=self.object)
            )
            
            # Add the performance agreement to the context
            context['performance_agreement'] = self.object.performance_agreement
            
            # Disable fields based on status and user role
            user = self.request.user
            status = self.object.status
            
            # Determine which fields should be editable
            if user == self.object.performance_agreement.employee:
                # Employee can only edit employee ratings
                for form in context['kra_formset'].forms:
                    form.fields['kra'].disabled = True
                    form.fields['supervisor_rating'].disabled = True
                    form.fields['supervisor_comments'].disabled = True
                    
                    # Disable employee fields if not in the right status
                    if status not in ['PENDING_EMPLOYEE_RATING', 'RETURNED']:
                        form.fields['employee_rating'].disabled = True
                        form.fields['employee_comments'].disabled = True
                
                for form in context['gaf_formset'].forms:
                    form.fields['gaf'].disabled = True
                    form.fields['supervisor_rating'].disabled = True
                    form.fields['supervisor_comments'].disabled = True
                    
                    # Disable employee fields if not in the right status
                    if status not in ['PENDING_EMPLOYEE_RATING', 'RETURNED']:
                        form.fields['employee_rating'].disabled = True
                        form.fields['employee_comments'].disabled = True
            
            elif user == self.object.performance_agreement.supervisor:
                # Supervisor can only edit supervisor ratings
                for form in context['kra_formset'].forms:
                    form.fields['kra'].disabled = True
                    form.fields['employee_rating'].disabled = True
                    form.fields['employee_comments'].disabled = True
                    
                    # Disable supervisor fields if not in the right status
                    if status not in ['PENDING_SUPERVISOR_RATING', 'PENDING_SUPERVISOR_SIGNOFF']:
                        form.fields['supervisor_rating'].disabled = True
                        form.fields['supervisor_comments'].disabled = True
                
                for form in context['gaf_formset'].forms:
                    form.fields['gaf'].disabled = True
                    form.fields['employee_rating'].disabled = True
                    form.fields['employee_comments'].disabled = True
                    
                    # Disable supervisor fields if not in the right status
                    if status not in ['PENDING_SUPERVISOR_RATING', 'PENDING_SUPERVISOR_SIGNOFF']:
                        form.fields['supervisor_rating'].disabled = True
                        form.fields['supervisor_comments'].disabled = True
            
            elif user.role == CustomUser.HR:
                # HR can edit all fields
                pass
            
            else:
                # Others can't edit anything
                for form in context['kra_formset'].forms:
                    for field in form.fields.values():
                        field.disabled = True
                
                for form in context['gaf_formset'].forms:
                    for field in form.fields.values():
                        field.disabled = True
        
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
            if submit_action == 'submit_employee_rating':
                # Employee submitting their self-rating
                if user == self.object.performance_agreement.employee:
                    self.object.status = 'PENDING_SUPERVISOR_RATING'
                    self.object.employee_rating_date = timezone.now()
                    self.object.save()
                    
                    # Notify supervisor
                    if self.object.performance_agreement.supervisor:
                        notify_user(
                            self.object.performance_agreement.supervisor,
                            'REVIEW_DUE',
                            'Mid-Year Review Needs Your Rating',
                            f'A mid-year review for {self.object.performance_agreement.employee.get_full_name()} needs your rating.',
                            'midyear_review',
                            self.object.id
                        )
                    
                    messages.success(self.request, 'Self-rating submitted successfully.')
                else:
                    messages.error(self.request, 'Only the employee can submit self-ratings.')
            
            elif submit_action == 'submit_supervisor_rating':
                # Supervisor submitting their rating
                if user == self.object.performance_agreement.supervisor:
                    self.object.status = 'PENDING_SUPERVISOR_SIGNOFF'
                    self.object.supervisor_rating_date = timezone.now()
                    self.object.save()
                    messages.success(self.request, 'Supervisor rating submitted successfully.')
                else:
                    messages.error(self.request, 'Only the supervisor can submit supervisor ratings.')
            
            elif submit_action == 'supervisor_signoff':
                # Supervisor signing off on the review
                if user == self.object.performance_agreement.supervisor:
                    self.object.status = 'PENDING_MANAGER_APPROVAL'
                    self.object.supervisor_signoff_date = timezone.now()
                    self.object.save()
                    
                    # Notify manager/approver if exists
                    if self.object.performance_agreement.approver:
                        notify_user(
                            self.object.performance_agreement.approver,
                            'APPROVAL',
                            'Mid-Year Review Needs Approval',
                            f'A mid-year review for {self.object.performance_agreement.employee.get_full_name()} needs your approval.',
                            'midyear_review',
                            self.object.id
                        )
                    
                    messages.success(self.request, 'Review signed off and submitted for manager approval.')
                else:
                    messages.error(self.request, 'Only the supervisor can sign off on this review.')
            
            elif submit_action == 'manager_approve':
                # Manager/Approver approving the review
                if (user == self.object.performance_agreement.approver or 
                    (user.role == CustomUser.HR and self.object.status == 'PENDING_MANAGER_APPROVAL')):
                    self.object.status = 'COMPLETED'
                    self.object.manager_approval_date = timezone.now()
                    self.object.save()
                    
                    # Notify employee and supervisor
                    notify_user(
                        self.object.performance_agreement.employee,
                        'APPROVAL',
                        'Mid-Year Review Approved',
                        f'Your mid-year review has been approved.',
                        'midyear_review',
                        self.object.id
                    )
                    
                    if self.object.performance_agreement.supervisor:
                        notify_user(
                            self.object.performance_agreement.supervisor,
                            'APPROVAL',
                            'Mid-Year Review Approved',
                            f'The mid-year review for {self.object.performance_agreement.employee.get_full_name()} has been approved.',
                            'midyear_review',
                            self.object.id
                        )
                    
                    messages.success(self.request, 'Mid-year review approved successfully.')
                else:
                    messages.error(self.request, 'Only the manager or HR can approve this review.')
            
            elif submit_action == 'return_to_employee':
                # Supervisor returning the review to the employee
                if user == self.object.performance_agreement.supervisor:
                    self.object.status = 'RETURNED'
                    self.object.save()
                    
                    # Notify employee
                    notify_user(
                        self.object.performance_agreement.employee,
                        'RETURNED',
                        'Mid-Year Review Returned',
                        f'Your mid-year review has been returned for revision.',
                        'midyear_review',
                        self.object.id
                    )
                    
                    messages.success(self.request, 'Mid-year review returned to employee for revision.')
                else:
                    messages.error(self.request, 'Only the supervisor can return this review to the employee.')
            
            elif submit_action == 'return_to_supervisor':
                # Manager returning the review to the supervisor
                if (user == self.object.performance_agreement.approver or 
                    (user.role == CustomUser.HR and self.object.status == 'PENDING_MANAGER_APPROVAL')):
                    self.object.status = 'PENDING_SUPERVISOR_SIGNOFF'
                    self.object.save()
                    
                    # Notify supervisor
                    if self.object.performance_agreement.supervisor:
                        notify_user(
                            self.object.performance_agreement.supervisor,
                            'RETURNED',
                            'Mid-Year Review Returned',
                            f'The mid-year review for {self.object.performance_agreement.employee.get_full_name()} has been returned for revision.',
                            'midyear_review',
                            self.object.id
                        )
                    
                    messages.success(self.request, 'Mid-year review returned to supervisor for revision.')
                else:
                    messages.error(self.request, 'Only the manager or HR can return this review to the supervisor.')
            
            else:
                # Just saving without status change
                messages.success(self.request, 'Mid-year review saved successfully.')
            
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


@login_required
@midyear_review_permission('delete')
def midyear_review_delete(request, pk):
    """
    Delete a mid-year review.
    """
    review = get_object_or_404(MidYearReview, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Mid-year review deleted successfully.')
        return redirect('performance:midyear_review_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': review,
        'title': 'Delete Mid-Year Review',
        'cancel_url': 'performance:midyear_review_detail',
        'object_name': f"Mid-Year Review for {review.performance_agreement.employee.get_full_name()}"
    }) 