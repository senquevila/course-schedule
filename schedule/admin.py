from django.contrib import admin
from .models import CourseSchedule, CourseCalendar, CourseCalendarLog, NonWorkingDay


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'days', 'start_time', 'end_time', 'created_at')
    list_filter = ('course', 'start_time')
    search_fields = ('course__name',)
    autocomplete_fields = ('course',)
    ordering = ('course', 'start_time')


@admin.register(CourseCalendar)
class CourseCalendarAdmin(admin.ModelAdmin):
    list_display = ('course', 'session_date', 'start_time', 'end_time', 'topic', 'created_at')
    list_filter = ('session_date', 'course', 'topic')
    search_fields = ('course__name', 'topic__name')
    autocomplete_fields = ('course', 'topic')
    ordering = ('-session_date', 'start_time')
    readonly_fields = ('created_at',)


@admin.register(NonWorkingDay)
class NonWorkingDayAdmin(admin.ModelAdmin):
    list_display = ('date', 'reason')
    list_filter = ('date',)
    ordering = ('date',)


@admin.register(CourseCalendarLog)
class CourseCalendarLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'actual_date', 'problems', 'solutions', 'created_at')
    list_filter = ('actual_date',)
    autocomplete_fields = ('calendar_entries',)
    readonly_fields = ('created_at',)
