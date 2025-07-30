# Lead Management System

A modern, scalable Django-based lead management system designed for sales teams and organizations to efficiently manage customer leads, agents, and sales processes.

## 🚀 Features

### Core Functionality
- **Lead Management**: Create, update, and track leads with comprehensive information
- **Agent Management**: Manage sales agents with performance tracking
- **Category System**: Organize leads by status (New, Contacted, Converted, Unconverted)
- **Role-Based Access**: Separate permissions for organizers and agents
- **Email Notifications**: Automated email notifications for lead assignments and updates

### Advanced Features
- **Search & Filtering**: Advanced search and filtering capabilities for leads
- **Performance Analytics**: Agent performance tracking and organization statistics
- **Dashboard**: Comprehensive dashboard with key metrics and recent activity
- **Responsive Design**: Modern UI built with Tailwind CSS
- **API Ready**: REST API support for future integrations

### Security & Performance
- **Environment Configuration**: Secure environment variable management
- **Database Optimization**: Efficient queries with proper indexing
- **Caching Support**: Redis-based caching for improved performance
- **Error Handling**: Comprehensive error handling and logging
- **Production Ready**: Security headers and production optimizations

## 🛠️ Technology Stack

- **Backend**: Django 4.2.7
- **Database**: PostgreSQL (production), SQLite (development)
- **Frontend**: Tailwind CSS, Crispy Forms
- **Caching**: Redis
- **Email**: Django Email Backend (configurable)
- **Deployment**: Gunicorn, WhiteNoise
- **Monitoring**: Sentry (optional)

## 📋 Prerequisites

- Python 3.8+
- PostgreSQL (for production)
- Redis (optional, for caching)
- Git

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Lead-Management-System
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Copy the example environment file and configure it:

```bash
cp env.example .env
```

Edit `.env` with your configuration:

```env
ENVIRONMENT=development
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Database Setup

For development (SQLite):
```bash
python manage.py migrate
```

For production (PostgreSQL):
```bash
# Update .env with your database credentials
python manage.py migrate
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run the Development Server

```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## 🏗️ Project Structure

```
Lead-Management-System/
├── agents/                 # Agent management app
│   ├── views.py           # Agent views
│   ├── forms.py           # Agent forms
│   ├── mixins.py          # Custom mixins
│   └── templates/         # Agent templates
├── leads/                  # Lead management app
│   ├── models.py          # Data models
│   ├── views.py           # Lead views
│   ├── forms.py           # Lead forms
│   ├── services.py        # Business logic services
│   └── templates/         # Lead templates
├── server/                 # Django project settings
│   ├── settings.py        # Main settings
│   ├── urls.py            # URL configuration
│   └── wsgi.py            # WSGI configuration
├── static/                 # Static files
├── templates/              # Base templates
├── media/                  # User uploaded files
├── logs/                   # Application logs
├── requirements.txt        # Python dependencies
├── env.example            # Environment variables example
└── README.md              # This file
```

## 🔧 Configuration

### Environment Variables

Key environment variables to configure:

- `ENVIRONMENT`: Set to 'production' or 'development'
- `SECRET_KEY`: Django secret key (generate a secure one)
- `DEBUG`: Set to False in production
- `ALLOWED_HOSTS`: Comma-separated list of allowed hosts
- `DATABASE_URL`: Database connection string
- `EMAIL_*`: Email configuration
- `REDIS_URL`: Redis connection string (optional)

### Database Configuration

The system supports both SQLite (development) and PostgreSQL (production):

```python
# Development (SQLite)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Production (PostgreSQL)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-django factory-boy

# Run tests
pytest

# Run with coverage
pytest --cov=leads --cov=agents
```

## 📊 Performance Optimization

### Database Optimization

- **Indexes**: Proper database indexes on frequently queried fields
- **Select Related**: Optimized queries to reduce database hits
- **Connection Pooling**: Database connection pooling for production

### Caching

Enable Redis caching for improved performance:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}
```

### Static Files

Static files are optimized for production:

```bash
python manage.py collectstatic
```

## 🔒 Security Features

- **CSRF Protection**: Built-in CSRF protection
- **XSS Protection**: Security headers for XSS prevention
- **HTTPS Redirect**: Automatic HTTPS redirect in production
- **Secure Cookies**: Secure cookie settings
- **Input Validation**: Comprehensive form validation
- **SQL Injection Protection**: Django ORM protection

## 🚀 Deployment

### Production Checklist

1. **Environment Variables**: Set all production environment variables
2. **Database**: Configure PostgreSQL database
3. **Static Files**: Run `python manage.py collectstatic`
4. **Migrations**: Run `python manage.py migrate`
5. **Security**: Set `DEBUG=False` and configure `SECRET_KEY`
6. **HTTPS**: Configure SSL certificates
7. **Monitoring**: Set up Sentry for error tracking

### Docker Deployment

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]
```

### Heroku Deployment

1. Create a Heroku app
2. Add PostgreSQL addon
3. Configure environment variables
4. Deploy using Git

```bash
heroku create your-app-name
heroku addons:create heroku-postgresql
heroku config:set ENVIRONMENT=production
git push heroku main
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

The project uses:
- **Black**: Code formatting
- **Flake8**: Linting
- **isort**: Import sorting

Run code quality checks:

```bash
black .
flake8 .
isort .
```

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. Check the [Issues](https://github.com/your-repo/issues) page
2. Create a new issue with detailed information
3. Contact the development team

## 🔄 Changelog

### Version 2.0.0 (Current)
- Complete refactoring for performance and scalability
- Added service layer for business logic
- Improved security and error handling
- Enhanced UI with modern design
- Added comprehensive testing
- Production-ready configuration

### Version 1.0.0
- Initial release with basic lead management features

## 🙏 Acknowledgments

- Django community for the excellent framework
- Tailwind CSS for the beautiful UI components
- All contributors who helped improve this project