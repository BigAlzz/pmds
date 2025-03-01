"""
Personal Development Plan views for the performance app.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse

from ..models import (
    CustomUser,
    PersonalDevelopmentPlan
)
from ..forms import (
    PersonalDevelopmentPlanForm
)
from ..mixins import DevelopmentPlanPermissionMixin
from ..decorators import development_plan_permission


class PersonalDevelopmentPlanListView(LoginRequiredMixin, ListView):
    """
    Display a list of personal development plans based on user role.
    """
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_list.html'
    context_object_name = 'plans'

    def get_queryset(self):
        user = self.request.user
        print(f"Current user: {user.username}, Role: {user.role}, ID: {user.id}")
        
        if user.is_superuser or user.role == CustomUser.HR:
            # Admin and HR can see all plans
            return PersonalDevelopmentPlan.objects.all()
        elif user.role == CustomUser.MANAGER:
            # Managers can see plans of their subordinates and their own
            plans = PersonalDevelopmentPlan.objects.filter(
                Q(employee=user) | Q(employee__in=user.subordinates.all())
            )
            print(f"Manager, showing own and subordinates' plans. Count: {plans.count()}")
            return plans
        else:
            # Regular employees can only see their own plans
            plans = PersonalDevelopmentPlan.objects.filter(employee=user)
            print(f"Regular user, showing own plans. Count: {plans.count()}")
            print(f"Plans in queryset: {list(plans.values('id', 'employee__username', 'competency_gap'))}")
            return plans

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Personal Development Plans'
        context['item_name'] = 'Development Plan'
        context['create_url'] = 'development_plan_create'
        context['detail_url'] = 'development_plan_detail'
        context['update_url'] = 'development_plan_update'
        context['delete_url'] = 'development_plan_delete'
        print(f"Context data: {context.keys()}")
        print(f"Plans in context: {context['plans']}")
        return context


class PersonalDevelopmentPlanCreateView(DevelopmentPlanPermissionMixin, CreateView):
    """
    Create a new personal development plan.
    """
    model = PersonalDevelopmentPlan
    form_class = PersonalDevelopmentPlanForm
    template_name = 'performance/development_plan_form.html'
    success_url = reverse_lazy('performance:development_plan_list')
    permission_type = 'create'

    def form_valid(self, form):
        # Set the employee to the current user if not specified
        if not form.instance.employee:
            form.instance.employee = self.request.user
        
        # Save the development plan
        self.object = form.save()
        
        messages.success(self.request, 'Personal Development Plan created successfully!')
        return redirect(self.get_success_url())

    def form_invalid(self, form):
        messages.error(self.request, 'There was an error in your submission. Please check the form and try again.')
        return super().form_invalid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # If user is a manager, allow them to select an employee
        if self.request.user.role == CustomUser.MANAGER:
            kwargs['user'] = self.request.user
        else:
            # For regular employees, pre-select themselves
            kwargs['user'] = None
        return kwargs


class PersonalDevelopmentPlanDetailView(DevelopmentPlanPermissionMixin, DetailView):
    """
    Display details of a personal development plan.
    """
    model = PersonalDevelopmentPlan
    template_name = 'performance/development_plan_detail.html'
    context_object_name = 'plan'
    permission_type = 'view'


class PersonalDevelopmentPlanUpdateView(DevelopmentPlanPermissionMixin, UpdateView):
    """
    Update an existing personal development plan.
    """
    model = PersonalDevelopmentPlan
    form_class = PersonalDevelopmentPlanForm
    template_name = 'performance/development_plan_form.html'
    success_url = reverse_lazy('performance:development_plan_list')
    permission_type = 'update'

    def form_valid(self, form):
        # Save the development plan
        self.object = form.save()
        
        messages.success(self.request, 'Personal Development Plan updated successfully!')
        return redirect(self.get_success_url())

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # If user is a manager, allow them to select an employee
        if self.request.user.role == CustomUser.MANAGER:
            kwargs['user'] = self.request.user
        else:
            # For regular employees, pre-select themselves
            kwargs['user'] = None
        return kwargs


@login_required
@development_plan_permission('delete')
def development_plan_delete(request, pk):
    """
    Delete a personal development plan.
    """
    plan = get_object_or_404(PersonalDevelopmentPlan, pk=pk)
    
    if request.method == 'POST':
        plan.delete()
        messages.success(request, 'Personal Development Plan deleted successfully!')
        return redirect('performance:development_plan_list')
    
    return render(request, 'performance/confirm_delete.html', {
        'object': plan,
        'title': 'Delete Personal Development Plan',
        'cancel_url': 'performance:development_plan_detail',
        'object_name': f"Personal Development Plan for {plan.employee.get_full_name()}"
    })


@login_required
def test_development_plans_view(request):
    """
    Test view for debugging development plans.
    """
    user = request.user
    print(f"Test view - Current user: {user.username}, Role: {user.role}, ID: {user.id}")
    
    # Get all plans for the user
    plans = PersonalDevelopmentPlan.objects.filter(employee=user)
    print(f"Plans for user: {plans.count()}")
    
    # Get details of each plan
    plan_details = []
    for plan in plans:
        plan_details.append({
            'id': plan.id,
            'competency_gap': plan.competency_gap,
            'development_need': plan.development_need,
            'action_plan': plan.action_plan,
            'target_date': plan.target_date.strftime('%Y-%m-%d') if plan.target_date else None,
            'status': plan.get_status_display()
        })
    
    return JsonResponse({
        'user': {
            'username': user.username,
            'role': user.get_role_display(),
            'id': user.id
        },
        'plans': plan_details
    }) 