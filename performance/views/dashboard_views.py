"""
Dashboard and profile views for the performance app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from ..models import (
    PerformanceAgreement,
    MidYearReview,
    FinalReview,
    ImprovementPlan,
    PersonalDevelopmentPlan
)
from ..forms import UserProfileForm


@login_required
def dashboard(request):
    """
    Display the user's dashboard with their performance-related data.
    """
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
    """
    Allow users to view and update their profile information.
    """
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