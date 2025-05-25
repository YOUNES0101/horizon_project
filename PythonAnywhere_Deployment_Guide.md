# PythonAnywhere Deployment Guide

This guide provides step-by-step instructions for deploying the Horizon Hotel Management System to PythonAnywhere.

## Prerequisites

1. A PythonAnywhere account ([Sign up here](https://www.pythonanywhere.com/))
2. Your project code (ideally in a Git repository)

## Deployment Steps

### 1. Sign in to PythonAnywhere

Go to [PythonAnywhere](https://www.pythonanywhere.com/) and log in to your account.

### 2. Open a Console

From the dashboard, click on "Consoles" and start a new Bash console.

### 3. Clone Your Repository

```bash
git clone https://github.com/your-username/horizon_project.git
```

### 4. Create a Virtual Environment

```bash
cd horizon_project
python -m venv venv
source venv/bin/activate
```

### 5. Install Requirements

```bash
pip install -r requirements.txt
```

### 6. Configure the Web App

1. Navigate to the "Web" tab in your PythonAnywhere dashboard
2. Click "Add a new web app"
3. Choose "Manual configuration" and select Python version 3.8 or newer
4. Set the path to your project: `/home/your-pythonanywhere-username/horizon_project`
5. Configure the WSGI file:

In the WSGI configuration file, replace the content with:

```python
import os
import sys

# Set path to your project directory
path = '/home/your-pythonanywhere-username/horizon_project'
if path not in sys.path:
    sys.path.append(path)

# Set environment variables for Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'horizonh_project_config.settings'
os.environ['DB_NAME'] = 'your-pythonanywhere-username$hotel_db2'
os.environ['DB_USER'] = 'your-pythonanywhere-username'
os.environ['DB_PASSWORD'] = 'your-database-password'
os.environ['DB_HOST'] = 'your-pythonanywhere-username.mysql.pythonanywhere-services.com'
os.environ['SECRET_KEY'] = 'your-secret-key'
os.environ['DEBUG'] = 'False'

# Import Django's WSGI handler
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

### 7. Create MySQL Database

1. Go to "Databases" tab and create a new MySQL database
2. Note down your database name (your-username$hotel_db2), host, username, and password

### 8. Update Settings

1. Edit `horizonh_project_config/settings.py` to ensure PythonAnywhere domain is in the ALLOWED_HOSTS list
2. Make sure to set DEBUG=False for production

### 9. Collect Static Files

From the Bash console:

```bash
cd horizon_project
source venv/bin/activate
python manage.py collectstatic --noinput
```

### 10. Migrate Database

```bash
python manage.py migrate
```

### 11. Create Superuser

```bash
python manage.py createsuperuser
```

### 12. Configure Static Files in PythonAnywhere

In your Web app configuration:

1. Add a Static Files entry:

   - URL: `/static/`
   - Path: `/home/your-pythonanywhere-username/horizon_project/staticfiles_collected`

2. Add a Media Files entry:
   - URL: `/media/`
   - Path: `/home/your-pythonanywhere-username/horizon_project/media`

### 13. Reload Web App

Click the "Reload" button in your web app configuration.

### 14. Access Your Site

Your site should now be available at `https://your-username.pythonanywhere.com`

## Troubleshooting

If you encounter issues:

1. Check the Error Log in PythonAnywhere Web tab
2. Make sure the database connection details are correct
3. Verify that all required environment variables are set
4. Check that static files are properly configured
