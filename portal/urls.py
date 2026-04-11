from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('login/', auth_views.LoginView.as_view(template_name='portal/auth.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('signup/', views.signup, name='signup'),
    
    # Attendance
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    
    # Grievances
    path('grievance/submit/', views.submit_grievance, name='submit_grievance'),
    path('grievances/', views.view_grievances, name='view_grievances'),
    path('grievance/<int:pk>/', views.grievance_detail, name='grievance_detail'),
]
