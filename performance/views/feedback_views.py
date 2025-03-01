"""
Feedback views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.http import JsonResponse

from ..models import (
    Feedback,
    KeyResponsibilityArea,
    ImprovementPlan,
    ImprovementPlanItem
)
from ..forms import (
    FeedbackForm
)


class FeedbackCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new feedback.
    """
    model = Feedback
    form_class = FeedbackForm
    template_name = 'performance/feedback_form.html'
    success_url = reverse_lazy('performance:dashboard')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Set the sender to the current user
        form.instance.sender = self.request.user
        
        # Save the feedback
        self.object = form.save()
        
        messages.success(self.request, 'Feedback submitted successfully!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error in your submission. Please check the form and try again.')
        return super().form_invalid(form)


@login_required
def upload_kra_evidence(request):
    """
    Upload evidence for a KRA.
    """
    if request.method == 'POST':
        kra_id = request.POST.get('kra_id')
        evidence_file = request.FILES.get('evidence_file')
        
        if kra_id and evidence_file:
            try:
                kra = KeyResponsibilityArea.objects.get(id=kra_id)
                
                # Check if the user is the employee of the performance agreement
                if request.user != kra.performance_agreement.employee:
                    return JsonResponse({
                        'success': False,
                        'message': 'You are not authorized to upload evidence for this KRA.'
                    })
                
                # Save the evidence file
                kra.evidence = evidence_file
                kra.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Evidence uploaded successfully!',
                    'file_url': kra.evidence.url,
                    'file_name': kra.evidence.name.split('/')[-1]
                })
            except KeyResponsibilityArea.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'KRA not found.'
                })
        
        return JsonResponse({
            'success': False,
            'message': 'Invalid request. Please provide a KRA ID and an evidence file.'
        })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
def add_to_improvement_plan(request):
    """
    Add an item to an improvement plan.
    """
    if request.method == 'POST':
        employee_id = request.POST.get('employee_id')
        action = request.POST.get('action')
        target_date = request.POST.get('target_date')
        
        if not employee_id or not action or not target_date:
            return JsonResponse({
                'success': False,
                'message': 'Please provide all required fields.'
            })
        
        # Check if an improvement plan exists for the employee
        try:
            plan = ImprovementPlan.objects.filter(employee_id=employee_id, status='IN_PROGRESS').first()
            
            # If no active plan exists, create one
            if not plan:
                plan = ImprovementPlan.objects.create(
                    employee_id=employee_id,
                    supervisor=request.user,
                    status='IN_PROGRESS'
                )
            
            # Add the item to the plan
            item = ImprovementPlanItem.objects.create(
                improvement_plan=plan,
                action=action,
                target_date=target_date,
                progress=0
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Item added to improvement plan successfully!',
                'plan_id': plan.id,
                'item_id': item.id
            })
        
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    }) 