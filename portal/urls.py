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
    path('attendance/', views.view_attendance, name='view_attendance'),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('session/start/', views.start_attendance_session, name='start_attendance_session'),
    path('session/close/<int:session_id>/', views.close_attendance_session, name='close_attendance_session'),
    path('session/checkin/', views.student_checkin, name='student_checkin'),
    path('api/dashboard-stats/', views.get_dashboard_stats, name='get_dashboard_stats'),

    
    # Grievances
    path('grievance/submit/', views.submit_grievance, name='submit_grievance'),
    path('grievances/', views.view_grievances, name='view_grievances'),
    path('grievance/<int:pk>/', views.grievance_detail, name='grievance_detail'),
    path('profile/', views.profile_view, name='profile'),
    path('get-latest-code/', views.get_latest_code, name='get_latest_code'),
    path('create-session/', views.create_session, name='create_session'),
    path('get-code/', views.get_active_code, name='get_code'),
    path('export/attendance/', views.export_attendance_csv, name='export_attendance_csv'),
]
