"""
Improvement Plan views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy, reverse
from django.contrib import messages
from django.db.models import Q

from ..models import (
    CustomUser,
    ImprovementPlan,
    ImprovementPlanItem,
    Notification
)
from ..forms import (
    ImprovementPlanForm,
    ImprovementPlanItemForm
)
from ..mixins import ImprovementPlanPermissionMixin
from ..decorators import improvement_plan_permission


class ImprovementPlanListView(LoginRequiredMixin, ListView):
    """
    Display a list of improvement plans based on user role.
    """
    model = ImprovementPlan
    template_name = 'performance/improvement_plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        user = self.request.user
        
        if user.is_superuser or user.role == CustomUser.HR:
            # Admin and HR can see all plans
            return ImprovementPlan.objects.all()
        elif user.role == CustomUser.MANAGER:
            # Managers can see plans of their subordinates and their own
            return ImprovementPlan.objects.filter(
                Q(employee=user) | Q(employee__in=user.subordinates.all())
            )
        else:
            # Regular employees can only see their own plans
            return ImprovementPlan.objects.filter(employee=user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Improvement Plans'
        context['item_name'] = 'Improvement Plan'
        context['create_url'] = 'improvement_plan_create'
        context['detail_url'] = 'improvement_plan_detail'
        context['update_url'] = 'improvement_plan_update'
        context['delete_url'] = 'improvement_plan_delete'
        return context


class ImprovementPlanCreateView(ImprovementPlanPermissionMixin, CreateView):
    """
    Create a new improvement plan.
    """
    model = ImprovementPlan
    form_class = ImprovementPlanForm
    template_name = 'performance/improvement_plan_form.html'
    success_url = reverse_lazy('performance:improvement_plan_list')
    permission_type = 'create'

    def form_valid(self, form):
        # Set the supervisor to the current user if they are a manager
        if self.request.user.role == CustomUser.MANAGER:
            form.instance.supervisor = self.request.user
        
        # Save the improvement plan
        self.object = form.save()
        
        # Send notification to employee
        if self.object.employee:
            Notification.objects.create(
                user=self.object.employee,
                message=f"An improvement plan has been created for you.",
                link=reverse('performance:improvement_plan_detail', kwargs={'pk': self.object.pk})
            )
        
        messages.success(self.request, 'Improvement Plan created successfully!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error in your submission. Please check the form and try again.')
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ImprovementPlanDetailView(ImprovementPlanPermissionMixin, DetailView):
    """
    Display details of an improvement plan.
    """
    model = ImprovementPlan
    template_name = 'performance/improvement_plan_detail.html'
    context_object_name = 'plan'
    permission_type = 'view'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['items'] = ImprovementPlanItem.objects.filter(improvement_plan=self.object)
        return context


class ImprovementPlanUpdateView(ImprovementPlanPermissionMixin, UpdateView):
    """
    Update an existing improvement plan.
    """
    model = ImprovementPlan
    form_class = ImprovementPlanForm
    template_name = 'performance/improvement_plan_form.html'
    success_url = reverse_lazy('performance:improvement_plan_list')
    permission_type = 'update'

    def form_valid(self, form):
        # Update the improvement plan
        self.object = form.save()
        
        # Send notification to employee if status changed
        if 'status' in form.changed_data and self.object.employee:
            status_message = f"Your improvement plan status has been updated to {self.object.get_status_display()}."
            Notification.objects.create(
                user=self.object.employee,
                message=status_message,
                link=reverse('performance:improvement_plan_detail', kwargs={'pk': self.object.pk})
            )
        
        messages.success(self.request, 'Improvement Plan updated successfully!')
        return redirect(self.get_success_url())


class ImprovementPlanItemCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new improvement plan item.
    """
    model = ImprovementPlanItem
    form_class = ImprovementPlanItemForm
    template_name = 'performance/improvement_plan_item_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Get the improvement plan
        self.improvement_plan = get_object_or_404(ImprovementPlan, pk=self.kwargs.get('plan_id'))
        
        # Check if user has permission to add items to this plan
        if not request.user.is_superuser and not request.user.role == CustomUser.HR:
            if request.user != self.improvement_plan.supervisor:
                messages.error(request, "You don't have permission to add items to this improvement plan.")
                return redirect('performance:improvement_plan_detail', pk=self.improvement_plan.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['improvement_plan'] = self.improvement_plan
        context['title'] = 'Add Improvement Plan Item'
        return context

    def form_valid(self, form):
        # Set the improvement plan
        form.instance.improvement_plan = self.improvement_plan
        
        # Save the item
        self.object = form.save()
        
        # Send notification to employee
        if self.improvement_plan.employee:
            Notification.objects.create(
                user=self.improvement_plan.employee,
                message=f"A new item has been added to your improvement plan.",
                link=reverse('performance:improvement_plan_detail', kwargs={'pk': self.improvement_plan.pk})
            )
        
        messages.success(self.request, 'Improvement Plan Item added successfully!')
        return redirect('performance:improvement_plan_detail', pk=self.improvement_plan.pk)


class ImprovementPlanItemUpdateView(LoginRequiredMixin, UpdateView):
    """
    Update an existing improvement plan item.
    """
    model = ImprovementPlanItem
    form_class = ImprovementPlanItemForm
    template_name = 'performance/improvement_plan_item_form.html'

    def dispatch(self, request, *args, **kwargs):
        # Get the item
        self.object = self.get_object()
        
        # Check if user has permission to update this item
        if not request.user.is_superuser and not request.user.role == CustomUser.HR:
            if request.user != self.object.improvement_plan.supervisor:
                messages.error(request, "You don't have permission to update this improvement plan item.")
                return redirect('performance:improvement_plan_detail', pk=self.object.improvement_plan.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['improvement_plan'] = self.object.improvement_plan
        context['title'] = 'Update Improvement Plan Item'
        return context

    def form_valid(self, form):
        # Save the item
        self.object = form.save()
        
        # Check if progress was updated
        if 'progress' in form.changed_data:
            # Send notification to employee
            if self.object.improvement_plan.employee:
                Notification.objects.create(
                    user=self.object.improvement_plan.employee,
                    message=f"Progress on an improvement plan item has been updated.",
                    link=reverse('performance:improvement_plan_detail', kwargs={'pk': self.object.improvement_plan.pk})
                )
        
        messages.success(self.request, 'Improvement Plan Item updated successfully!')
        return redirect('performance:improvement_plan_detail', pk=self.object.improvement_plan.pk)

    def get_success_url(self):
        return reverse('performance:improvement_plan_detail', kwargs={'pk': self.object.improvement_plan.pk})


@login_required
@improvement_plan_permission('delete')
def improvement_plan_delete(request, pk):
    """
    Delete an improvement plan.
    """
    plan = get_object_or_404(ImprovementPlan, pk=pk)
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Improvement Plan deleted successfully!')
        return redirect('performance:improvement_plan_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': plan,
        'title': 'Delete Improvement Plan',
        'cancel_url': 'performance:improvement_plan_detail',
        'object_name': f"Improvement Plan for {plan.employee.get_full_name()}"
    })


@login_required
@improvement_plan_permission('delete')
def improvement_plan_item_delete(request, pk):
    """
    Delete an improvement plan item.
    """
    item = get_object_or_404(ImprovementPlanItem, pk=pk)
    plan_id = item.improvement_plan.pk
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Improvement Plan Item deleted successfully!')
        return redirect('performance:improvement_plan_detail', pk=plan_id)
    
    return render(request, 'performance/confirm_delete.html', {
        'object': item,
        'title': 'Delete Improvement Plan Item',
        'cancel_url': 'performance:improvement_plan_detail',
        'cancel_kwargs': {'pk': plan_id},
        'object_name': f"Improvement Plan Item: {item.action}"
    }) 