@echo off
echo Starting Lead Management System...
echo.

echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Starting Django development server...
echo Server will be available at: http://127.0.0.1:8000
echo Admin login: http://127.0.0.1:8000/admin
echo Username: admin
echo Password: admin
echo.
echo Press Ctrl+C to stop the server
echo ========================================
python manage.py runserver 