from django.contrib import admin
from .models import Period, Assignature, Course, Topic, Material, CourseSchedule, CourseSession


@admin.register(Period)
class PeriodAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'created_at')
    list_filter = ('start_date',)
    search_fields = ('name',)
    ordering = ('-start_date',)


@admin.register(Assignature)
class AssignatureAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'uv', 'created_at')
    list_filter = ('uv',)
    search_fields = ('code', 'name')
    ordering = ('code',)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'assignature', 'period', 'instructor_name', 'location', 'created_at')
    list_filter = ('period', 'assignature')
    search_fields = ('name', 'instructor_name', 'location')
    raw_id_fields = ('assignature', 'period')
    ordering = ('-created_at',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('code', 'name')
    raw_id_fields = ('course',)
    ordering = ('course', 'order')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'material_type', 'topic', 'created_at')
    list_filter = ('material_type', 'topic')
    search_fields = ('code', 'name')
    raw_id_fields = ('topic',)
    ordering = ('topic', 'code')


@admin.register(CourseSchedule)
class CourseScheduleAdmin(admin.ModelAdmin):
    list_display = ('course', 'get_day_of_week_display', 'start_time', 'end_time', 'created_at')
    list_filter = ('course', 'day_of_week')
    search_fields = ('course__name',)
    raw_id_fields = ('course',)
    ordering = ('course', 'day_of_week', 'start_time')


@admin.register(CourseSession)
class CourseSessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'session_date', 'start_time', 'end_time', 'topic', 'created_at')
    list_filter = ('session_date', 'course', 'topic')
    search_fields = ('course__name', 'topic__name')
    raw_id_fields = ('course', 'topic')
    ordering = ('-session_date', 'start_time')
    readonly_fields = ('created_at',)
