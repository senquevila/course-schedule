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

    # Course Schedules
    path('courses/<int:course_id>/schedule/', views.CourseScheduleListView.as_view(), name='schedule-list'),
    path('courses/<int:course_id>/schedule/create/', views.CourseScheduleCreateView.as_view(), name='schedule-create'),
    path('courses/<int:course_id>/schedule/<int:schedule_id>/edit/', views.CourseScheduleUpdateView.as_view(), name='schedule-edit'),
    path('courses/<int:course_id>/schedule/<int:schedule_id>/delete/', views.CourseScheduleDeleteView.as_view(), name='schedule-delete'),

    # Syllabus Import
    path('courses/<int:course_id>/syllabus/upload/', views.SyllabusUploadView.as_view(), name='syllabus-upload'),
    path('courses/<int:course_id>/syllabus/review/', views.SyllabusReviewView.as_view(), name='syllabus-review'),
]

router = SimpleRouter()

urlpatterns = template_patterns + htmx_patterns + router.urls
