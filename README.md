# Performance Management and Development System (PMDS)

A comprehensive Django-based application for managing employee performance reviews, development plans, and improvement plans.

## Features

- **Performance Agreements**: Create and manage performance agreements between employees and managers
- **Mid-Year Reviews**: Conduct and track mid-year performance evaluations
- **Final Reviews**: Complete end-of-cycle performance assessments
- **Personal Development Plans**: Track employee growth and development activities
- **Improvement Plans**: Manage performance improvement initiatives
- **User Role Management**: Different views and permissions for employees, managers, and administrators

## Technology Stack

- Django (Python web framework)
- Bootstrap (Frontend styling)
- SQLite (Database)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/BigAlzz/pmds.git
   cd pmds
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv Venv
   Venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Run migrations:
   ```
   python manage.py migrate
   ```

5. Create a superuser:
   ```
   python manage.py createsuperuser
   ```

6. Run the development server:
   ```
   python manage.py runserver
   ```

## Usage

1. Access the admin interface at `http://localhost:8000/admin/` to manage users and data
2. Regular users can access the application at `http://localhost:8000/`

## Project Structure

- `performance/`: Main application directory
  - `models.py`: Database models for performance management
  - `views.py`: View functions and classes
  - `forms.py`: Form definitions
  - `templates/`: HTML templates
  - `static/`: CSS, JavaScript, and images
  - `templatetags/`: Custom template tags

## License

This project is licensed under the MIT License - see the LICENSE file for details. 