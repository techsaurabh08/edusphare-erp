from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from .models import StudentProfile, TeacherProfile, Attendance, Grievance, GrievanceResponse, Subject, AttendanceSession


# ── Custom UserAdmin (allows filtering by group) ─────────────────────────────
admin.site.unregister(User)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display  = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active']
    list_filter   = ['groups', 'is_staff', 'is_superuser', 'is_active']
    search_fields = ['username', 'first_name', 'last_name', 'email']
    ordering      = ['username']


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'student_class', 'roll_number']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'roll_number']
    list_filter = ['student_class']
    ordering = ['roll_number']


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'date', 'status']
    list_filter = ['status', 'date']
    search_fields = ['student__username', 'student__first_name']
    date_hierarchy = 'date'
    ordering = ['-date']


@admin.register(Grievance)
class GrievanceAdmin(admin.ModelAdmin):
    list_display = ['id', 'category', 'status', 'is_anonymous', 'student', 'created_at']
    list_filter = ['status', 'category', 'is_anonymous']
    search_fields = ['message', 'student__username']
    list_editable = ['status']
    readonly_fields = ['created_at']
    ordering = ['-created_at']


@admin.register(GrievanceResponse)
class GrievanceResponseAdmin(admin.ModelAdmin):
    list_display = ['grievance', 'user', 'created_at']
    search_fields = ['message', 'user__username']
    readonly_fields = ['created_at']
    ordering = ['-created_at']
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'department']
    search_fields = ['user__username', 'user__first_name', 'department']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'teacher', 'session_code', 'is_active', 'created_at']
    list_filter = ['is_active', 'subject']
    search_fields = ['session_code', 'teacher__username']
