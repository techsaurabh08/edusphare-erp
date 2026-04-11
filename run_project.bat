@echo off
echo Setting up EduSphere - Smart Campus Portal...

:: 1. Create virtual environment
echo Creating virtual environment...
python -m venv venv

:: 2. Activate environment and install requirements
echo Activating environment and installing dependencies...
call venv\Scripts\activate
pip install -r requirements.txt

:: 3. Run Migrations
echo Setting up database...
python manage.py makemigrations portal
python manage.py migrate

:: 4. Create Superuser (Manual Step)
echo.
echo NOTE: You need to create a superuser manually once the server starts.
echo Press Ctrl+C later to stop and run: python manage.py createsuperuser
echo.

:: 5. Start Server
echo Starting server...
python manage.py runserver

pause
