# Course Programming Calendar

A web-based course calendar application that helps instructors manage teaching schedules by automatically generating course sessions, distributing topics across sessions, and displaying them in multiple calendar views (month, week, day, agenda).

## Technology Stack

- **Backend:** Django 6.0 + Django REST Framework
- **Frontend:** HTMX + HTML/CSS + Alpine.js
- **Database:** SQLite (development) / PostgreSQL (production)
- **Python:** 3.13+

## Project Structure

```
course-schedule/
├── course_schedule/                    # Main Django project configuration
│   ├── settings.py              # Django settings (DB, apps, middleware)
│   ├── urls.py                  # Root URL routing
│   ├── wsgi.py                  # WSGI application
│   └── asgi.py                  # ASGI application
│
├── courses/                      # Main Django app
│   ├── models.py                # 7 data models (Period, Assignature, Course, Topic, Material, CourseSchedule, CourseSession)
│   ├── views.py                 # API ViewSets and template views (TODO)
│   ├── serializers.py           # DRF serializers (TODO)
│   ├── urls.py                  # App URL routing
│   ├── admin.py                 # Django admin interface
│   ├── apps.py                  # App configuration
│   ├── migrations/              # Database migrations
│   └── templates/               # HTML templates (TODO)
│       ├── base.html            # Base template with navigation
│       └── courses/             # Course-related templates
│           ├── course_list.html
│           ├── course_form.html
│           ├── topics_list.html
│           └── calendar_*.html  # 4 calendar view templates
│
├── utils/                        # Utility modules
│   ├── helpers.py               # Date/time helper functions (TODO)
│   ├── courseCalculations.py    # Session generation logic (TODO)
│   └── topicDistribution.py     # Topic distribution logic (TODO)
│
├── static/                       # Static files
│   ├── css/
│   │   └── style.css            # Custom CSS styling (TODO)
│   └── js/
│       └── htmx.min.js          # HTMX library
│
├── templates/                    # Project-level templates
│   └── base.html                # Base template (TODO)
│
├── manage.py                     # Django management script
├── requirements.txt              # Python dependencies
├── docker-compose.yml            # Docker Compose for PostgreSQL
├── init-db.sql                   # PostgreSQL initialization script
├── .env                          # Environment variables (development)
├── .env.example                  # Environment variables template
├── db.sqlite3                    # SQLite database (development)
├── REQUIREMENTS.md               # Project requirements and specifications
└── README.md                     # This file
```

## Setup Instructions

### Prerequisites
- Python 3.13+
- pip and virtual environment
- Docker (optional, for PostgreSQL)

### Installation

1. **Clone the repository**
   ```bash
   cd ~/Documents/GitHub/senquevila/course-schedule
   ```

2. **Create and activate virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env if needed (defaults work for development)
   ```

5. **Run migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser (for Django admin)**
   ```bash
   python manage.py createsuperuser
   # Follow the prompts to create an admin user
   ```

7. **Start development server**
   ```bash
   python manage.py runserver
   ```

   Server will be available at: `http://localhost:8000/`

### Database Options

**SQLite (Development - Default)**
- Already configured and working
- No additional setup needed
- Data stored in `db.sqlite3`

**PostgreSQL (Production)**
- Requires Docker and docker-compose
- Start with: `docker-compose up -d`
- Update `.env` with PostgreSQL credentials
- Run migrations: `python manage.py migrate`

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate

# Run development server
python manage.py runserver

# Create/apply migrations
python manage.py makemigrations
python manage.py migrate

# Django shell (interactive Python with Django context)
python manage.py shell

# Create superuser
python manage.py createsuperuser

# Collect static files (production)
python manage.py collectstatic

# Run tests
python manage.py test

# Format code
black .
python -m flake8 .
```

## Contributing

Development workflow:
1. Create feature branch
2. Make changes
3. Test thoroughly
4. Create pull request

## License

[Add your license here]

## Contact

Project by: senquevila
Repository: ~/Documents/GitHub/senquevila/course-schedule
