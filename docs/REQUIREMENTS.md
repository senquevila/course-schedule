# Course Programming Calendar - Requirements Document

## Project Overview

A web-based course calendar application that helps instructors manage teaching schedules by automatically generating course sessions, distributing topics across sessions, and displaying them in multiple calendar views (month, week, day, agenda).

**Technology Stack:**
- **Backend:** Django, Django REST Framework
- **Frontend:** HTMX with HTML/CSS
- **Database:** PostgreSQL
- **Repository:** ~/Documents/GitHub/senquevila/course-schedule

---

## Core Models & Data Structure

### 1. Period
Represents a 3-month teaching period (e.g., Spring 2026, Fall 2026)

**Fields:**
- `id` (number) - Primary key
- `name` (string) - Period name
- `start_date` (string) - ISO format YYYY-MM-DD
- `end_date` (string) - ISO format YYYY-MM-DD
- `created_at` (string) - Timestamp

### 2. Assignature
Represents a course subject/discipline with standard weekly hours

**Fields:**
- `id` (number) - Primary key
- `code` (string) - Unique course code (e.g., "CS101")
- `name` (string) - Course name (e.g., "Data Structures")
- `uv` (number) - Hours per week
- `created_at` (string) - Timestamp

### 3. Course
Represents a specific instance of an assignature taught in a period

**Fields:**
- `id` (number) - Primary key
- `assignature_id` (number) - Foreign key to Assignature
- `period_id` (number) - Foreign key to Period
- `name` (string) - Course instance name (e.g., "CS101 - Spring 2026 Morning")
- `instructor_name` (string) - Instructor name
- `location` (string) - Room/building location
- `created_at` (string) - Timestamp

### 4. Topic
Represents a teaching topic within a course

**Fields:**
- `id` (number) - Primary key
- `course_id` (number) - Foreign key to Course
- `code` (string) - Topic code (e.g., "T01")
- `name` (string) - Topic name (e.g., "Introduction to Arrays")
- `description` (string) - Description
- `order` (number) - Sequence position within course (1, 2, 3...)
- `created_at` (string) - Timestamp

### 5. Material
Represents teaching materials attached to a topic (documents, URLs, media)

**Fields:**
- `id` (number) - Primary key
- `topic_id` (number) - Foreign key to Topic
- `code` (string) - Material code
- `name` (string) - Material name
- `type` (enum) - Type: 'pdf', 'url', 'image', 'video', 'document'
- `url_or_path` (string) - External URL or file path
- `created_at` (string) - Timestamp

### 6. CourseSchedule
Represents the recurring weekly pattern for a course (e.g., MWF 9:00-11:00)

**Fields:**
- `id` (number) - Primary key
- `course_id` (number) - Foreign key to Course
- `day_of_week` (number) - Day number (0=Sunday...6=Saturday)
- `start_time` (string) - Time in HH:MM format
- `end_time` (string) - Time in HH:MM format
- `created_at` (string) - Timestamp

### 7. CourseSession
Represents a specific course session instance on a particular date (auto-generated from CourseSchedule)

**Fields:**
- `id` (number) - Primary key
- `course_id` (number) - Foreign key to Course
- `session_date` (string) - ISO format YYYY-MM-DD
- `day_of_week` (number) - Day number (0-6)
- `start_time` (string) - Time in HH:MM format
- `end_time` (string) - Time in HH:MM format
- `topic_id` (number | null) - Foreign key to Topic (null if not assigned)
- `created_at` (string) - Timestamp

---

## Database Schema

### PostgreSQL Tables

```sql
-- Periods
CREATE TABLE periods (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assignatures
CREATE TABLE assignatures (
  id SERIAL PRIMARY KEY,
  code VARCHAR(50) NOT NULL UNIQUE,
  name VARCHAR(255) NOT NULL,
  uv INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Courses
CREATE TABLE courses (
  id SERIAL PRIMARY KEY,
  assignature_id INTEGER NOT NULL,
  period_id INTEGER NOT NULL,
  name VARCHAR(255) NOT NULL,
  instructor_name VARCHAR(255),
  location VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (assignature_id) REFERENCES assignatures(id),
  FOREIGN KEY (period_id) REFERENCES periods(id)
);

-- Topics
CREATE TABLE topics (
  id SERIAL PRIMARY KEY,
  course_id INTEGER NOT NULL,
  code VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  description TEXT,
  "order" INTEGER NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Materials
CREATE TABLE materials (
  id SERIAL PRIMARY KEY,
  topic_id INTEGER NOT NULL,
  code VARCHAR(50) NOT NULL,
  name VARCHAR(255) NOT NULL,
  type VARCHAR(50) NOT NULL CHECK(type IN ('pdf', 'url', 'image', 'video', 'document')),
  url_or_path TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (topic_id) REFERENCES topics(id)
);

-- Course Schedules
CREATE TABLE course_schedules (
  id SERIAL PRIMARY KEY,
  course_id INTEGER NOT NULL,
  day_of_week INTEGER NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id)
);

-- Course Sessions
CREATE TABLE course_sessions (
  id SERIAL PRIMARY KEY,
  course_id INTEGER NOT NULL,
  session_date DATE NOT NULL,
  day_of_week INTEGER NOT NULL,
  start_time TIME NOT NULL,
  end_time TIME NOT NULL,
  topic_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (course_id) REFERENCES courses(id),
  FOREIGN KEY (topic_id) REFERENCES topics(id)
);
```

---

## Key Features & Workflows

### Feature 1: Course Creation & Setup
1. User creates a **Period** (start/end date for semester)
2. User creates an **Assignature** (course subject with weekly hours)
3. User creates a **Course** (assigns assignature to period with instructor/location)
4. User sets up **CourseSchedule** (selects which days per week, sets time)
5. System auto-generates **CourseSession** records for each matching date in period
6. User creates **Topics** and optionally auto-distributes or manually assigns to sessions

### Feature 2: Topic Management
- **Create Topics:** User adds topics with code, name, description in order
- **Auto-distribute:** System calculates total sessions and distributes topics evenly
- **Manual Override:** User can click individual session and reassign topic
- **Attach Materials:** User adds materials (PDFs, URLs, images, videos) to each topic
- **Materials Shared:** Same materials display across all sessions teaching that topic

### Feature 3: Session Generation Algorithm
- **Input:** Course period dates, CourseSchedule (recurring days/times)
- **Algorithm:**
  1. Find all dates matching the recurring pattern between period start/end
  2. Create CourseSession record for each matching date
  3. Example: Course 3/1-5/15 with MWF 9-11 creates sessions for all Mon/Wed/Fri in range
- **Output:** CourseSession records with topic_id initially null

### Feature 4: Calendar Views
App displays course sessions in four different views:

#### 4a. Month View
- Grid layout with calendar days
- Blue dots on dates with sessions
- Tap date to see that day's sessions
- Navigation arrows for prev/next month
- Display session time and topic name

#### 4b. Week View
- 7 columns (Monday through Sunday)
- Hourly rows for time slots
- Course sessions displayed as blocks
- Shows topic name inside session block
- Navigation arrows for prev/next week

#### 4c. Day View
- Hourly breakdown for single day
- All sessions for that day listed
- Tap session to view topic + materials
- Show instructor name, location, topic name

#### 4d. Agenda View
- Chronological list of upcoming sessions
- Grouped by week or date
- Each entry: date, time, topic name, location
- Tap to open session details

### Feature 5: Materials Display
- Materials attached to topics (not individual sessions)
- When viewing session details:
  - Fetch associated topic
  - Display all materials for that topic
  - Support types: PDF, URL, image, video, document
- URLs can be tapped to open in browser
- PDFs can be viewed in-app or opened externally

---

## Navigation Structure

### Page Hierarchy

```
/courses/ (Courses List Page)
├── /courses/<id>/ (Course Detail Page)
│   ├── /courses/<id>/edit/ (Edit course info)
│   ├── /courses/<id>/schedule/ (Define weekly pattern & generate sessions)
│   ├── /courses/<id>/topics/ (Manage topics)
│   │   └── /courses/<id>/topics/<topic_id>/edit/ (Edit topic, attach materials)
│   └── /courses/<id>/calendar/ (Calendar views with HTMX tabs):
│       ├── ?view=month (Month view)
│       ├── ?view=week (Week view)
│       ├── ?view=day (Day view)
│       └── ?view=agenda (List view)
│           └── /courses/<id>/sessions/<session_id>/ (Session details + materials)
```

### Navigation Patterns
- **List → Detail:** Click course link → GET /courses/<id>/
- **Detail → Edit:** Click "Edit" button → GET /courses/<id>/edit/ (HTMX form)
- **Detail → Calendar:** Click "View Calendar" → GET /courses/<id>/calendar/?view=month
- **Calendar ↔ Calendar:** View buttons swap view parameter (HTMX)
- **Calendar → Session:** Click session → GET /courses/<id>/sessions/<session_id>/ (HTMX modal or page)
- **Detail → Setup:** Click "Setup Schedule" → GET /courses/<id>/schedule/ (HTMX form)

---

## Core Workflows

### Workflow 1: Create a New Course and Generate Sessions

1. User taps FAB on CoursesHome → CoursesAddEdit
2. Select Assignature (dropdown: "CS101 Data Structures")
3. Select Period (dropdown: "Spring 2026")
4. Enter course name: "CS101 - Spring 2026 Morning"
5. Enter instructor: "Dr. Smith"
6. Enter location: "Room 204"
7. Save → Navigate to CourseDetail

8. On CourseDetail, tap "Setup Schedule"
9. Select days: Monday ✓, Wednesday ✓, Friday ✓
10. Set time: 9:00 AM - 11:00 AM
11. Tap "Generate Sessions" → System creates ~16 CourseSession records
12. Show preview: "Generated 16 sessions from 3/1/2026 to 5/15/2026"
13. Confirm → Sessions saved to database

### Workflow 2: Create Topics and Auto-Distribute

1. On CourseDetail, tap "Manage Topics"
2. Tap FAB to add first topic
3. Enter: Code "T01", Name "Arrays", Description "Basic array concepts"
4. Save and continue adding: "T02 Linked Lists", "T03 Trees", "T04 Graphs", "T05 Hash Tables"
5. All 5 topics saved

6. Tap "Auto-distribute Topics" button
7. System calculates: 16 sessions ÷ 5 topics = ~3 sessions per topic
8. Assigns: T01 to sessions 1-3, T02 to 4-6, T03 to 7-9, T04 to 10-12, T05 to 13-16
9. Show result: "Distributed 5 topics across 16 sessions"
10. Confirm → topic_id values set in course_sessions table

### Workflow 3: Attach Materials to Topic

1. On TopicsManage, tap "T01 Arrays"
2. On TopicDetail, tap "Add Material"
3. Enter: Code "M01", Name "Arrays Lecture Notes", Type "PDF"
4. Enter URL: "https://example.com/arrays-notes.pdf"
5. Save → Material attached to topic

6. When any session on a day teaching Arrays is viewed:
   - Session details show topic "Arrays"
   - Materials section displays "Arrays Lecture Notes (PDF)" with clickable link

### Workflow 4: View Course in Different Calendar Views

Starting from CourseDetail, user switches views:

1. Tap "View Calendar" → CalendarMonth opens
   - Shows month grid with blue dots on M/W/F dates
   - Tap a date → Shows sessions for that day with topic names

2. Tap "Week" button → CalendarWeek opens
   - Shows 7-day week with hourly time slots
   - Sessions appear as blocks with topic names
   - Swipe or tap arrows to navigate weeks

3. Tap "Day" button → User selects a specific day
   - CalendarDay opens showing hourly breakdown
   - Lists all sessions with times, topics, locations

4. Tap "Agenda" button → CalendarAgenda opens
   - Chronological list of all upcoming sessions
   - Each entry: "Wed, Mar 3, 2026 | 9:00-11:00 AM | T01: Arrays | Room 204"
   - Tap entry → SessionDetail with full topic info + materials

---

## Implementation Phases

### Phase 1: Django Project Setup & Models (Foundation)
- Initialize Django project and `courses` app
- Create Django models in `models.py`:
  - Period
  - Assignature
  - Course
  - Topic
  - Material
  - CourseSchedule
  - CourseSession
- Configure PostgreSQL database connection in `settings.py`
- Create migrations and run `migrate`
- Register models in `admin.py` for Django admin interface
- Create `serializers.py` with Django REST Framework serializers for all models

### Phase 2: Utility Functions & Service Layer
- **Session Generation:** `generate_sessions_for_course(course_id)`
  - Calculates matching dates based on CourseSchedule pattern
  - Creates CourseSession records
  
- **Topic Distribution:** `auto_distribute_topics(course_id)`
  - Calculates sessions per topic (total sessions ÷ topic count)
  - Assigns topics sequentially to sessions

- **Date/Time Helpers:** (`utils/helpers.py`)
  - `get_day_name(day_of_week)` → "Monday"
  - `get_day_of_week(date_obj)` → 0-6
  - `get_week_bounds(date_obj)` → {start, end}
  - `get_month_bounds(date_obj)` → {start, end}
  - `format_date(date_obj)` → "Mar 3, 2026"
  - `format_time(time_obj)` → "9:00 AM"
  - `is_same_day(date1, date2)` → boolean

### Phase 3: API Endpoints & Views (Django REST Framework)
- Create ViewSets for all models (using generics or ViewSets)
- Create URLs configuration with router for REST endpoints
- Implement CRUD endpoints:
  - `/api/periods/` - List, create, retrieve, update, delete periods
  - `/api/assignatures/` - List, create, retrieve, update, delete assignatures
  - `/api/courses/` - List, create, retrieve, update, delete courses
  - `/api/topics/` - List, create, retrieve, update, delete topics
  - `/api/materials/` - List, create, retrieve, update, delete materials
  - `/api/course-schedules/` - Manage course schedules
  - `/api/course-sessions/` - List, retrieve, update sessions

### Phase 4: HTML Templates & HTMX Integration
- Create base template with navigation
- Build template views using Django template language
- Create HTMX-enabled forms for create/update operations:
  - `course_list.html` - List all courses with HTMX delete/edit buttons
  - `course_form.html` - Create/edit course (HTMX form submission)
  - `schedule_form.html` - Setup schedule with HTMX
  - `topics_list.html` - Manage topics with HTMX reordering
  - `topic_form.html` - Create/edit topic with material attachment
  - `calendar_base.html` - Base calendar template with HTMX view switching
  - `calendar_month.html` - Month grid with HTMX date selection
  - `calendar_week.html` - Week view with HTMX navigation
  - `calendar_day.html` - Day view with session details
  - `calendar_agenda.html` - Chronological list view
  - `session_detail.html` - Full session details with materials

### Phase 5: Frontend Polish & Styling
- Set up CSS styling (Bootstrap or custom CSS)
- Create reusable HTML components:
  - Course card partial
  - Session block partial
  - Materials list partial
- Implement HTMX interactions:
  - Form validation and submission without page reload
  - Modal dialogs for confirmations
  - Inline editing for quick updates
  - Real-time calendar view switching
- Add JavaScript enhancements as needed
- Test responsive design across devices

---

## Testing Checklist

### Manual Testing Flow

**Setup Phase:**
- [ ] Create Period: "Spring 2026" (3/1/2026 - 5/15/2026)
- [ ] Create Assignature: "CS101", "Data Structures", 3 hours/week
- [ ] Create Course: CS101 + Spring 2026, "John Doe", "Room 101"

**Schedule Phase:**
- [ ] Open ScheduleSetup for course
- [ ] Select: Monday, Wednesday, Friday
- [ ] Set time: 9:00 AM - 11:00 AM
- [ ] Generate sessions
- [ ] Verify ~16 sessions created (3/3, 3/5, 3/8... through 5/12)

**Topic Phase:**
- [ ] Create 5 topics: Arrays, Linked Lists, Trees, Graphs, Hash Tables
- [ ] Auto-distribute across 16 sessions
- [ ] Verify each topic assigned ~3 sessions

**Materials Phase:**
- [ ] Add material to "Arrays" topic: PDF link
- [ ] Verify material displays when viewing Arrays sessions

**Calendar Views:**
- [ ] Month view: See blue dots on M/W/F dates
- [ ] Week view: See 9-11 AM blocks on M/W/F
- [ ] Day view: Click a day, see session with topic
- [ ] Agenda view: See chronological list of all sessions

### Edge Cases
- [ ] Course spanning month boundaries
- [ ] Period starting/ending mid-week
- [ ] Multiple courses in same period
- [ ] Manual topic reassignment to different session
- [ ] Material deletion and re-addition

---

## Technical Constraints

1. **Backend Framework:** Django with Django REST Framework for API endpoints
2. **Database:** PostgreSQL with Django ORM
3. **Frontend:** HTMX with HTML templates (Django templates)
4. **Styling:** CSS (Bootstrap or custom CSS)
5. **Date Handling:** Django DateField (YYYY-MM-DD), no timezones
6. **Time Format:** Django TimeField (HH:MM in 24-hour format)
7. **API:** REST API built with Django REST Framework for programmatic access
8. **Frontend Interactions:** HTMX for dynamic updates without full page reloads

---

## File Structure to Create

```
course-schedule/
├── manage.py
├── requirements.txt
├── db.sqlite3 (PostgreSQL connection)
├── course_schedule/
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
├── courses/
│   ├── migrations/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── serializers.py
│   ├── admin.py
│   ├── apps.py
│   ├── tests.py
│   └── templates/
│       ├── courses/
│       │   ├── course_list.html
│       │   ├── course_detail.html
│       │   ├── course_form.html
│       │   ├── schedule_form.html
│       │   ├── topics_list.html
│       │   ├── topic_form.html
│       │   ├── calendar_base.html
│       │   ├── calendar_month.html
│       │   ├── calendar_week.html
│       │   ├── calendar_day.html
│       │   ├── calendar_agenda.html
│       │   └── session_detail.html
│       └── base.html
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── htmx.min.js
└── utils/
    ├── helpers.py
    ├── courseCalculations.py
    └── topicDistribution.py
```

---

## Success Criteria

✓ User can create Period, Assignature, and Course  
✓ User can define weekly schedule and auto-generate sessions  
✓ User can create topics and auto-distribute across sessions  
✓ User can attach materials to topics  
✓ All 4 calendar views display correctly (Month/Week/Day/Agenda)  
✓ Tapping sessions shows topic + materials  
✓ Manual topic reassignment works  
✓ Navigation between views is smooth and intuitive  
✓ Database properly stores and retrieves all data  
✓ No crashes on edge case dates (month/year boundaries)  

---

## Notes

- This is a web-based Django application with HTMX frontend
- All dates stored as Django DateField (YYYY-MM-DD)
- All times stored as Django TimeField (HH:MM in 24-hour format)
- Materials are topic-level (shared across all sessions teaching that topic)
- No timezone handling needed (local time only)
- Session generation is one-time per course (not dynamic, but can be regenerated)
- Topics can be manually reassigned to different sessions anytime
- API is REST-based using Django REST Framework for programmatic access
- HTMX enables dynamic UI updates without full page reloads
- PostgreSQL provides robust data persistence and ACID compliance
