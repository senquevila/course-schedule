from django.urls import path
from rest_framework.routers import SimpleRouter
from . import views

app_name = 'courses'

# Template Views
template_patterns = [
    # Home and Courses
    path('', views.HomeView.as_view(), name='home'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
]

# HTMX Views
htmx_patterns = [
    # Topics
    path('courses/<int:course_id>/topics/', views.TopicListView.as_view(), name='topic-list'),
    path('courses/<int:course_id>/topics/create/', views.TopicCreateView.as_view(), name='topic-create'),
    path('courses/<int:course_id>/topics/<int:topic_id>/edit/', views.TopicUpdateView.as_view(), name='topic-edit'),
    path('courses/<int:course_id>/topics/<int:topic_id>/delete/', views.TopicDeleteView.as_view(), name='topic-delete'),

    # Materials
    path('courses/<int:course_id>/topics/<int:topic_id>/materials/', views.MaterialListView.as_view(), name='material-list'),
    path('courses/<int:course_id>/topics/<int:topic_id>/materials/create/', views.MaterialCreateView.as_view(), name='material-create'),
    path('courses/<int:course_id>/topics/<int:topic_id>/materials/<int:material_id>/edit/', views.MaterialUpdateView.as_view(), name='material-edit'),
    path('courses/<int:course_id>/topics/<int:topic_id>/materials/<int:material_id>/delete/', views.MaterialDeleteView.as_view(), name='material-delete'),

    # Calendar
    path('courses/<int:course_id>/calendar/', views.CourseCalendarListView.as_view(), name='calendar-list'),
    path('courses/<int:course_id>/calendar/generate/', views.CourseCalendarGenerateAllView.as_view(), name='calendar-generate'),
    path('courses/<int:course_id>/calendar/logs/', views.CourseCalendarLogListView.as_view(), name='calendar-log-list'),
    path('courses/<int:course_id>/calendar/logs/<int:log_id>/edit/', views.CourseCalendarLogUpdateView.as_view(), name='calendar-log-edit'),
    path('courses/<int:course_id>/calendar/logs/<int:log_id>/delete/', views.CourseCalendarLogDeleteView.as_view(), name='calendar-log-delete'),
    path('courses/<int:course_id>/calendar/delays/', views.CourseCalendarDelayView.as_view(), name='calendar-delays'),
    path('courses/<int:course_id>/calendar/<int:session_id>/', views.CourseCalendarSessionDetailView.as_view(), name='calendar-session-detail'),
    path('courses/<int:course_id>/calendar/<int:session_id>/log/', views.CourseCalendarLogCreateView.as_view(), name='calendar-log-create'),

    # Course Schedules
    path('courses/<int:course_id>/schedule/', views.CourseScheduleListView.as_view(), name='schedule-list'),
    path('courses/<int:course_id>/schedule/create/', views.CourseScheduleCreateView.as_view(), name='schedule-create'),
    path('courses/<int:course_id>/schedule/<int:schedule_id>/edit/', views.CourseScheduleUpdateView.as_view(), name='schedule-edit'),
    path('courses/<int:course_id>/schedule/<int:schedule_id>/delete/', views.CourseScheduleDeleteView.as_view(), name='schedule-delete'),
    path('courses/<int:course_id>/schedule/<int:schedule_id>/generate-calendar/', views.CourseCalendarGenerateView.as_view(), name='schedule-generate-calendar'),

    # Syllabus Import
    path('courses/<int:course_id>/syllabus/upload/', views.SyllabusUploadView.as_view(), name='syllabus-upload'),
    path('courses/<int:course_id>/syllabus/review/', views.SyllabusReviewView.as_view(), name='syllabus-review'),
    path('courses/<int:course_id>/syllabus/cancel/', views.SyllabusReviewCancelView.as_view(), name='syllabus-cancel'),
]

router = SimpleRouter()

urlpatterns = template_patterns + htmx_patterns + router.urls
