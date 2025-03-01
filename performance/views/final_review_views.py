"""
Final Review views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.http import Http404

from ..models import (
    CustomUser,
    FinalReview,
    KRAFinalRating,
    GAFFinalRating,
    Notification,
    PerformanceAgreement,
    KeyResponsibilityArea,
    GenericAssessmentFactor
)
from ..forms import (
    FinalReviewForm,
    KRAFinalRatingFormSet,
    GAFFinalRatingFormSet
)
from ..mixins import FinalReviewPermissionMixin
from ..decorators import final_review_permission
from functools import wraps


class FinalReviewListView(LoginRequiredMixin, ListView):
    """
    Display a list of final reviews based on user role.
    """
    model = FinalReview
    template_name = 'performance/final_review_list.html'
    context_object_name = 'reviews'

    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == CustomUser.HR:
            # Admin and HR can see all reviews
            return FinalReview.objects.all()
        elif user.role == CustomUser.MANAGER:
            # Managers can see reviews of their subordinates and their own
            return FinalReview.objects.filter(
                Q(employee=user) | Q(employee__in=user.subordinates.all())
            )
        elif user.role == CustomUser.APPROVER:
            # Approvers can see reviews pending their approval and their own
            return FinalReview.objects.filter(
                Q(employee=user) | Q(status='PENDING_APPROVAL')
            )
        else:
            # Regular employees can only see their own reviews
            return FinalReview.objects.filter(employee=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Final Reviews'
        context['item_name'] = 'Final Review'
        context['create_url'] = 'final_review_create'
        context['detail_url'] = 'final_review_detail'
        context['update_url'] = 'final_review_update'
        context['delete_url'] = 'final_review_delete'
        return context


class FinalReviewCreateView(FinalReviewPermissionMixin, CreateView):
    """
    Create a new final review.
    """
    model = FinalReview
    form_class = FinalReviewForm
    template_name = 'performance/final_review_form.html'
    success_url = reverse_lazy('performance:final_review_list')
    permission_type = 'create'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add formsets for KRA and GAF ratings
        if self.request.POST:
            context['kra_formset'] = KRAFinalRatingFormSet(self.request.POST, prefix='kra')
            context['gaf_formset'] = GAFFinalRatingFormSet(self.request.POST, prefix='gaf')
        else:
            context['kra_formset'] = KRAFinalRatingFormSet(prefix='kra')
            context['gaf_formset'] = GAFFinalRatingFormSet(prefix='gaf')
            
            # If performance_agreement_id is in GET parameters, pre-populate the form
            pa_id = self.request.GET.get('performance_agreement')
            if pa_id:
                try:
                    pa = PerformanceAgreement.objects.get(id=pa_id)
                    context['form'].fields['performance_agreement'].initial = pa.id
                    
                    # Add the performance agreement to the context
                    context['performance_agreement'] = pa
                    
                    # Add KRAs and GAFs directly to context for easy access in template
                    context['kras'] = KeyResponsibilityArea.objects.filter(performance_agreement=pa)
                    context['gafs'] = GenericAssessmentFactor.objects.filter(performance_agreement=pa, is_applicable=True)
                    
                    # Pre-populate KRA formset
                    kras = context['kras']
                    for i, kra in enumerate(kras):
                        if i < len(context['kra_formset'].forms):
                            context['kra_formset'].forms[i].initial = {
                                'kra': kra.id
                            }
                    
                    # Pre-populate GAF formset
                    gafs = context['gafs']
                    for i, gaf in enumerate(gafs):
                        if i < len(context['gaf_formset'].forms):
                            context['gaf_formset'].forms[i].initial = {
                                'gaf': gaf.id
                            }
                except PerformanceAgreement.DoesNotExist:
                    messages.error(self.request, 'Performance Agreement not found.')
                except Exception as e:
                    messages.error(self.request, f'Error pre-populating form: {str(e)}')
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']

        # Check if formsets are valid
        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Set the employee to the current user
            form.instance.employee = self.request.user
            
            # Set initial status based on user role
            if self.request.user.role == CustomUser.MANAGER:
                form.instance.status = 'SUPERVISOR_REVIEWED'
            else:
                form.instance.status = 'DRAFT'
            
            # Save the review
            self.object = form.save()
            
            # Save KRA ratings
            kra_formset.instance = self.object
            kra_formset.save()
            
            # Save GAF ratings
            gaf_formset.instance = self.object
            gaf_formset.save()
            
            # Send notification to supervisor if submitted by employee
            if form.instance.status == 'DRAFT' and 'submit' in self.request.POST:
                form.instance.status = 'PENDING_SUPERVISOR_REVIEW'
                form.instance.save()
                
                # Get the employee's manager
                manager = self.request.user.manager
                if manager:
                    # Send notification to manager
                    Notification.objects.create(
                        user=manager,
                        message=f"{self.request.user.get_full_name()} has submitted a final review for your review.",
                        link=reverse('performance:final_review_detail', kwargs={'pk': self.object.pk})
                    )
                    
                    messages.success(self.request, 'Final Review submitted for supervisor review.')
                else:
                    messages.warning(self.request, 'Final Review saved, but no supervisor was found to notify.')
            else:
                messages.success(self.request, 'Final Review saved successfully.')
            
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


class FinalReviewDetailView(FinalReviewPermissionMixin, DetailView):
    """
    Display details of a final review.
    """
    model = FinalReview
    template_name = 'performance/final_review_detail.html'
    context_object_name = 'review'
    permission_type = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kra_ratings'] = KRAFinalRating.objects.filter(final_review=self.object)
        context['gaf_ratings'] = GAFFinalRating.objects.filter(final_review=self.object)
        return context


class FinalReviewUpdateView(FinalReviewPermissionMixin, UpdateView):
    """
    Update an existing final review.
    """
    model = FinalReview
    form_class = FinalReviewForm
    template_name = 'performance/final_review_form.html'
    success_url = reverse_lazy('performance:final_review_list')
    permission_type = 'update'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add formsets for KRA and GAF ratings
        if self.request.POST:
            context['kra_formset'] = KRAFinalRatingFormSet(
                self.request.POST, 
                prefix='kra',
                queryset=KRAFinalRating.objects.filter(final_review=self.object)
            )
            context['gaf_formset'] = GAFFinalRatingFormSet(
                self.request.POST, 
                prefix='gaf',
                queryset=GAFFinalRating.objects.filter(final_review=self.object)
            )
        else:
            context['kra_formset'] = KRAFinalRatingFormSet(
                prefix='kra',
                queryset=KRAFinalRating.objects.filter(final_review=self.object)
            )
            context['gaf_formset'] = GAFFinalRatingFormSet(
                prefix='gaf',
                queryset=GAFFinalRating.objects.filter(final_review=self.object)
            )
        
        # Disable fields based on status and user role
        review = self.get_object()
        user = self.request.user
        
        if user.role == CustomUser.MANAGER and review.status in ['PENDING_SUPERVISOR_REVIEW', 'SUPERVISOR_REVIEWED']:
            # Enable supervisor fields for managers
            for field_name, field in context['form'].fields.items():
                if field_name.startswith('supervisor_'):
                    field.disabled = False
                else:
                    field.disabled = True
            
            # Enable supervisor rating fields in formsets
            for form in context['kra_formset'].forms:
                form.fields['supervisor_rating'].disabled = False
                form.fields['supervisor_comments'].disabled = False
                form.fields['kra'].disabled = True
                form.fields['employee_rating'].disabled = True
                form.fields['employee_comments'].disabled = True
            
            for form in context['gaf_formset'].forms:
                form.fields['supervisor_rating'].disabled = False
                form.fields['supervisor_comments'].disabled = False
                form.fields['factor'].disabled = True
                form.fields['employee_rating'].disabled = True
                form.fields['employee_comments'].disabled = True
        
        elif user.role == CustomUser.APPROVER and review.status == 'PENDING_APPROVAL':
            # Enable approver fields for approvers
            for field_name, field in context['form'].fields.items():
                if field_name.startswith('approver_'):
                    field.disabled = False
                else:
                    field.disabled = True
            
            # Disable all fields in formsets
            for form in context['kra_formset'].forms:
                for field in form.fields.values():
                    field.disabled = True
            
            for form in context['gaf_formset'].forms:
                for field in form.fields.values():
                    field.disabled = True
        
        elif user == review.performance_agreement.employee and review.status in ['DRAFT', 'RETURNED']:
            # Enable employee fields for the employee
            for field_name, field in context['form'].fields.items():
                if not field_name.startswith('supervisor_') and not field_name.startswith('approver_'):
                    field.disabled = False
                else:
                    field.disabled = True
            
            # Enable employee rating fields in formsets
            for form in context['kra_formset'].forms:
                form.fields['kra'].disabled = False
                form.fields['employee_rating'].disabled = False
                form.fields['employee_comments'].disabled = False
                form.fields['supervisor_rating'].disabled = True
                form.fields['supervisor_comments'].disabled = True
            
            for form in context['gaf_formset'].forms:
                form.fields['factor'].disabled = False
                form.fields['employee_rating'].disabled = False
                form.fields['employee_comments'].disabled = False
                form.fields['supervisor_rating'].disabled = True
                form.fields['supervisor_comments'].disabled = True
        
        elif user.role == CustomUser.HR:
            # HR can edit all fields
            pass
        
        else:
            # Others can't edit anything
            for field in context['form'].fields.values():
                field.disabled = True
            
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
        action = self.request.POST.get('action', '')
        
        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Save the review
            self.object = form.save(commit=False)
            
            # Check if the user is submitting for review
            review = self.object
            user = self.request.user
            
            if user == review.performance_agreement.employee and action == 'submit':
                # Employee submitting for supervisor review
                review.status = 'PENDING_SUPERVISOR_REVIEW'
                review.employee_rating_date = timezone.now()
                review.save()
                
                # Notify supervisor
                if review.performance_agreement.employee.manager:
                    Notification.objects.create(
                        user=review.performance_agreement.employee.manager,
                        message=f"{review.performance_agreement.employee.get_full_name()} has submitted a final review for your review.",
                        link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                    )
                
                messages.success(self.request, 'Final review submitted for supervisor review.')
                return redirect('performance:final_review_list')
            
            elif user.role == CustomUser.MANAGER and action == 'review':
                # Supervisor reviewing
                review.status = 'SUPERVISOR_REVIEWED'
                review.supervisor_rating_date = timezone.now()
                review.save()
                
                # Notify approvers
                approvers = CustomUser.objects.filter(role=CustomUser.APPROVER)
                for approver in approvers:
                    Notification.objects.create(
                        user=approver,
                        message=f"A final review for {review.performance_agreement.employee.get_full_name()} needs your approval.",
                        link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                    )
                
                # Notify employee
                Notification.objects.create(
                    user=review.performance_agreement.employee,
                    message=f"Your final review has been reviewed by your supervisor and is pending approval.",
                    link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                )
                
                messages.success(self.request, 'Final review submitted for approval.')
                return redirect('performance:final_review_list')
            
            elif user.role == CustomUser.APPROVER and action == 'approve':
                # Approver approving
                review.status = 'APPROVED'
                review.approver_approval_date = timezone.now()
                review.save()
                
                # Notify employee and supervisor
                Notification.objects.create(
                    user=review.performance_agreement.employee,
                    message=f"Your final review has been approved.",
                    link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                )
                
                if review.performance_agreement.employee.manager:
                    Notification.objects.create(
                        user=review.performance_agreement.employee.manager,
                        message=f"The final review for {review.performance_agreement.employee.get_full_name()} has been approved.",
                        link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                    )
                
                messages.success(self.request, 'Final review approved.')
                return redirect('performance:final_review_list')
            
            elif action == 'return':
                # Return for revision
                review.status = 'RETURNED'
                review.save()
                
                # Notify employee
                Notification.objects.create(
                    user=review.performance_agreement.employee,
                    message=f"Your final review has been returned for revision.",
                    link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                )
                
                # Notify supervisor
                if review.performance_agreement.employee.manager:
                    Notification.objects.create(
                        user=review.performance_agreement.employee.manager,
                        message=f"The final review for {review.performance_agreement.employee.get_full_name()} has been returned for revision.",
                        link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
                    )
                
                messages.success(self.request, 'Final review returned for revision.')
                return redirect('performance:final_review_list')
            
            else:
                # Regular save
                review.save()
            
            # Save the formsets
            kra_formset.instance = self.object
            kra_formset.save()
            
            gaf_formset.instance = self.object
            gaf_formset.save()
            
            messages.success(self.request, 'Final review saved successfully.')
            return super().form_valid(form)
        else:
            return self.form_invalid(form)


class FinalReviewDeleteView(FinalReviewPermissionMixin, DeleteView):
    """
    Delete a final review.
    """
    model = FinalReview
    template_name = 'performance/confirm_delete.html'
    success_url = reverse_lazy('performance:final_review_list')
    permission_type = 'delete'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Delete Final Review'
        context['cancel_url'] = 'performance:final_review_detail'
        context['object_name'] = f"Final Review for {self.object.performance_agreement.employee.get_full_name()}"
        return context


@login_required
@final_review_permission('delete')
def final_review_delete(request, pk):
    """
    Delete a final review.
    """
    review = get_object_or_404(FinalReview, pk=pk)
    
    if request.method == 'POST':
        review.delete()
        messages.success(request, 'Final review deleted successfully.')
        return redirect('performance:final_review_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': review,
        'object_name': f"Final Review for {review.performance_agreement.employee.get_full_name()}"
    })


@final_review_permission('update')
def final_review_approve(request, pk):
    """
    Approve a final review.
    """
    review = get_object_or_404(FinalReview, pk=pk)
    
    if request.method == 'POST':
        review.status = 'APPROVED'
        review.approver_approval_date = timezone.now()
        review.save()
        
        # Notify employee and supervisor
        Notification.objects.create(
            user=review.performance_agreement.employee,
            message=f"Your final review has been approved.",
            link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
        )
        
        if review.performance_agreement.employee.manager:
            Notification.objects.create(
                user=review.performance_agreement.employee.manager,
                message=f"The final review for {review.performance_agreement.employee.get_full_name()} has been approved.",
                link=reverse('performance:final_review_detail', kwargs={'pk': review.pk})
            )
        
        messages.success(request, 'Final review approved successfully.')
        return redirect('performance:final_review_list')
    
    return render(request, 'performance/final_review_approve.html', {
        'review': review,
        'employee_name': review.performance_agreement.employee.get_full_name()
    }) 