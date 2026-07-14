from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_class = models.CharField(max_length=50)
    roll_number = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.student_class})"

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    department = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user.get_full_name()} (Teacher)"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    students = models.ManyToManyField(User, related_name='enrolled_subjects')

    def __str__(self):
        return self.name

class AttendanceSession(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='active_sessions')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='sessions')
    session_code = models.CharField(max_length=4)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def is_expired(self):
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"{self.subject.name} - {self.session_code} ({'Active' if self.is_active else 'Closed'})"

class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='attendances')
    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, null=True, blank=True, related_name='records')
    date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    subject_old = models.CharField(max_length=100, default='General') # Fallback for old records
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    class Meta:
        unique_together = ('student', 'session')

    def __str__(self):
        return f"{self.student.username} - {self.status}"

class Grievance(models.Model):
    CATEGORY_CHOICES = [
        ('Academic', 'Academic'),
        ('Facility', 'Facility'),
        ('Others', 'Others'),
    ]
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Resolved', 'Resolved'),
    ]
    student = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='grievances')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    is_anonymous = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.status} ({self.created_at.date()})"

class GrievanceResponse(models.Model):
    grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name='responses')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grievance_responses')
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response by {self.user.username} on {self.created_at.date()}"
