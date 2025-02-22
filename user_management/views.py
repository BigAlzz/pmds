from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from performance.models import CustomUser
from .forms import UserCreationForm, UserUpdateForm

def is_hr_or_admin(user):
    return user.is_superuser or user.role == 'HR'

class UserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = CustomUser
    template_name = 'user_management/user_list.html'
    context_object_name = 'users'
    
    def test_func(self):
        return is_hr_or_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['role_filters'] = CustomUser.ROLE_CHOICES
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        role_filter = self.request.GET.get('role')
        if role_filter:
            queryset = queryset.filter(role=role_filter)
        return queryset

class UserCreateView(LoginRequiredMixin, UserPassesTestMixin, CreateView):
    model = CustomUser
    form_class = UserCreationForm
    template_name = 'user_management/user_form.html'
    success_url = reverse_lazy('user_management:user_list')
    
    def test_func(self):
        return is_hr_or_admin(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'User {form.instance.get_full_name()} has been created successfully.')
        return response

class UserUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = CustomUser
    form_class = UserUpdateForm
    template_name = 'user_management/user_form.html'
    success_url = reverse_lazy('user_management:user_list')
    
    def test_func(self):
        return is_hr_or_admin(self.request.user)

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'User {form.instance.get_full_name()} has been updated successfully.')
        return response

class UserDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = CustomUser
    template_name = 'user_management/user_confirm_delete.html'
    success_url = reverse_lazy('user_management:user_list')
    
    def test_func(self):
        return is_hr_or_admin(self.request.user)

    def delete(self, request, *args, **kwargs):
        user = self.get_object()
        messages.success(self.request, f'User {user.get_full_name()} has been deleted successfully.')
        return super().delete(request, *args, **kwargs)

@login_required
@user_passes_test(is_hr_or_admin)
def switch_user_view(request, user_id):
    """View to temporarily switch to another user's role for testing"""
    if request.method == 'POST':
        target_user = get_object_or_404(CustomUser, id=user_id)
        request.session['original_user_id'] = request.user.id
        request.session['impersonating_user_id'] = target_user.id
        messages.info(request, f'Now viewing as {target_user.get_full_name()} ({target_user.role})')
        return redirect('performance:dashboard')
    return redirect('user_management:user_list')

@login_required
def stop_impersonation(request):
    """View to stop impersonating another user"""
    if 'original_user_id' in request.session:
        original_user = get_object_or_404(CustomUser, id=request.session['original_user_id'])
        del request.session['original_user_id']
        del request.session['impersonating_user_id']
        messages.info(request, f'Returned to {original_user.get_full_name()}')
    return redirect('performance:dashboard')
