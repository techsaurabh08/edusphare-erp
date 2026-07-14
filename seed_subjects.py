import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'edusphere_project.settings')
django.setup()

from django.contrib.auth.models import User, Group
from portal.models import Subject

def seed():
    print("--- EduSphere Subject Seeder ---")
    
    # 1. Get or Create Subject
    math_sub, created = Subject.objects.get_or_create(name="Mathematics")
    python_sub, created = Subject.objects.get_or_create(name="Python Programming")
    
    # 2. Find all students
    student_group = Group.objects.get(name='Students')
    students = User.objects.filter(groups=student_group)
    
    if not students.exists():
        print("ERROR: No students found. Please create a student account first!")
        return

    # 3. Enroll students in subjects
    for student in students:
        math_sub.students.add(student)
        python_sub.students.add(student)
        print(f"Enrolled {student.username} in {math_sub.name} & {python_sub.name}")

    print("\nSUCCESS: subjects are ready for testing.")
    print("You can now login as a teacher and start a session for 'Mathematics'!")

if __name__ == "__main__":
    seed()
