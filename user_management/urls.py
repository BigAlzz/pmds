from django.urls import path
from . import views

app_name = 'user_management'

urlpatterns = [
    path('users/', views.UserListView.as_view(), name='user_list'),
    path('users/create/', views.UserCreateView.as_view(), name='user_create'),
    path('users/<int:pk>/update/', views.UserUpdateView.as_view(), name='user_update'),
    path('users/<int:pk>/delete/', views.UserDeleteView.as_view(), name='user_delete'),
    path('users/<int:user_id>/switch/', views.switch_user_view, name='switch_user'),
    path('stop-impersonation/', views.stop_impersonation, name='stop_impersonation'),
] 