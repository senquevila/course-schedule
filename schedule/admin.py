from django.contrib import admin
from .models import CourseSchedule, CourseSession


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'days', 'start_time', 'end_time', 'created_at')
    list_filter = ('course', 'start_time')
    search_fields = ('course__name',)
    raw_id_fields = ('course',)
    ordering = ('course', 'start_time')


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'session_date', 'start_time', 'end_time', 'topic', 'created_at')
    list_filter = ('session_date', 'course', 'topic')
    search_fields = ('course__name', 'topic__name')
    raw_id_fields = ('course', 'topic')
    ordering = ('-session_date', 'start_time')
    readonly_fields = ('created_at',)
