from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import StudentProfile, Attendance, Grievance, GrievanceResponse
from django.contrib.auth.models import User, Group
from django.utils import timezone
from django.db.models import Count

# Helper functions for role-based access
def is_student(user):
    return user.groups.filter(name='Students').exists()

def is_teacher(user):
    return user.groups.filter(name='Teachers').exists() or user.is_staff

def is_admin(user):
    return user.is_superuser

@login_required
def dashboard(request):
    if is_admin(request.user):
        return admin_dashboard(request)
    elif is_teacher(request.user):
        return teacher_dashboard(request)
    else:
        return student_dashboard(request)

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'portal/landing.html')

@login_required
def student_dashboard(request):
    student_profile = getattr(request.user, 'student_profile', None)
    attendances = Attendance.objects.filter(student=request.user).order_by('-date')
    
    total_days = attendances.count()
    present_days = attendances.filter(status='Present').count()
    percentage = (present_days / total_days * 100) if total_days > 0 else 0
    
    grievances = Grievance.objects.filter(student=request.user).order_by('-created_at')
    
    context = {
        'attendances': attendances[:5],
        'percentage': round(percentage, 2),
        'grievances': grievances[:5],
        'student_profile': student_profile
    }
    return render(request, 'portal/student_dashboard.html', context)

@login_required
def teacher_dashboard(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
        
    students = User.objects.filter(groups__name='Students')
    total_grievances = Grievance.objects.count()
    pending_grievances = Grievance.objects.filter(status='Pending').count()
    
    context = {
        'students': students,
        'total_grievances': total_grievances,
        'pending_grievances': pending_grievances,
    }
    return render(request, 'portal/teacher_dashboard.html', context)

@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('dashboard')
        
    total_students = User.objects.filter(groups__name='Students').count()
    total_teachers = User.objects.filter(groups__name='Teachers').count()
    total_grievances = Grievance.objects.count()
    grievance_stats = Grievance.objects.values('status').annotate(count=Count('status'))
    
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_grievances': total_grievances,
        'grievance_stats': grievance_stats,
    }
    return render(request, 'portal/admin_dashboard.html', context)

@login_required
def mark_attendance(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
        
    if request.method == 'POST':
        date = request.POST.get('date', timezone.now().date())
        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                student_id = key.split('_')[1]
                student = get_object_or_404(User, id=student_id)
                Attendance.objects.update_or_create(
                    student=student, 
                    date=date, 
                    defaults={'status': value}
                )
        messages.success(request, "Attendance marked successfully!")
        return redirect('dashboard')
        
    students = User.objects.filter(groups__name='Students')
    return render(request, 'portal/mark_attendance.html', {'students': students, 'today': timezone.now().date()})

@login_required
def submit_grievance(request):
    if request.method == 'POST':
        category = request.POST.get('category')
        message_text = request.POST.get('message')
        is_anonymous = request.POST.get('is_anonymous') == 'on'
        
        grievance = Grievance.objects.create(
            student=request.user,
            category=category,
            message=message_text,
            is_anonymous=is_anonymous
        )
        messages.success(request, "Grievance submitted successfully!")
        return redirect('dashboard')
        
    return render(request, 'portal/submit_grievance.html')

@login_required
def view_grievances(request):
    if is_teacher(request.user) or is_admin(request.user):
        grievances = Grievance.objects.all().order_by('-created_at')
    else:
        grievances = Grievance.objects.filter(student=request.user).order_by('-created_at')
    return render(request, 'portal/view_grievances.html', {'grievances': grievances})

@login_required
def grievance_detail(request, pk):
    grievance = get_object_or_404(Grievance, pk=pk)
    
    # Permission context
    is_staff = is_teacher(request.user) or is_admin(request.user)
    if not is_staff and grievance.student != request.user:
        messages.error(request, "You do not have permission to view this grievance.")
        return redirect('dashboard')
        
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_response':
            message_text = request.POST.get('message')
            if message_text:
                GrievanceResponse.objects.create(
                    grievance=grievance,
                    user=request.user,
                    message=message_text
                )
                messages.success(request, "Response added successfully.")
                
        elif action == 'update_status' and is_staff:
            status = request.POST.get('status')
            if status in dict(Grievance.STATUS_CHOICES):
                grievance.status = status
                grievance.save()
                messages.success(request, "Grievance status updated!")
                
        return redirect('grievance_detail', pk=grievance.pk)
        
    responses = grievance.responses.all().order_by('created_at')
    
    return render(request, 'portal/grievance_detail.html', {
        'grievance': grievance,
        'responses': responses,
        'is_staff': is_staff
    })
def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        student_class = request.POST.get('student_class')
        roll_number = request.POST.get('roll_number')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('/login/?mode=signup')
            
        if StudentProfile.objects.filter(roll_number=roll_number).exists():
            messages.error(request, "Roll number already registered")
            return redirect('/login/?mode=signup')
            
        # Create User
        first_name = full_name.split(' ')[0] if ' ' in full_name else full_name
        last_name = ' '.join(full_name.split(' ')[1:]) if ' ' in full_name else ''
        
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Ensure Group exists and assign
        group, created = Group.objects.get_or_create(name='Students')
        user.groups.add(group)
        
        # Create Student Profile
        StudentProfile.objects.create(
            user=user,
            student_class=student_class,
            roll_number=roll_number
        )
        
        login(request, user)
        messages.success(request, f"Welcome to EduSphere, {user.first_name}!")
        return redirect('dashboard')
        
    return render(request, 'portal/auth.html')
