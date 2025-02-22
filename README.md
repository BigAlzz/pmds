# Performance Management and Development System (PMDS)

A comprehensive web-based system for managing employee performance agreements, reviews, and development plans.

## Features

- Performance Agreement Management
- Mid-Year Reviews
- Personal Development Plans
- Improvement Plans
- Salary Level Management
- Notification System
- User Profile Management
- Role-based Access Control (Employee, Manager, HR)

## Technology Stack

- Python 3.10+
- Django 5.0.2
- Bootstrap 5
- PostgreSQL (Production) / SQLite (Development)
- Crispy Forms with Bootstrap 5 template pack

## Prerequisites

- Python 3.10 or higher
- Virtual Environment
- pip (Python package installer)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/PMDS.git
cd PMDS
```

2. Create and activate a virtual environment:
```bash
python -m venv Venv
# Windows
Venv\Scripts\activate
# Linux/Mac
source Venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a .env file in the project root and add your environment variables:
```
DEBUG=True
SECRET_KEY=your-secret-key-here
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=PMS System <noreply@yourdomain.com>
```

5. Run migrations:
```bash
python manage.py migrate
```

6. Create a superuser:
```bash
python manage.py createsuperuser
```

7. Run the development server:
```bash
python manage.py runserver
```

## Usage

1. Access the admin interface at `http://localhost:8000/admin/`
2. Log in with your superuser credentials
3. Create users and assign roles (Employee, Manager, HR)
4. Users can then log in at `http://localhost:8000/` to:
   - Create and manage performance agreements
   - Conduct mid-year reviews
   - Create development plans
   - Track improvement plans
   - Receive notifications

## Project Structure

```
PMDS/
├── performance/              # Main application
│   ├── migrations/          # Database migrations
│   ├── static/             # Static files (CSS, JS)
│   ├── templates/          # HTML templates
│   ├── templatetags/       # Custom template tags
│   ├── tests/              # Test files
│   ├── forms.py           # Form definitions
│   ├── models.py          # Database models
│   ├── urls.py            # URL configurations
│   └── views.py           # View logic
├── performance_management_system/  # Project settings
├── manage.py              # Django management script
├── requirements.txt       # Project dependencies
└── README.md             # This file
```

## Testing

Run the test suite:
```bash
python manage.py test
```

## Deployment

For production deployment:

1. Set DEBUG=False in .env
2. Configure your production database in settings.py
3. Set up your web server (e.g., Gunicorn)
4. Configure static file serving
5. Set up SSL/TLS
6. Configure email settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 