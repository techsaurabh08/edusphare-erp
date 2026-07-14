import csv
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Count, Q
from .models import StudentProfile, TeacherProfile, Attendance, Grievance, GrievanceResponse, Subject, AttendanceSession
from django.contrib.auth.models import User, Group
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Helper functions for role-based access
def is_student(user):
    return hasattr(user, 'student_profile')

def is_teacher(user):
    return hasattr(user, 'teacher_profile') or user.is_staff

def is_admin(user):
    return user.is_superuser

@login_required
def dashboard(request):
    if is_admin(request.user):
        return redirect('/admin/')
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
    attendances = Attendance.objects.filter(student=request.user).order_by('-created_at')
    
    total_count = attendances.count()
    present_count = attendances.filter(status='Present').count()
    overall_pct = (present_count / total_count * 100) if total_count > 0 else 0
    
    # 1. Prediction & Milestone Tracker
    def calculate_milestone(current_p, total, target):
        if (current_p / total * 100) >= target if total > 0 else False:
            return 0
        # Formula: (p + x) / (t + x) = target/100  => p + x = (target/100)*t + (target/100)*x
        # x(1 - target/100) = (target/100)*t - p
        # x = ((target/100)*t - p) / (1 - target/100)
        target_f = target / 100.0
        needed = (target_f * total - current_p) / (1 - target_f)
        return int(needed + 0.99) if needed > 0 else 0

    # 2. Subject-wise Precision Intelligence
    enrolled_subjects = request.user.enrolled_subjects.all()
    subject_stats = []
    for sub in enrolled_subjects:
        sub_attendances = attendances.filter(Q(session__subject=sub) | Q(subject_old=sub.name))
        s_total = sub_attendances.count()
        s_present = sub_attendances.filter(status='Present').count()
        s_pct = round((s_present / s_total * 100), 1) if s_total > 0 else 0
        
        # What-if Simulation
        pct_if_attend = round(((s_present + 1) / (s_total + 1) * 100), 1) if s_total >= 0 else 100
        pct_if_miss = round((s_present / (s_total + 1) * 100), 1) if s_total >= 0 else 0
        
        # Risk Classification
        risk_level = 'safe' if s_pct > 85 else ('caution' if s_pct >= 75 else 'danger')
        
        subject_stats.append({
            'name': sub.name,
            'pct': s_pct,
            'total': s_total,
            'present': s_present,
            'status': risk_level,
            'if_attend': pct_if_attend,
            'if_miss': pct_if_miss,
            'needed_75': calculate_milestone(s_present, s_total, 75),
            'needed_80': calculate_milestone(s_present, s_total, 80),
            'needed_90': calculate_milestone(s_present, s_total, 90),
        })

    # 3. Trend & Insights Engine (Calculated before slicing)
    recent_sessions = list(attendances[:5])
    recent_present_count = sum(1 for s in recent_sessions if s.status == 'Present')
    trend = "Stable"
    if len(recent_sessions) >= 3:
        if recent_present_count >= 4: trend = "Improving"
        elif recent_present_count <= 2: trend = "Declining"

    # 4. Streak Engine (Session-based, ignoring calendar gaps)
    streak = 0
    subject_streaks = {}
    for att in attendances:
        if att.status == 'Present':
            streak += 1
        else:
            break

    # 5. Smart Health Score (60/20/20 Weighted)
    # Weight A (60%): Attendance %
    # Weight B (20%): Streak (capped at 10 days for 100% contribution)
    # Weight C (20%): Trend (Improving=100, Stable=70, Declining=30)
    streak_bonus = min(streak * 10, 100)
    trend_score = 100 if trend == "Improving" else (70 if trend == "Stable" else 30)
    health_score = int((overall_pct * 0.6) + (streak_bonus * 0.2) + (trend_score * 0.2))

    # 6. Weekly Presence Map (Enhanced with metadata)
    weekly_map = []
    for i in range(6, -1, -1):
        target_date = timezone.now().date() - timezone.timedelta(days=i)
        day_att = attendances.filter(date=target_date).first()
        status = 'empty'
        sub_name = 'No Sessions'
        if day_att:
            status = 'present' if day_att.status == 'Present' else 'absent'
            sub_name = day_att.session.subject.name if day_att.session else day_att.subject_old
        
        weekly_map.append({
            'day': target_date.strftime('%a'),
            'date': target_date.strftime('%d %b'),
            'status': status,
            'subject': sub_name,
            'is_today': i == 0
        })
        
    # Status classification for UI
    status = 'danger'
    status_label = 'Critically Low'
    if overall_pct >= 75:
        status = 'success'
        status_label = 'Safe for Exams'
    elif overall_pct >= 65:
        status = 'warning'
        status_label = 'Low (Warning)'

    # Overall milestone
    classes_to_75 = calculate_milestone(present_count, total_count, 75)

    context = {
        'student_profile': student_profile,
        'overall_pct': round(overall_pct, 1),
        'attendance_percentage': round(overall_pct, 1), # Compatibility with template
        'present_count': present_count,
        'absent_count': total_count - present_count,
        'total_count': total_count,
        'status': status,
        'status_label': status_label,
        'classes_to_75': classes_to_75,
        'health_score': health_score,
        'trend': trend,
        'streak': streak,
        'subject_stats': subject_stats,
        'weekly_map': weekly_map,
        'pending_count': Grievance.objects.filter(student=request.user, status__in=['Pending', 'In Progress']).count(),
        'recent_activity': attendances[:5],
        'active_session': AttendanceSession.objects.filter(is_active=True, subject__students=request.user).exclude(records__student=request.user).first()
    }
    return render(request, 'portal/student_dashboard.html', context)


@login_required
def view_attendance(request):
    # Only students should see their history this way
    attendances = Attendance.objects.filter(student=request.user).order_by('-created_at')
    
    total_count = attendances.count()
    present_count = attendances.filter(status='Present').count()
    absent_count = total_count - present_count
    percentage = (present_count / total_count * 100) if total_count > 0 else 0
    
    # Simple analytics for the page header
    status = 'danger'
    status_label = 'Critically Low'
    if percentage >= 75:
        status = 'success'
        status_label = 'Safe for Exams'
    elif percentage >= 65:
        status = 'warning'
        status_label = 'Low (Warning)'

    context = {
        'all_attendances': attendances,
        'attendance_percentage': round(percentage, 1),
        'present_count': present_count,
        'absent_count': absent_count,
        'total_count': total_count,
        'status': status,
        'status_label': status_label,
    }
    return render(request, 'portal/attendance.html', context)



@login_required
@login_required
def teacher_dashboard(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
        
    # Standard querysets
    students = User.objects.filter(groups__name='Students')
    all_attendance = Attendance.objects.all()
    
    # 1. Quick Stats
    total_students = students.count()
    # Total unique sessions
    total_classes = AttendanceSession.objects.count()
    
    # Global Avg Attendance
    total_records = all_attendance.count()
    avg_pct = 0
    if total_records > 0:
        present_count = all_attendance.filter(status='Present').count()
        avg_pct = round((present_count / total_records * 100), 1)
        
    pending_grievances_count = Grievance.objects.filter(status='Pending').count()

    # 2. Performance Insights (Students with < 75% attendance) optimized
    students_with_stats = students.annotate(
        total_att=Count('attendances'),
        present_att=Count('attendances', filter=Q(attendances__status='Present'))
    )
    
    student_performance = []
    for student in students_with_stats[:20]:
        if student.total_att > 0:
            s_pct = (student.present_att / student.total_att * 100)
            if s_pct < 75:
                student_performance.append({
                    'name': student.get_full_name() or student.username,
                    'pct': round(s_pct, 1),
                    'low': True
                })
    
    # 3. Subject Breakdown
    subjects = AttendanceSession.objects.values('subject__name').annotate(
        total=Count('records'),
        present=Count('records', filter=Q(records__status='Present'))
    )
    subject_stats = []
    for sub in subjects:
        pct = (sub['present'] / sub['total'] * 100) if sub['total'] > 0 else 0
        subject_stats.append({
            'name': sub['subject__name'],
            'pct': round(pct, 1)
        })
        
    # 4. Trend Data (Last 7 Days with data)
    trend_dates = Attendance.objects.values('date').distinct().order_by('-date')[:7]
    chart_labels = []
    chart_data = []
    for d in reversed(trend_dates):
        d_total = Attendance.objects.filter(date=d['date']).count()
        d_present = Attendance.objects.filter(date=d['date'], status='Present').count()
        d_pct = (d_present / d_total * 100) if d_total > 0 else 0
        chart_labels.append(d['date'].strftime('%d %b'))
        chart_data.append(round(d_pct, 1))

    # 5. Recent Grievances
    recent_grievances = Grievance.objects.all().order_by('-created_at')[:5]
    
    context = {
        'total_students': total_students,
        'total_classes': total_classes,
        'avg_attendance': avg_pct,
        'pending_grievances': pending_grievances_count,
        'student_performance': student_performance, # Low attendance triggers
        'subject_stats': subject_stats,
        'recent_grievances': recent_grievances,
        'chart_labels': chart_labels,
        'chart_data': chart_data,
        'students': students[:10], # Recent registry
        'active_session': AttendanceSession.objects.filter(teacher=request.user, is_active=True).first(),
        'all_subjects': Subject.objects.all()
    }
    return render(request, 'portal/teacher_dashboard.html', context)


@login_required
def admin_dashboard(request):
    if not is_admin(request.user):
        return redirect('dashboard')
    return redirect('/admin/')

@login_required
def mark_attendance(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
        
    students = User.objects.filter(groups__name='Students')
    existing_subjects = Attendance.objects.values_list('subject_old', flat=True).distinct()
    
    if request.method == 'POST':
        date = request.POST.get('date', timezone.now().date())
        subject = request.POST.get('subject', 'General')
        
        for key, value in request.POST.items():
            if key.startswith('attendance_'):
                student_id = key.split('_')[1]
                student = get_object_or_404(User, id=student_id)
                Attendance.objects.update_or_create(
                    student=student, 
                    date=date, 
                    subject_old=subject,
                    defaults={'status': value}
                )
        messages.success(request, f"Attendance for {subject} marked successfully!")
        return redirect('dashboard')
        
    context = {
        'students': students, 
        'today': timezone.now().date(),
        'existing_subjects': existing_subjects
    }
    return render(request, 'portal/mark_attendance.html', context)


@login_required
def start_attendance_session(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, id=subject_id)
        
        # Ensure no other active session for this teacher + subject
        AttendanceSession.objects.filter(teacher=request.user, subject=subject, is_active=True).update(is_active=False)
        
        # Generate 4-digit code
        import random
        code = str(random.randint(1000, 9999))
        
        expires_at = timezone.now() + timezone.timedelta(minutes=10)
        
        AttendanceSession.objects.create(
            teacher=request.user,
            subject=subject,
            session_code=code,
            is_active=True,
            expires_at=expires_at
        )

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "attendance",
            {
                "type": "send_code",
                "code": code
            }
        )

        messages.success(request, f"Attendance session for {subject.name} started! Code: {code}")
        
    return redirect('dashboard')

@login_required
def close_attendance_session(request, session_id):
    if not is_teacher(request.user):
        return redirect('dashboard')
    
    session = get_object_or_404(AttendanceSession, id=session_id, teacher=request.user)
    session.is_active = False
    session.save()
    
    # Auto-Finalize: Mark all enrolled students who didn't check-in as "Absent"
    enrolled_students = session.subject.students.all()
    checked_in_student_ids = session.records.values_list('student_id', flat=True)
    
    absent_records = []
    for student in enrolled_students:
        if student.id not in checked_in_student_ids:
            absent_records.append(Attendance(
                student=student,
                session=session,
                status='Absent'
            ))
    
    if absent_records:
        Attendance.objects.bulk_create(absent_records)
        
    messages.info(request, f"Session for {session.subject.name} closed and attendance finalized.")
    return redirect('dashboard')

@login_required
def student_checkin(request):
    if not is_student(request.user):
        return redirect('dashboard')
        
    if request.method == 'POST':
        code = request.POST.get('session_code')
        
        # Find active session with this code
        session = AttendanceSession.objects.filter(session_code=code, is_active=True).first()
        
        if not session:
            messages.error(request, "Invalid or inactive session code.")
        elif session.is_expired():
            session.is_active = False
            session.save()
            messages.error(request, "This session has expired.")
        elif not session.subject.students.filter(id=request.user.id).exists():
            messages.error(request, "You are not enrolled in this subject.")
        elif Attendance.objects.filter(student=request.user, session=session).exists():
            messages.warning(request, "You have already checked in for this session.")
        else:
            Attendance.objects.create(
                student=request.user,
                session=session,
                status='Present'
            )
            messages.success(request, f"Successfully checked into {session.subject.name}!")
            
    return redirect('dashboard')

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
        user_role = request.POST.get('user_role', 'student')  # New field
        
        student_class = request.POST.get('student_class')
        roll_number = request.POST.get('roll_number')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists")
            return redirect('/login/?mode=signup')
            
        if user_role == 'student' and StudentProfile.objects.filter(roll_number=roll_number).exists():
            messages.error(request, "Roll number already registered")
            return redirect('/login/?mode=signup')
            
        # Create User
        parts = full_name.split(' ')
        first_name = parts[0]
        last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''
        
        user = User.objects.create_user(
            username=username, 
            email=email, 
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Role-based logic
        if user_role == 'teacher':
            group, _ = Group.objects.get_or_create(name='Teachers')
            user.groups.add(group)
            TeacherProfile.objects.create(user=user)
        else:
            group, _ = Group.objects.get_or_create(name='Students')
            user.groups.add(group)
            StudentProfile.objects.create(
                user=user,
                student_class=student_class,
                roll_number=roll_number
            )
        
        login(request, user)
        messages.success(request, f"Welcome to EduSphere, {user.first_name}!")
        return redirect('dashboard')

        
    return render(request, 'portal/signup.html')


@login_required
def profile_view(request):
    user = request.user
    student_profile = getattr(user, 'student_profile', None)
    teacher_profile = getattr(user, 'teacher_profile', None)
    
    # Enrolled subjects
    enrolled_subjects = user.enrolled_subjects.all()
    
    # Stats
    total_attendances = user.attendances.count()
    present_attendances = user.attendances.filter(status='Present').count()
    attendance_pct = round((present_attendances / total_attendances * 100), 1) if total_attendances > 0 else 0
    
    grievances_count = user.grievances.count() if is_student(user) else Grievance.objects.count()
    
    context = {
        'profile_user': user,
        'student_profile': student_profile,
        'teacher_profile': teacher_profile,
        'enrolled_subjects': enrolled_subjects,
        'attendance_pct': attendance_pct,
        'grievances_count': grievances_count,
        'is_student': is_student(user),
        'is_teacher': is_teacher(user),
    }
    
    return render(request, 'portal/profile.html', context)
@login_required
def get_dashboard_stats(request):
    """AJAX endpoint for real-time dashboard updates."""
    if not is_student(request.user):
        return JsonResponse({'error': 'Unauthorized'}, status=403)
        
    attendances = Attendance.objects.filter(student=request.user).order_by('-created_at')
    total_count = attendances.count()
    present_count = attendances.filter(status='Present').count()
    overall_pct = (present_count / total_count * 100) if total_count > 0 else 0
    
    # Calculate Streak
    streak = 0
    for att in attendances:
        if att.status == 'Present': streak += 1
        else: break
        
    # Trend Analysis
    recent = list(attendances[:5])
    recent_present = sum(1 for att in recent if att.status == 'Present')
    trend = "Stable"
    if len(recent) >= 3:
        if recent_present >= 4: trend = "Improving"
        elif recent_present <= 2: trend = "Declining"

    # Health Score
    streak_bonus = min(streak * 10, 100)
    trend_score = 100 if trend == "Improving" else (70 if trend == "Stable" else 30)
    health_score = int((overall_pct * 0.6) + (streak_bonus * 0.2) + (trend_score * 0.2))

    # Subject Level
    subject_stats = []
    for sub in request.user.enrolled_subjects.all():
        s_att = attendances.filter(Q(session__subject=sub) | Q(subject_old=sub.name))
        s_total = s_att.count()
        s_present = s_att.filter(status='Present').count()
        s_pct = round((s_present / s_total * 100), 1) if s_total > 0 else 0
        subject_stats.append({
            'name': sub.name,
            'pct': s_pct,
            'status': 'safe' if s_pct > 85 else ('caution' if s_pct >= 75 else 'danger')
        })

    return JsonResponse({
        'overall_pct': round(overall_pct, 1),
        'health_score': health_score,
        'streak': streak,
        'trend': trend,
        'subject_stats': subject_stats
    })

def get_latest_code(request):
    session = AttendanceSession.objects.filter(is_active=True).order_by('created_at').last()
    return JsonResponse({
        'code': session.session_code if session else None
    })

# --- Added alternative alias endpoints per your request ---

def create_session(request):
    code = str(random.randint(1000, 9999))
    
    if request.user.is_authenticated:
        # Fallback to a default subject for the simple GET request <a> tag version
        subject = Subject.objects.first()
        
        if subject:
            AttendanceSession.objects.filter(
                teacher=request.user,
                subject=subject
            ).update(is_active=False)

            expires_at = timezone.now() + timezone.timedelta(minutes=10)
            AttendanceSession.objects.create(
                teacher=request.user, 
                subject=subject, 
                session_code=code,
                expires_at=expires_at
            )
    return redirect('teacher_dashboard')

from datetime import timedelta

def get_active_code(request):
    session = AttendanceSession.objects.filter(is_active=True).order_by('created_at').last()
    
    if session:
        # expiry logic
        if timezone.now() - session.created_at > timedelta(minutes=10):
            session.is_active = False
            session.save()
            session = None
            
    return JsonResponse({
        'code': session.session_code if session else None
    })

@login_required
def export_attendance_csv(request):
    if not is_teacher(request.user):
        return redirect('dashboard')
        
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename="attendance_report.csv"'},
    )

    writer = csv.writer(response)
    writer.writerow(['Date', 'Student Name', 'Roll Number', 'Subject', 'Status'])

    attendances = Attendance.objects.all().select_related(
        'student', 'student__student_profile', 'session', 'session__subject'
    ).order_by('-date')
    
    for att in attendances:
        try:
            roll_num_str = att.student.student_profile.roll_number
        except Exception:
            roll_num_str = "N/A"
            
        subject_name = att.session.subject.name if att.session and att.session.subject else att.subject_old
        
        writer.writerow([
            att.date.strftime('%Y-%m-%d'),
            att.student.get_full_name() or att.student.username,
            roll_num_str,
            subject_name,
            att.status
        ])

    return response
