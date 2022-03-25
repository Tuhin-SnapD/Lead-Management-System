python manage.py collectstatic --noinput
python manage.py migrate
gunicorn --worker-tmp-dir /dev/shm server.application 
