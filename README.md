# Course Programming Calendar

A web-based course calendar application that helps instructors manage teaching schedules by automatically generating course sessions, distributing topics across sessions, and displaying them in multiple calendar views (month, week, day, agenda).

**Repository:** `~/Documents/GitHub/senquevila/course-schedule`

## Technology Stack

- **Backend:** Django 6.0 + Django REST Framework
- **Frontend:** HTMX + HTML/CSS (custom styling, no framework)
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

## Data Models

### 1. Period
Represents a 3-month teaching period (e.g., Spring 2026, Fall 2026)
- `name`: String - Period name
- `start_date`: Date - Period start
- `end_date`: Date - Period end
- `created_at`: DateTime - Creation timestamp

### 2. Assignature
Represents a course subject/discipline with standard weekly hours
- `code`: String (unique) - Course code (e.g., "CS101")
- `name`: String - Course name
- `uv`: Integer - Hours per week
- `created_at`: DateTime - Creation timestamp

### 3. Course
Represents a specific instance of an assignature taught in a period
- `assignature`: ForeignKey → Assignature
- `period`: ForeignKey → Period
- `name`: String - Course instance name
- `instructor_name`: String - Instructor name
- `location`: String - Room/building location
- `created_at`: DateTime - Creation timestamp

### 4. Topic
Represents a teaching topic within a course
- `course`: ForeignKey → Course
- `code`: String - Topic code (e.g., "T01")
- `name`: String - Topic name
- `description`: Text - Topic description
- `order`: Integer - Sequence position
- `created_at`: DateTime - Creation timestamp

### 5. Material
Represents teaching materials attached to a topic
- `topic`: ForeignKey → Topic
- `code`: String - Material code
- `name`: String - Material name
- `material_type`: Choice - 'pdf', 'url', 'image', 'video', 'document'
- `url_or_path`: TextField - External URL or file path
- `created_at`: DateTime - Creation timestamp

### 6. CourseSchedule
Represents the recurring weekly pattern for a course (e.g., MWF 9:00-11:00)
- `course`: ForeignKey → Course
- `day_of_week`: Integer - Day number (0=Sunday...6=Saturday)
- `start_time`: Time - Session start time
- `end_time`: Time - Session end time
- `created_at`: DateTime - Creation timestamp

### 7. CourseSession
Represents a specific course session instance on a particular date
- `course`: ForeignKey → Course
- `session_date`: Date - Session date
- `day_of_week`: Integer - Day number (0-6)
- `start_time`: Time - Session start time
- `end_time`: Time - Session end time
- `topic`: ForeignKey → Topic (nullable) - Assigned topic
- `created_at`: DateTime - Creation timestamp

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

## Django Admin Interface

Access the Django admin at: `http://localhost:8000/admin/`

**Available Models:**
- Periods - Create and manage teaching periods
- Assignatures - Define course subjects and weekly hours
- Courses - Create course instances
- Topics - Add topics to courses
- Materials - Attach materials to topics
- Course Schedules - Set weekly recurring patterns
- Course Sessions - View/manage generated sessions

## API Endpoints (TODO - Not Yet Implemented)

```
REST API Base: /api/

GET    /api/periods/                 - List all periods
POST   /api/periods/                 - Create period
GET    /api/periods/{id}/            - Retrieve period
PUT    /api/periods/{id}/            - Update period
DELETE /api/periods/{id}/            - Delete period

GET    /api/assignatures/            - List assignatures
POST   /api/assignatures/            - Create assignature
GET    /api/assignatures/{id}/       - Retrieve assignature
PUT    /api/assignatures/{id}/       - Update assignature
DELETE /api/assignatures/{id}/       - Delete assignature

GET    /api/courses/                 - List courses
POST   /api/courses/                 - Create course
GET    /api/courses/{id}/            - Retrieve course
PUT    /api/courses/{id}/            - Update course
DELETE /api/courses/{id}/            - Delete course
POST   /api/courses/{id}/generate-sessions/ - Generate sessions
POST   /api/courses/{id}/auto-distribute/  - Auto-distribute topics

GET    /api/topics/                  - List topics
POST   /api/topics/                  - Create topic
GET    /api/topics/{id}/             - Retrieve topic
PUT    /api/topics/{id}/             - Update topic
DELETE /api/topics/{id}/             - Delete topic

GET    /api/materials/               - List materials
POST   /api/materials/               - Create material
GET    /api/materials/{id}/          - Retrieve material
PUT    /api/materials/{id}/          - Update material
DELETE /api/materials/{id}/          - Delete material

GET    /api/course-schedules/        - List schedules
POST   /api/course-schedules/        - Create schedule
GET    /api/course-schedules/{id}/   - Retrieve schedule
PUT    /api/course-schedules/{id}/   - Update schedule
DELETE /api/course-schedules/{id}/   - Delete schedule

GET    /api/course-sessions/         - List sessions
GET    /api/course-sessions/{id}/    - Retrieve session
PUT    /api/course-sessions/{id}/    - Update session
```

## Web Interface Routes (TODO - Not Yet Implemented)

```
GET  /courses/                       - List all courses
GET  /courses/<id>/                  - View course details
GET  /courses/<id>/edit/             - Edit course
GET  /courses/<id>/schedule/         - Setup course schedule
GET  /courses/<id>/topics/           - Manage topics
GET  /courses/<id>/calendar/         - View calendar (with ?view=month|week|day|agenda)
GET  /courses/<id>/sessions/<sid>/   - View session details
```

## Core Workflows

### Workflow 1: Create a Course and Generate Sessions

1. Create a **Period** (e.g., "Spring 2026" from 3/1/2026 to 5/15/2026)
2. Create an **Assignature** (e.g., "CS101 Data Structures", 3 hours/week)
3. Create a **Course** (assign assignature to period, add instructor and location)
4. Set up **Schedule** (select days: M/W/F, set time: 9:00-11:00)
5. **Generate Sessions** (system creates ~16 sessions from 3/3 to 5/12)

### Workflow 2: Create Topics and Auto-Distribute

1. Create **Topics** (e.g., Arrays, Linked Lists, Trees, Graphs, Hash Tables)
2. **Auto-distribute** topics across 16 sessions (~3 sessions per topic)
3. Verify assignments (T01 → sessions 1-3, T02 → sessions 4-6, etc.)

### Workflow 3: Attach Materials to Topics

1. Open a **Topic**
2. Add **Material** (code, name, type, URL/path)
3. Material displays in all sessions teaching that topic

### Workflow 4: View Course in Different Calendars

1. **Month View** - Grid with dots on session dates
2. **Week View** - 7-day layout with hourly slots
3. **Day View** - Hourly breakdown for a single day
4. **Agenda View** - Chronological list of all sessions

## Implementation Status

### ✅ Completed
- Django project setup
- All 7 models defined and migrated
- Django admin interface configured
- Static and template directories created
- Environment configuration

### 🚧 In Progress / TODO
- REST API endpoints (serializers, viewsets)
- Service layer (session generation, topic distribution)
- HTML templates with HTMX
- Custom CSS styling
- Calendar view logic
- Form handling and validation

### 📋 Development Roadmap

**Phase 1 (Foundation)** - ✅ DONE
- Django setup, models, migrations

**Phase 2 (API & Services)**
- Service layer for business logic
- DRF serializers and viewsets
- API endpoints testing

**Phase 3 (Templates & Views)**
- Base template and navigation
- CRUD templates for each model
- HTMX form handling

**Phase 4 (Calendar Views)**
- Month, week, day, and agenda calendar views
- Calendar logic and rendering
- Session details display

**Phase 5 (Styling & Polish)**
- Custom CSS for all templates
- HTMX dynamic interactions
- UI/UX improvements

**Phase 6 (Testing & Deployment)**
- Unit and integration tests
- Production deployment setup
- Documentation

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

## Project Files Reference

| File | Purpose |
|------|---------|
| `course_schedule/settings.py` | Django configuration, database, installed apps |
| `course_schedule/urls.py` | Root URL routing |
| `courses/models.py` | Database models definition |
| `courses/views.py` | API views and template views (TODO) |
| `courses/serializers.py` | DRF serializers (TODO) |
| `courses/urls.py` | App URL routing (TODO) |
| `courses/admin.py` | Django admin configuration |
| `utils/helpers.py` | Date/time utilities (TODO) |
| `utils/courseCalculations.py` | Session generation logic (TODO) |
| `utils/topicDistribution.py` | Topic distribution logic (TODO) |
| `requirements.txt` | Python dependencies |
| `.env` | Environment variables |
| `REQUIREMENTS.md` | Detailed project specifications |

## Troubleshooting

### Issue: Database locked
**Solution:** Delete `db.sqlite3` and run `python manage.py migrate` again

### Issue: Port 8000 already in use
**Solution:** Use `python manage.py runserver 8001` or kill process on port 8000

### Issue: Superuser login fails in admin
**Solution:** Create new superuser with `python manage.py createsuperuser`

### Issue: Static files not loading
**Solution:** Run `python manage.py collectstatic --clear --noinput`

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
