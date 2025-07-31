# 🚀 LeadFlow - Modern Lead Management System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Django](https://img.shields.io/badge/Django-4.2.7-green.svg)](https://djangoproject.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)](https://github.com/yourusername/Lead-Management-System)

A modern, feature-rich Django-based lead management system designed for sales teams to efficiently manage customer leads, agents, and sales processes with a beautiful, responsive interface.

## ✨ Features

### 🎯 Core Functionality
- **Lead Management**: Create, update, and track leads with comprehensive information
- **Agent Management**: Manage sales agents with performance tracking and assignments
- **Category System**: Organize leads by status (New, Contacted, Converted, Unconverted)
- **Role-Based Access**: Separate permissions for organizers and agents
- **Advanced Search**: Powerful search and filtering capabilities
- **Real-time Dashboard**: Live metrics and performance indicators

### 🎨 User Experience
- **Modern UI**: Beautiful, responsive design with Tailwind CSS
- **Mobile Responsive**: Perfect experience on all devices
- **Interactive Elements**: Hover effects, animations, and smooth transitions
- **Color-coded Categories**: Visual organization with custom colors
- **Professional Typography**: Inter font family for better readability
- **Icon Integration**: Font Awesome icons throughout the interface

### 🔧 Technical Features
- **Django 4.2.7**: Latest stable Django version
- **PostgreSQL Ready**: Production-ready database support
- **Custom User Model**: Extended user model with role-based permissions
- **Signal Handlers**: Automated profile creation and data management
- **Form Validation**: Comprehensive client and server-side validation
- **Security**: CSRF protection, SQL injection prevention, XSS protection

## 🛠️ Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| **Backend** | Django | 4.2.7 |
| **Database** | PostgreSQL/SQLite | Latest |
| **Frontend** | Tailwind CSS | Latest |
| **Forms** | Django Crispy Forms | 2.1 |
| **Icons** | Font Awesome | Latest |
| **Deployment** | Gunicorn + WhiteNoise | Latest |

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- pip (Python package installer)
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/Lead-Management-System.git
cd Lead-Management-System
```

### 2. Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Configuration
```bash
# Copy environment template
cp env.example .env

# Edit .env with your configuration
# Key variables to set:
# - DEBUG=True (for development)
# - SECRET_KEY=your-secret-key-here
# - ALLOWED_HOSTS=localhost,127.0.0.1
```

### 5. Database Setup
```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### 6. Seed Demo Data (Optional)
For a realistic demonstration with sample data:

```bash
# Option 1: Using the management command
python manage.py setup_demo_data --clear --leads 150

# Option 2: Using the simple script
python seed_data.py
```

This creates:
- 3 Organizer accounts
- 15 Agent accounts  
- 10 Categories per organizer
- 150+ realistic leads with varied data

### 7. Run the Development Server
```bash
# Using the startup script
python start.py

# Or using Django's runserver
python manage.py runserver
```

Visit `http://127.0.0.1:8000` to access the application.

## 👤 Demo Credentials

After seeding demo data, you can login with these credentials (username = password):

### 🏢 Organizers
| Username | Password | Name |
|----------|----------|------|
| `admin` | `admin` | Sarah Johnson |
| `manager` | `manager` | Michael Chen |
| `director` | `director` | Emily Rodriguez |

### 👥 Agents
| Username | Password | Name |
|----------|----------|------|
| `john` | `john` | John Smith |
| `jane` | `jane` | Jane Doe |
| `mike` | `mike` | Mike Johnson |
| `sarah` | `sarah` | Sarah Williams |
| `david` | `david` | David Brown |

*And 10 more agents...*

## 🏗️ Project Structure

```
Lead-Management-System/
├── 📁 agents/                 # Agent management app
│   ├── 📁 migrations/         # Database migrations
│   ├── 📁 templates/          # Agent-specific templates
│   ├── models.py             # Agent data models
│   ├── views.py              # Agent views and logic
│   └── urls.py               # Agent URL routing
├── 📁 leads/                  # Lead management app
│   ├── 📁 management/         # Custom management commands
│   │   └── 📁 commands/       # Data seeding commands
│   ├── 📁 migrations/         # Database migrations
│   ├── 📁 templates/          # Lead-specific templates
│   ├── 📁 tests/              # Test files
│   ├── models.py             # Lead data models
│   ├── views.py              # Lead views and logic
│   ├── services.py           # Business logic services
│   └── urls.py               # Lead URL routing
├── 📁 server/                 # Django project settings
│   ├── settings.py           # Django settings
│   ├── urls.py               # Main URL routing
│   └── wsgi.py               # WSGI configuration
├── 📁 static/                 # Static files (CSS, JS, images)
├── 📁 templates/              # Base templates
├── 📄 requirements.txt        # Python dependencies
├── 📄 seed_data.py           # Data seeding script
├── 📄 start.py               # Startup script
└── 📄 manage.py              # Django management script
```

## 🔧 Configuration

### Environment Variables

Key environment variables in `.env`:

```env
# Django Settings
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (for production)
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# Email (for production)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration

- **Development**: SQLite (default, no configuration needed)
- **Production**: PostgreSQL (configure in settings.py)

## 📊 Data Seeding Options

The system includes comprehensive data seeding capabilities:

### Management Command Options

```bash
# Basic seeding (100 leads)
python manage.py setup_demo_data

# Clear existing data and seed 200 leads
python manage.py setup_demo_data --clear --leads 200

# Just clear existing data
python manage.py setup_demo_data --clear
```

### Custom Data

You can modify the seeding script in `leads/management/commands/setup_demo_data.py` to:
- Add more realistic company names
- Customize lead sources
- Modify agent assignments
- Adjust category distributions

## 🧪 Testing

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=leads --cov=agents

# Run specific test file
pytest leads/tests/test_models.py
```

## 🚀 Deployment

### Production Checklist

1. **Environment Setup**
   - Set `DEBUG=False`
   - Configure production `SECRET_KEY`
   - Set up environment variables

2. **Database Setup**
   - Configure PostgreSQL database
   - Run migrations: `python manage.py migrate`
   - Create superuser: `python manage.py createsuperuser`

3. **Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

4. **Security**
   - Set up SSL certificates
   - Configure HTTPS
   - Set secure headers

5. **Server Configuration**
   - Configure Gunicorn
   - Set up reverse proxy (Nginx)
   - Configure process manager (systemd)

### Docker Deployment

```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "server.wsgi:application"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://postgres:password@db:5432/leadflow
    depends_on:
      - db
    volumes:
      - .:/app
      - static_volume:/app/staticfiles

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=leadflow
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  static_volume:
```

## 🎯 Key Features Explained

### Lead Management
- **Comprehensive Lead Data**: Store personal info, contact details, business info
- **Agent Assignment**: Assign leads to specific agents for follow-up
- **Category Organization**: Categorize leads by status or type
- **Contact Tracking**: Track when leads were last contacted
- **Source Attribution**: Track where leads originated from

### Agent Management
- **Role-Based Access**: Agents can only see their assigned leads
- **Performance Tracking**: Monitor agent activity and assignments
- **Organization Isolation**: Agents work within their organization's scope

### Category System
- **Custom Categories**: Create organization-specific categories
- **Color Coding**: Visual organization with custom colors
- **Status Tracking**: Track lead progression through categories

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   pytest
   ```
5. **Commit your changes**
   ```bash
   git commit -m "Add amazing feature"
   ```
6. **Push to the branch**
   ```bash
   git push origin feature/amazing-feature
   ```
7. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Use meaningful commit messages

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Django community for the excellent framework
- Tailwind CSS for the beautiful styling
- Font Awesome for the icons
- All contributors who have helped improve this project

## 📞 Support

If you have any questions or need help:

- 📧 Email: support@leadflow.com
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/Lead-Management-System/issues)
- 📖 Documentation: [Wiki](https://github.com/yourusername/Lead-Management-System/wiki)

---

**Made with ❤️ by the LeadFlow Team**
