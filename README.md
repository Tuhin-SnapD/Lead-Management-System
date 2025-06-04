# Lead Management System

A Django-based web application for managing leads and agents, designed to streamline the process of tracking, assigning, and following up with potential clients. This project is suitable for small businesses, sales teams, or anyone needing a simple CRM solution.

---

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [Running the Server](#running-the-server)
- [Environment Variables](#environment-variables)
- [Database](#database)
- [Static Files](#static-files)
- [Testing](#testing)
- [Deployment](#deployment)
- [Important Commands](#important-commands)
- [License](#license)
- [Contributing](#contributing)
- [Contact](#contact)

---

## Features

- User authentication (login/logout)
- Agent and lead management
- Assign leads to agents
- Admin interface for managing data
- Custom forms for leads and agents
- Modular app structure for scalability
- Responsive UI with Django templates
- Static files handling (CSS, JS, images)
- Database integration (SQLite by default)
- Easily extensible for new features

---

## Project Structure

```
.
├── agents/                 # Django app for agent management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── mixins.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   └── templates/
├── leads/                  # Django app for lead management
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── urls.py
│   ├── views.py
│   ├── migrations/
│   ├── templates/
│   └── tests/
├── server/                 # Django project config
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── static/                 # Source static files (CSS, JS, images)
├── static_root/            # Collected static files for deployment
├── staticfiles/            # (May be used for static collection)
├── templates/              # Global HTML templates
├── db.sqlite3              # SQLite database (default)
├── manage.py               # Django management script
├── requirements.txt        # Python dependencies
├── Procfile                # For deployment (e.g., Heroku)
├── runtime.txt             # Python version for deployment
├── runserver.sh            # Shell script to run the server
├── .gitignore              # Git ignore rules
├── README.md               # This file
├── important commands.txt  # Handy command references
└── dbdiagram.png           # Database schema diagram
```

---

## Installation

### Prerequisites

- Python 3.8+
- pip (Python package manager)
- Git (for cloning the repo)

### Steps

1. **Clone the repository**
    ```sh
    git clone https://github.com/Tuhin-SnapD/Lead-Management-System.git
    cd Lead-Management-System
    ```

2. **Create and activate a virtual environment**
    ```sh
    python -m venv env
    # On Windows:
    env\Scripts\activate.bat
    # On Unix/macOS:
    source env/bin/activate
    ```

3. **Install dependencies**
    ```sh
    pip install -r requirements.txt
    ```

4. **Apply migrations**
    ```sh
    python manage.py migrate
    ```

5. **Create a superuser (admin)**
    ```sh
    python manage.py createsuperuser
    ```

---

## Usage

- **Start the development server:**
    ```sh
    python manage.py runserver
    ```
- Visit `http://127.0.0.1:8000/` in your browser.

- **Access Django Admin:**
    - Go to `http://127.0.0.1:8000/admin/`
    - Login with the superuser credentials you created.

---

## Running the Server

- **Using the provided shell script (Linux/macOS):**
    ```sh
    ./runserver.sh
    ```
- **Or manually:**
    ```sh
    python manage.py runserver
    ```

---

## Environment Variables

- By default, settings are managed in [`server/settings.py`](server/settings.py).
- For production, set environment variables for `SECRET_KEY`, `DEBUG`, and `ALLOWED_HOSTS`.
- You can use a `.env` file with [django-environ](https://django-environ.readthedocs.io/) if you wish to manage secrets securely.

---

## Database

- Default: SQLite (`db.sqlite3`)
- To use PostgreSQL or another DB, update `DATABASES` in [`server/settings.py`](server/settings.py) and install the required Python packages.

---

## Static Files

- Place your static assets in the `static/` directory.
- Run `python manage.py collectstatic` to collect static files into `static_root/` for production deployment.
- Static files are served automatically in development.

---

## Testing

- To run tests for the apps:
    ```sh
    python manage.py test agents
    python manage.py test leads
    ```
- Test files are located in `agents/tests.py` and `leads/tests/`.

---

## Deployment

- **Heroku:**  
  The repository includes a `Procfile` and `runtime.txt` for easy deployment on Heroku.
    - Set up environment variables on Heroku for production.
    - Use `collectstatic` before deployment.

- **Other Platforms:**  
  Adapt the deployment process as needed for your platform (e.g., Docker, AWS, DigitalOcean).

---

## Important Commands

See [`important commands.txt`](important%20commands.txt) for a quick reference to common commands, including git and environment activation.

---

## License

- Source code: MIT License (see [`LICENSE`](staticfiles/admin/js/vendor/xregexp/LICENSE.txt) and [`LICENSE`](staticfiles/admin/js/vendor/select2/LICENSE.md))
- Fonts: Apache License 2.0 ([`staticfiles/admin/fonts/LICENSE.txt`](staticfiles/admin/fonts/LICENSE.txt))
- Icons: MIT License ([`staticfiles/admin/img/LICENSE`](staticfiles/admin/img/LICENSE))

---

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## Contact

- **Author:** [Tuhin-SnapD](https://github.com/Tuhin-SnapD)
- **Issues:** Please use the [GitHub Issues](https://github.com/Tuhin-SnapD/Lead-Management-System/issues) page for bug reports and feature requests.

---

## Screenshots

_Add screenshots or a demo GIF here to showcase the UI and features._

---

## Database Diagram

See [`dbdiagram.png`](dbdiagram.png) for a visual representation of the database schema.

---

## Acknowledgements

- [Django](https://www.djangoproject.com/)
- [Select2](https://select2.org/) (MIT License)
- [XRegExp](http://xregexp.com/) (MIT License)
- [Roboto Font](https://fonts.google.com/specimen/Roboto) (Apache License 2.0)
- [Font Awesome](http://fontawesome.io/) (SIL OFL 1.1)

---