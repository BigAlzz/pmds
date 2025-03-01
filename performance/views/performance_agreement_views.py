"""
Performance Agreement views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseForbidden, JsonResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from io import BytesIO
from django.core.exceptions import PermissionDenied

from ..models import (
    CustomUser,
    PerformanceAgreement,
    KeyResponsibilityArea,
    GenericAssessmentFactor
)
from ..forms import (
    PerformanceAgreementForm,
    KRAFormSet,
    GAFFormSet
)
from ..notifications import notify_user
from ..mixins import PerformanceAgreementPermissionMixin
from ..decorators import performance_agreement_permission
from ..permissions import can_update_performance_agreement


class PerformanceAgreementListView(LoginRequiredMixin, ListView):
    """
    Display a list of performance agreements based on user role.
    """
    model = PerformanceAgreement
    template_name = 'performance/performance_agreement_list.html'
    context_object_name = 'agreements'

    def get_queryset(self):
        user = self.request.user
        print(f"Current user: {user.username}, Role: {user.role}, ID: {user.id}")
        
        if user.is_superuser or user.role == CustomUser.HR:
            # Admin and HR can see all agreements
            return PerformanceAgreement.objects.all()
        elif user.role == CustomUser.MANAGER:
            # Managers can see agreements of their subordinates and their own
            return PerformanceAgreement.objects.filter(
                Q(employee=user) | Q(employee__in=user.subordinates.all())
            )
        elif user.role == CustomUser.APPROVER:
            # Approvers can see agreements pending their approval and their own
            return PerformanceAgreement.objects.filter(
                Q(employee=user) | 
                Q(status=PerformanceAgreement.PENDING_MANAGER_APPROVAL)
            )
        else:
            # Regular employees can only see their own agreements
            agreements = PerformanceAgreement.objects.filter(employee=user)
            print(f"Regular user, showing own agreements. Count: {agreements.count()}")
            return agreements


class PerformanceAgreementCreateView(PerformanceAgreementPermissionMixin, CreateView):
    """
    Create a new performance agreement.
    """
    model = PerformanceAgreement
    form_class = PerformanceAgreementForm
    template_name = 'performance/performance_agreement_form.html'
    success_url = reverse_lazy('performance:performance_agreement_list')
    permission_type = 'create'

    def dispatch(self, request, *args, **kwargs):
        # Check if user profile is complete
        if not request.user.employee_id or not request.user.persal_number:
                messages.warning(request, 'Please complete your profile before creating a performance agreement.')
                return redirect('performance:profile')
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['kra_formset'] = KRAFormSet(self.request.POST, prefix='kras')
            context['gaf_formset'] = GAFFormSet(self.request.POST, prefix='gafs')
        else:
            context['kra_formset'] = KRAFormSet(prefix='kras')
            context['gaf_formset'] = GAFFormSet(prefix='gafs')
            
            # Pre-populate supervisor field if user has a manager
            if self.request.user.manager:
                context['form'].fields['supervisor'].initial = self.request.user.manager.id
            
            # Pre-populate date fields with suggested values
            today = timezone.now().date()
            
            # Determine the fiscal year dates based on current date
            # Fiscal year runs from April to March
            current_year = today.year
            next_year = current_year + 1
            
            # If we're in January-March, fiscal year is previous year to current year
            # If we're in April-December, fiscal year is current year to next year
            if today.month < 4:  # January-March
                start_date = timezone.datetime(current_year - 1, 4, 1).date()
                end_date = timezone.datetime(current_year, 3, 31).date()
                midyear_date = timezone.datetime(current_year - 1, 9, 30).date()
                final_date = timezone.datetime(current_year, 3, 15).date()
            else:  # April-December
                start_date = timezone.datetime(current_year, 4, 1).date()
                end_date = timezone.datetime(next_year, 3, 31).date()
                midyear_date = timezone.datetime(current_year, 9, 30).date()
                final_date = timezone.datetime(next_year, 3, 15).date()
            
            # Set initial values for date fields
            context['form'].fields['plan_start_date'].initial = start_date
            context['form'].fields['plan_end_date'].initial = end_date
            context['form'].fields['midyear_review_date'].initial = midyear_date
            context['form'].fields['final_assessment_date'].initial = final_date
                
            # Pre-populate GAF formset with default values
            for i, form in enumerate(context['gaf_formset']):
                gaf_id = i + 1
                if gaf_id <= 15:  # We have 15 GAFs
                    form.initial = {'factor': f'GAF{gaf_id}', 'is_applicable': False}
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        kra_formset = context['kra_formset']
        gaf_formset = context['gaf_formset']
        
        if kra_formset.is_valid() and gaf_formset.is_valid():
            # Set the employee to the current user
            form.instance.employee = self.request.user
            
            # Save the performance agreement
            self.object = form.save()
            
            # Save the KRA formset
            kra_formset.instance = self.object
            kra_formset.save()
            
            # Save the GAF formset
            gaf_formset.instance = self.object
            gaf_formset.save()
            
            # Notify the supervisor
            if self.object.supervisor:
                notify_user(
                    self.object.supervisor,
                    'APPROVAL',
                    'New Performance Agreement Submitted',
                    f'A new performance agreement has been submitted by {self.request.user.get_full_name()} for your review.',
                    'performance_agreement',
                    self.object.id
                )
            
            messages.success(self.request, 'Performance Agreement created successfully!')
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error in your submission. Please check the form and try again.')
        return super().form_invalid(form)


class PerformanceAgreementDetailView(PerformanceAgreementPermissionMixin, DetailView):
    """
    Display details of a performance agreement.
    """
    model = PerformanceAgreement
    template_name = 'performance/performance_agreement_detail.html'
    context_object_name = 'agreement'
    permission_type = 'view'


class PerformanceAgreementUpdateView(PerformanceAgreementPermissionMixin, UpdateView):
    """
    Update an existing performance agreement.
    """
    model = PerformanceAgreement
    form_class = PerformanceAgreementForm
    template_name = 'performance/performance_agreement_form.html'
    success_url = reverse_lazy('performance:performance_agreement_list')
    permission_type = 'update'

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        
        # Disable fields based on status and user role
        if self.object.status != PerformanceAgreement.DRAFT:
            # If not in draft status, disable most fields
            for field_name, field in form.fields.items():
                if field_name not in ['employee_comments', 'supervisor_comments', 'manager_comments']:
                    field.disabled = True
                    
            # Allow supervisor to edit their comments
            if self.request.user == self.object.supervisor:
                form.fields['supervisor_comments'].disabled = False
                
            # Allow manager/approver to edit their comments
            if self.request.user == self.object.approver:
                form.fields['manager_comments'].disabled = False
                
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        if self.request.POST:
            context['kra_formset'] = KRAFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='kras'
            )
            context['gaf_formset'] = GAFFormSet(
                self.request.POST, 
                instance=self.object,
                prefix='gafs'
            )
        else:
            context['kra_formset'] = KRAFormSet(
                instance=self.object,
                prefix='kras'
            )
            context['gaf_formset'] = GAFFormSet(
                instance=self.object,
                prefix='gafs'
            )
            
            # Disable formset fields if not in draft status
            if self.object.status != PerformanceAgreement.DRAFT:
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
            # Save the performance agreement
            self.object = form.save()
            
            # Save the formsets if in draft status
            if self.object.status == PerformanceAgreement.DRAFT:
                kra_formset.save()
                gaf_formset.save()
            
            # Check if the form has a 'submit_action' field to determine the action
            submit_action = self.request.POST.get('submit_action', 'save')
            
            if submit_action == 'submit_for_review' and self.object.status == PerformanceAgreement.DRAFT:
                # Employee submitting for supervisor review
                self.object.status = PerformanceAgreement.PENDING_SUPERVISOR_REVIEW
                self.object.submission_date = timezone.now()
                self.object.save()
                
                # Notify supervisor
                if self.object.supervisor:
                    notify_user(
                        self.object.supervisor,
                        'APPROVAL',
                        'Performance Agreement Needs Review',
                        f'A performance agreement from {self.object.employee.get_full_name()} needs your review.',
                        'performance_agreement',
                        self.object.id
                    )
                
                messages.success(self.request, 'Performance Agreement submitted for supervisor review.')
            
            elif submit_action == 'supervisor_approve' and self.object.status == PerformanceAgreement.PENDING_SUPERVISOR_REVIEW:
                # Supervisor approving
                self.object.status = PerformanceAgreement.PENDING_MANAGER_APPROVAL
                self.object.supervisor_approval_date = timezone.now()
                self.object.save()
                
                # Notify manager/approver
                if self.object.approver:
                    notify_user(
                        self.object.approver,
                        'APPROVAL',
                        'Performance Agreement Needs Approval',
                        f'A performance agreement from {self.object.employee.get_full_name()} needs your approval.',
                        'performance_agreement',
                        self.object.id
                    )
                
                # Notify employee
                notify_user(
                    self.object.employee,
                    'STATUS_UPDATE',
                    'Performance Agreement Approved by Supervisor',
                    f'Your performance agreement has been approved by your supervisor and is now pending manager approval.',
                    'performance_agreement',
                    self.object.id
                )
                
                messages.success(self.request, 'Performance Agreement approved and sent for manager approval.')
            
            elif (submit_action == 'manager_approve' and 
                  (self.request.user == self.object.approver or 
                   (self.request.user.role == CustomUser.HR and self.object.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL))):
                # Manager/Approver approving
                self.object.status = PerformanceAgreement.PENDING_HR_VERIFICATION
                self.object.manager_approval_date = timezone.now()
                self.object.save()
                
                # Notify HR
                hr_users = CustomUser.objects.filter(role=CustomUser.HR)
                for hr_user in hr_users:
                    notify_user(
                        hr_user,
                        'VERIFICATION',
                        'Performance Agreement Needs Verification',
                        f'A performance agreement from {self.object.employee.get_full_name()} needs your verification.',
                        'performance_agreement',
                        self.object.id
                    )
                
                # Notify employee
                notify_user(
                    self.object.employee,
                    'STATUS_UPDATE',
                    'Performance Agreement Approved by Manager',
                    f'Your performance agreement has been approved by the manager and is now pending HR verification.',
                    'performance_agreement',
                    self.object.id
                )
                
                # Notify supervisor
                if self.object.supervisor:
                    notify_user(
                        self.object.supervisor,
                        'STATUS_UPDATE',
                        'Performance Agreement Approved by Manager',
                        f'The performance agreement for {self.object.employee.get_full_name()} has been approved by the manager.',
                        'performance_agreement',
                        self.object.id
                    )
                
                messages.success(self.request, 'Performance Agreement approved and sent for HR verification!')
                
            elif (submit_action == 'hr_verify' and 
                  self.request.user.role == CustomUser.HR and 
                  self.object.status == PerformanceAgreement.PENDING_HR_VERIFICATION):
                # HR verifying
                self.object.status = PerformanceAgreement.COMPLETED
                self.object.hr_verification_date = timezone.now()
                self.object.hr_verifier = self.request.user
                self.object.completion_date = timezone.now()
                self.object.save()
                
                # Log the audit event
                from ..utils import log_audit_event
                from ..models import AuditTrail
                log_audit_event(
                    user=self.request.user,
                    action=AuditTrail.ACTION_VERIFY,
                    request=self.request,
                    obj=self.object,
                    details=f"HR verified performance agreement for {self.object.employee.get_full_name()}"
                )
                
                # Notify employee
                notify_user(
                    self.object.employee,
                    'VERIFICATION',
                    'Performance Agreement Verified',
                    f'Your performance agreement has been verified by HR and is now complete.',
                    'performance_agreement',
                    self.object.id
                )
                
                # Notify supervisor
                if self.object.supervisor:
                    notify_user(
                        self.object.supervisor,
                        'VERIFICATION',
                        'Performance Agreement Verified',
                        f'The performance agreement for {self.object.employee.get_full_name()} has been verified by HR.',
                        'performance_agreement',
                        self.object.id
                    )
                
                messages.success(self.request, 'Performance Agreement verified successfully!')
            
            else:
                messages.success(self.request, 'Performance Agreement updated successfully!')
            
            return redirect(self.get_success_url())
        else:
            return self.form_invalid(form)


@login_required
@performance_agreement_permission('update')
def performance_agreement_submit(request, pk):
    """
    Submit a performance agreement for supervisor review.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    if agreement.status != PerformanceAgreement.DRAFT:
        messages.error(request, 'This performance agreement cannot be submitted because it is not in draft status.')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    agreement.status = PerformanceAgreement.PENDING_SUPERVISOR_REVIEW
    agreement.submission_date = timezone.now()
    agreement.save()
    
    # Notify supervisor
    if agreement.supervisor:
        notify_user(
            agreement.supervisor,
            'APPROVAL',
            'Performance Agreement Needs Review',
            f'A performance agreement from {agreement.employee.get_full_name()} needs your review.',
            'performance_agreement',
            agreement.id
        )
    
    messages.success(request, 'Performance Agreement submitted for supervisor review.')
    return redirect('performance:performance_agreement_detail', pk=pk)


@login_required
@performance_agreement_permission('update')
def performance_agreement_approve(request, pk):
    """
    Approve a performance agreement.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    user = request.user
    
    # Check if the user is authorized to approve
    if user == agreement.supervisor and agreement.status == PerformanceAgreement.PENDING_SUPERVISOR_REVIEW:
        # Supervisor approving
        agreement.status = PerformanceAgreement.PENDING_MANAGER_APPROVAL
        agreement.supervisor_approval_date = timezone.now()
        agreement.save()
        
        # Notify manager/approver
        if agreement.approver:
            notify_user(
                agreement.approver,
                'APPROVAL',
                'Performance Agreement Needs Approval',
                f'A performance agreement from {agreement.employee.get_full_name()} needs your approval.',
                'performance_agreement',
                agreement.id
            )
        
        # Notify employee
        notify_user(
            agreement.employee,
            'STATUS_UPDATE',
            'Performance Agreement Approved by Supervisor',
            f'Your performance agreement has been approved by your supervisor and is now pending manager approval.',
            'performance_agreement',
            agreement.id
        )
        
        messages.success(request, 'Performance Agreement approved and sent for manager approval.')
    
    elif ((user == agreement.approver or user.role == CustomUser.HR) and 
          agreement.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL):
        # Manager/Approver approving
        agreement.status = PerformanceAgreement.COMPLETED
        agreement.manager_approval_date = timezone.now()
        agreement.completion_date = timezone.now()
        agreement.save()
        
        # Notify employee
        notify_user(
            agreement.employee,
            'APPROVAL',
            'Performance Agreement Approved',
            f'Your performance agreement has been approved by {user.get_full_name()}.',
            'performance_agreement',
            agreement.id
        )
        
        # Notify supervisor
        if agreement.supervisor:
            notify_user(
                agreement.supervisor,
                'APPROVAL',
                'Performance Agreement Approved',
                f'The performance agreement for {agreement.employee.get_full_name()} has been approved.',
                'performance_agreement',
                agreement.id
            )
        
        messages.success(request, 'Performance Agreement approved successfully!')
    
    else:
        messages.error(request, 'You are not authorized to approve this performance agreement.')
    
    return redirect('performance:performance_agreement_detail', pk=pk)


@login_required
@performance_agreement_permission('update')
def performance_agreement_reject(request, pk):
    """
    Reject a performance agreement.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', '')
        
        # Update status
        if agreement.status == PerformanceAgreement.PENDING_SUPERVISOR_REVIEW:
            agreement.status = PerformanceAgreement.DRAFT
            agreement.supervisor_comments = f"Rejected: {rejection_reason}\n\n{agreement.supervisor_comments or ''}"
        elif agreement.status == PerformanceAgreement.PENDING_MANAGER_APPROVAL:
            agreement.status = PerformanceAgreement.PENDING_SUPERVISOR_REVIEW
            agreement.manager_comments = f"Rejected: {rejection_reason}\n\n{agreement.manager_comments or ''}"
        
        agreement.save()
        
        # Notify the appropriate user
        if agreement.status == PerformanceAgreement.DRAFT:
            # Notify employee
            notify_user(
                agreement.employee,
                'REJECTION',
                'Performance Agreement Rejected',
                f'Your performance agreement has been rejected by your supervisor. Reason: {rejection_reason}',
                'performance_agreement',
                agreement.id
            )
        else:
            # Notify supervisor
            notify_user(
                agreement.supervisor,
                'REJECTION',
                'Performance Agreement Rejected by Manager',
                f'The performance agreement for {agreement.employee.get_full_name()} has been rejected by the manager. Reason: {rejection_reason}',
                'performance_agreement',
                agreement.id
            )
        
        messages.success(request, 'Performance Agreement rejected successfully!')
        return redirect('performance:performance_agreement_detail', pk=pk)
    
    return render(request, 'performance/reject_form.html', {
        'object': agreement,
        'title': 'Reject Performance Agreement',
        'message': f'Please provide a reason for rejecting the performance agreement for {agreement.employee.get_full_name()}:',
    })


@login_required
@performance_agreement_permission('delete')
def performance_agreement_delete(request, pk):
    """
    Delete a performance agreement.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    if request.method == 'POST':
        agreement.delete()
        messages.success(request, 'Performance Agreement deleted successfully!')
        return redirect('performance:performance_agreement_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': agreement,
        'title': 'Delete Performance Agreement',
        'cancel_url': 'performance:performance_agreement_detail',
        'object_name': f"Performance Agreement for {agreement.employee.get_full_name()}"
    })


@login_required
@performance_agreement_permission('view')
def export_agreement_pdf(request, pk):
    """
    Export a performance agreement as a PDF.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    # Create a file-like buffer to receive PDF data
    buffer = BytesIO()
    
    # Create the PDF object, using the buffer as its "file"
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Container for the 'Flowable' objects
    elements = []
    
    # Define styles
    styles = getSampleStyleSheet()
    title_style = styles['Heading1']
    subtitle_style = styles['Heading2']
    normal_style = styles['Normal']
    
    # Add title
    elements.append(Paragraph(f"Performance Agreement", title_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add employee information
    elements.append(Paragraph(f"Employee: {agreement.employee.get_full_name()}", subtitle_style))
    elements.append(Paragraph(f"Employee ID: {agreement.employee.employee_id}", normal_style))
    elements.append(Paragraph(f"Department: {agreement.employee.department or 'N/A'}", normal_style))
    elements.append(Paragraph(f"Period: {agreement.plan_start_date.strftime('%Y-%m-%d')} to {agreement.plan_end_date.strftime('%Y-%m-%d')}", normal_style))
    elements.append(Spacer(1, 0.25*inch))
    
    # Add KRAs
    elements.append(Paragraph("Key Responsibility Areas", subtitle_style))
    
    # Create KRA table
    kra_data = [['#', 'Description', 'Weight']]
    for i, kra in enumerate(agreement.kras.all(), 1):
        kra_data.append([i, kra.description, f"{kra.weighting}%"])
    
    kra_table = Table(kra_data, colWidths=[0.5*inch, 5*inch, 1*inch])
    kra_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(kra_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add GAFs
    elements.append(Paragraph("Generic Assessment Factors", subtitle_style))
    
    # Create GAF table
    gaf_data = [['#', 'Factor', 'Applicable']]
    for i, gaf in enumerate(agreement.genericassessmentfactor_set.all(), 1):
        gaf_data.append([i, gaf.factor, 'Yes' if gaf.is_applicable else 'No'])
    
    gaf_table = Table(gaf_data, colWidths=[0.5*inch, 5*inch, 1*inch])
    gaf_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(gaf_table)
    elements.append(Spacer(1, 0.25*inch))
    
    # Add comments
    elements.append(Paragraph("Comments", subtitle_style))
    
    if agreement.employee_comments:
        elements.append(Paragraph(f"Employee Comments:", styles['Heading3']))
        elements.append(Paragraph(agreement.employee_comments, normal_style))
        elements.append(Spacer(1, 0.1*inch))
    
    if agreement.supervisor_comments:
        elements.append(Paragraph(f"Supervisor Comments:", styles['Heading3']))
        elements.append(Paragraph(agreement.supervisor_comments, normal_style))
        elements.append(Spacer(1, 0.1*inch))
    
    if agreement.manager_comments:
        elements.append(Paragraph(f"Manager Comments:", styles['Heading3']))
        elements.append(Paragraph(agreement.manager_comments, normal_style))
    
    # Add approval information
    elements.append(Spacer(1, 0.25*inch))
    elements.append(Paragraph("Approval Information", subtitle_style))
    
    if agreement.submission_date:
        elements.append(Paragraph(f"Submitted: {agreement.submission_date.strftime('%Y-%m-%d')}", normal_style))
    
    if agreement.supervisor_approval_date:
        elements.append(Paragraph(f"Supervisor Approval: {agreement.supervisor_approval_date.strftime('%Y-%m-%d')}", normal_style))
    
    if agreement.manager_approval_date:
        elements.append(Paragraph(f"Manager Approval: {agreement.manager_approval_date.strftime('%Y-%m-%d')}", normal_style))
    
    # Build the PDF
    doc.build(elements)
    
    # Get the value of the BytesIO buffer and write it to the response
    pdf = buffer.getvalue()
    buffer.close()
    
    # Create the HttpResponse object with the appropriate PDF headers
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="performance_agreement_{agreement.id}.pdf"'
    
    return response 


@login_required
@permission_required('performance.change_performanceagreement')
def return_performance_agreement(request, pk):
    """
    View for HR to return a performance agreement for correction.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    # Check if user has permission to return this agreement
    if not can_update_performance_agreement(request.user, agreement):
        raise PermissionDenied("You don't have permission to return this agreement.")
    
    # Check if agreement is in a state that can be returned
    if agreement.status not in [PerformanceAgreement.PENDING_HR_VERIFICATION]:
        messages.error(request, "This agreement cannot be returned in its current state.")
        return redirect('performance_agreement_detail', pk=agreement.pk)
    
    if request.method == 'POST':
        return_reason = request.POST.get('return_reason', '')
        
        if not return_reason:
            messages.error(request, "Please provide a reason for returning the agreement.")
            return redirect('performance_agreement_detail', pk=agreement.pk)
        
        # Update agreement status and return details
        agreement.status = PerformanceAgreement.DRAFT
        agreement.return_reason = return_reason
        agreement.return_date = timezone.now()
        agreement.save()
        
        # Log the audit event
        from ..utils import log_audit_event
        from ..models import AuditTrail
        log_audit_event(
            user=request.user,
            action=AuditTrail.ACTION_UPDATE,
            request=request,
            obj=agreement,
            details=f"HR returned performance agreement for correction: {return_reason}"
        )
        
        # Notify employee
        notify_user(
            agreement.employee,
            'CORRECTION',
            'Performance Agreement Returned for Correction',
            f'Your performance agreement has been returned for correction. Reason: {return_reason}',
            'performance_agreement',
            agreement.id
        )
        
        # Notify supervisor
        if agreement.supervisor:
            notify_user(
                agreement.supervisor,
                'CORRECTION',
                'Performance Agreement Returned for Correction',
                f'The performance agreement for {agreement.employee.get_full_name()} has been returned for correction. Reason: {return_reason}',
                'performance_agreement',
                agreement.id
            )
        
        messages.success(request, "Performance Agreement has been returned for correction.")
        return redirect('performance_agreement_list')
    
    return render(request, 'performance/return_performance_agreement.html', {
        'agreement': agreement,
    })


@login_required
@permission_required('performance.change_performanceagreement')
def performance_agreement_hr_verify(request, pk):
    """
    View for HR to verify a performance agreement.
    """
    agreement = get_object_or_404(PerformanceAgreement, pk=pk)
    
    # Check if user has permission to verify this agreement
    if not can_update_performance_agreement(request.user, agreement):
        raise PermissionDenied("You don't have permission to verify this agreement.")
    
    # Check if agreement is in a state that can be verified
    if agreement.status != PerformanceAgreement.PENDING_HR_VERIFICATION:
        messages.error(request, "This agreement cannot be verified in its current state.")
        return redirect('performance_agreement_detail', pk=agreement.pk)
    
    if request.method == 'POST':
        hr_comments = request.POST.get('hr_comments', '')
        
        # Update agreement status and verification details
        agreement.status = PerformanceAgreement.COMPLETED
        agreement.hr_verification_date = timezone.now()
        agreement.hr_verifier = request.user
        agreement.hr_comments = hr_comments
        agreement.completion_date = timezone.now()
        agreement.save()
        
        # Log the audit event
        from ..utils import log_audit_event
        from ..models import AuditTrail
        log_audit_event(
            user=request.user,
            action=AuditTrail.ACTION_VERIFY,
            request=request,
            obj=agreement,
            details=f"HR verified performance agreement for {agreement.employee.get_full_name()}"
        )
        
        # Notify employee
        notify_user(
            agreement.employee,
            'VERIFICATION',
            'Performance Agreement Verified',
            f'Your performance agreement has been verified by HR and is now complete.',
            'performance_agreement',
            agreement.id
        )
        
        # Notify supervisor
        if agreement.supervisor:
            notify_user(
                agreement.supervisor,
                'VERIFICATION',
                'Performance Agreement Verified',
                f'The performance agreement for {agreement.employee.get_full_name()} has been verified by HR.',
                'performance_agreement',
                agreement.id
            )
        
        messages.success(request, "Performance Agreement has been verified successfully.")
        return redirect('performance_agreement_list')
    
    return render(request, 'performance/performance_agreement_hr_verify.html', {
        'agreement': agreement,
    }) 