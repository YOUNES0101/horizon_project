# Horizon Hotel Management System

## Technical Architecture Documentation

### Project Overview

Horizon Hotel Management System is a Django-based web application designed to manage hotel operations, bookings, and user interactions. The system follows a modular architecture with clear separation of concerns.

### System Architecture

#### 1. Core Components

- **Django Framework**: The project is built on Django, utilizing its MVT (Model-View-Template) architecture
- **Database**: SQLite (development) with potential for PostgreSQL in production
- **Frontend**: HTML, CSS, JavaScript with Bootstrap for responsive design
- **Authentication**: Django AllAuth for user authentication and management

#### 2. Application Structure

```
horizon_project/
├── apps/                    # Main applications directory
│   ├── core/               # Core functionality and shared components
│   ├── users/              # User management and authentication
│   ├── rooms/              # Room management and availability
│   ├── bookings/           # Booking system and reservations
│   └── dashboard/          # Admin dashboard and analytics
├── templates/              # HTML templates
│   └── partials/          # Reusable template components
├── static/                 # Static files (CSS, JS, images)
├── media/                  # User-uploaded media files
└── horizonh_project_config/ # Project configuration
```

### Component Communication

#### 1. Data Flow

- **Models Layer**: Each app contains its models defining data structure
- **Views Layer**: Handles business logic and data processing
- **Templates Layer**: Renders data to user interface
- **URLs**: Routes requests to appropriate views

#### 2. Inter-App Communication

- Apps communicate through Django's import system
- Shared functionality in core app
- Cross-app relationships through model foreign keys

### Deployment Guide for Railway with MySQL

#### 1. Prerequisites
- A [Railway](https://railway.app/) account
- Git installed on your machine
- Your project code pushed to GitHub

#### 2. Setting Up Railway
1. Log in to Railway and create a new project
2. Choose "Deploy from GitHub repo" and select your repository
3. Add a new MySQL service from the Railway dashboard
4. Connect your MySQL service to your deployment

#### 3. Environment Variables
Configure the following environment variables in Railway dashboard:
- `SECRET_KEY` - Your Django secret key
- `DEBUG` - Set to False for production
- `SITE_URL` - Your Railway app URL (e.g., https://your-app-name.up.railway.app)
- `EMAIL_HOST_USER` - Your email for sending notifications
- `EMAIL_HOST_PASSWORD` - Your email app password

#### 4. Database Migration
Railway will automatically run your Procfile command. To manually trigger migrations:
1. Go to Railway dashboard
2. Open the CLI for your deployment
3. Run: `python manage.py migrate`

#### 5. Static Files
Static files are handled by WhiteNoise. To collect static files:
1. Use Railway CLI: `python manage.py collectstatic --no-input`

### Key Features and Implementation

#### 1. User Management (users app)

- User registration and authentication
- Profile management
- Role-based access control

#### 2. Room Management (rooms app)

- Room type definitions
- Availability tracking
- Room status management

#### 3. Booking System (bookings app)

- Reservation processing
- Payment integration
- Booking status management

#### 4. Dashboard (dashboard app)

- Admin interface
- Analytics and reporting
- System management

### Technical Dependencies

```
Django==4.2.0
django-allauth==0.54.0
Pillow==9.5.0
python-dotenv==1.0.0
```

### Development Setup

1. **Environment Setup**

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Database Setup**

   ```bash
   python manage.py migrate
   ```

3. **Run Development Server**
   ```bash
   python manage.py runserver
   ```

### Security Considerations

1. **Authentication**

   - Django AllAuth for secure user authentication
   - CSRF protection enabled
   - Session management

2. **Data Protection**
   - Password hashing
   - Secure form handling
   - Input validation

### Deployment Considerations

1. **Production Settings**

   - Debug mode disabled
   - Secure static file serving
   - Database configuration
   - Environment variables

2. **Performance Optimization**
   - Static file caching
   - Database indexing
   - Template caching

### Testing Strategy

1. **Unit Tests**

   - Model tests
   - View tests
   - Form validation tests

2. **Integration Tests**
   - API endpoint tests
   - User flow tests
   - Cross-app functionality tests

### Maintenance and Updates

1. **Regular Updates**

   - Security patches
   - Dependency updates
   - Feature additions

2. **Backup Strategy**
   - Database backups
   - Media file backups
   - Configuration backups

### Contributing Guidelines

1. **Code Style**

   - PEP 8 compliance
   - Django coding style
   - Documentation requirements

2. **Version Control**
   - Git workflow
   - Branch naming conventions
   - Commit message format

### Support and Documentation

- Technical documentation in code
- API documentation
- User guides
- Troubleshooting guides

### License

[Specify your license here]

---

For more detailed information about specific components, please refer to the respective app's documentation.
