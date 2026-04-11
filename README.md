# EduSphere - Smart Campus Portal

EduSphere is a full-stack web application built using Python and Django for school/college project management. It includes modules for Attendance and Grievance (Complaint) tracking with role-based access control.

## Features

- **Authentication System**: Login/Logout for Admin, Teacher, and Student roles.
- **Attendance Module**: 
  - Teachers can mark daily attendance.
  - Students can view their attendance history and calculate percentage automatically.
- **Grievance Module**:
  - Students can submit complaints (Academic, Facility, Others) with an option for anonymity.
  - Admin/Teachers can view and update grievance status (Pending, In Progress, Resolved).
- **Dashboard**: Role-specific dashboards with summary statistics.
- **Modern UI**: Fully responsive design using Bootstrap 5.

## Tech Stack

- **Backend**: Django (Python)
- **Database**: PostgreSQL (Neon DB)
- **Frontend**: HTML5, CSS3, Bootstrap 5

## Setup Instructions

### 1. Prerequisites
- Python 3.10+ installed
- A Neon DB account and a PostgreSQL database URL

### 2. Clone and Setup Environment
```bash
# Navigate to project directory
cd Edusphare

# Create a virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration
1. Create a `.env` file in the root directory by copying `.env.example`:
   ```bash
   cp .env.example .env
   ```
2. Open `.env` and enter your Neon `DATABASE_URL` and a `SECRET_KEY`.

### 4. Initialize Database
```bash
python manage.py makemigrations portal
python manage.py migrate
```

### 5. Create Users & Roles
1. Create a superuser (Admin):
   ```bash
   python manage.py createsuperuser
   ```
2. Start the server:
   ```bash
   python manage.py runserver
   ```
3. Go to `http://127.0.0.1:8000/admin/` and:
   - Create two Groups: `Students` and `Teachers`.
   - Create new Users and assign them to these groups.

### 6. Run the Application
Access the portal at `http://127.0.0.1:8000/`.

## Folder Structure
- `edusphere_project/`: Main Django configuration.
- `portal/`: Application logic (models, views, urls).
- `templates/`: HTML templates for the UI.
- `requirements.txt`: Project dependencies.
