from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
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
    GenericAssessmentFactor
)
from .forms import (
    PerformanceAgreementForm,
    MidYearReviewForm,
    ImprovementPlanForm,
    PersonalDevelopmentPlanForm,
    KRAFormSet,
    GAFFormSet,
    UserProfileForm
)
from .notifications import notify_user

# Dashboard views
@login_required
def dashboard(request):
    context = {
        'performance_agreements': PerformanceAgreement.objects.filter(employee=request.user),
        'reviews': MidYearReview.objects.filter(performance_agreement__employee=request.user),
        'improvement_plans': ImprovementPlan.objects.filter(employee=request.user),
        'development_plans': PersonalDevelopmentPlan.objects.filter(employee=request.user),
    }
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
            context['gaf_formset'] = GAFFormSet(
                initial=[{'factor': factor[0], 'is_applicable': False} for factor in GenericAssessmentFactor.GAF_CHOICES]
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
            kra_formset.save()
            
            gaf_formset.instance = self.object
            gaf_formset.save()
            
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['kra_formset'] = KRAFormSet(self.request.POST, instance=self.object)
            context['gaf_formset'] = GAFFormSet(self.request.POST, instance=self.object)
        else:
            context['kra_formset'] = KRAFormSet(instance=self.object)
            # Initialize GAF formset with existing GAFs or create new ones
            if self.object.gafs.exists():
                context['gaf_formset'] = GAFFormSet(instance=self.object)
            else:
                context['gaf_formset'] = GAFFormSet(
                    instance=self.object,
                    initial=[{'factor': factor[0]} for factor in GenericAssessmentFactor.GAF_CHOICES]
                )
        context['user_profile'] = self.request.user
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']
        
        if kra_formset.is_valid() and gaf_formset.is_valid():
            self.object = form.save()
            kra_formset.instance = self.object
            kra_formset.save()
            
            gaf_formset.instance = self.object
            gaf_formset.save()
            
            messages.success(self.request, 'Performance Agreement updated successfully!')
            return redirect(self.success_url)
        else:
            messages.error(self.request, 'Please correct the errors below.')
            return self.render_to_response(self.get_context_data(form=form))

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PerformanceAgreement.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PerformanceAgreement.objects.filter(supervisor=self.request.user)
        return PerformanceAgreement.objects.filter(employee=self.request.user)

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
    template_name = 'performance/midyear_review_form.html'
    fields = ['performance_agreement', 'self_rating', 'supervisor_rating', 'final_rating', 'comments']
    success_url = reverse_lazy('midyear_review_list')

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

class MidYearReviewUpdateView(LoginRequiredMixin, UpdateView):
    model = MidYearReview
    template_name = 'performance/midyear_review_form.html'
    fields = ['self_rating', 'supervisor_rating', 'final_rating', 'comments']
    success_url = reverse_lazy('midyear_review_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return MidYearReview.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return MidYearReview.objects.filter(performance_agreement__employee__manager=self.request.user)
        return MidYearReview.objects.filter(performance_agreement__employee=self.request.user)

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

class ImprovementPlanCreateView(LoginRequiredMixin, CreateView):
    model = ImprovementPlan
    template_name = 'performance/improvement_plan_form.html'
    fields = ['area_for_development', 'interventions', 'timeline']
    success_url = reverse_lazy('improvement_plan_list')

    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

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
    template_name = 'performance/improvement_plan_form.html'
    fields = ['area_for_development', 'interventions', 'timeline', 'status']
    success_url = reverse_lazy('improvement_plan_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return ImprovementPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return ImprovementPlan.objects.filter(employee__manager=self.request.user)
        return ImprovementPlan.objects.filter(employee=self.request.user)

# Personal Development Plan views
class PersonalDevelopmentPlanListView(LoginRequiredMixin, ListView):
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PersonalDevelopmentPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PersonalDevelopmentPlan.objects.filter(employee__manager=self.request.user)
        return PersonalDevelopmentPlan.objects.filter(employee=self.request.user)

class PersonalDevelopmentPlanCreateView(LoginRequiredMixin, CreateView):
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_form.html'
    fields = ['competency_gap', 'development_activities', 'timeline', 'expected_outcome', 'start_date', 'end_date']
    success_url = reverse_lazy('development_plan_list')

    def form_valid(self, form):
        form.instance.employee = self.request.user
        return super().form_valid(form)

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
    template_name = 'performance/development_plan_form.html'
    fields = ['competency_gap', 'development_activities', 'timeline', 'expected_outcome', 'start_date', 'end_date', 'progress']
    success_url = reverse_lazy('development_plan_list')

    def get_queryset(self):
        if self.request.user.role == CustomUser.HR:
            return PersonalDevelopmentPlan.objects.all()
        elif self.request.user.role == CustomUser.MANAGER:
            return PersonalDevelopmentPlan.objects.filter(employee__manager=self.request.user)
        return PersonalDevelopmentPlan.objects.filter(employee=self.request.user)

# Feedback views
class FeedbackCreateView(LoginRequiredMixin, CreateView):
    model = Feedback
    template_name = 'performance/feedback_form.html'
    fields = ['feedback', 'anonymous']
    success_url = reverse_lazy('dashboard')

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
        return redirect('notification_preferences')
    
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
