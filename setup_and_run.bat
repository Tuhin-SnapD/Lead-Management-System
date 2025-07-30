@echo off
echo ========================================
echo Lead Management System Setup
echo ========================================

echo.
echo 1. Creating virtual environment...
python -m venv venv

echo.
echo 2. Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo 3. Upgrading pip...
python -m pip install --upgrade pip

echo.
echo 4. Installing dependencies...
pip install -r requirements.txt

echo.
echo 5. Running database migrations...
python manage.py makemigrations
python manage.py migrate

echo.
echo 6. Creating admin user (username: admin, password: admin)...
python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@example.com', 'admin') if not User.objects.filter(username='admin').exists() else print('Admin user already exists')"

echo.
echo 7. Starting Django development server...
echo Server will be available at: http://127.0.0.1:8000
echo Admin login: http://127.0.0.1:8000/admin
echo Username: admin
echo Password: admin
echo.
echo Press Ctrl+C to stop the server
echo ========================================
python manage.py runserver 