from django.contrib import admin
from .models import Period, Assignature, Course, Topic, Material


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
    autocomplete_fields = ('assignature', 'period')
    ordering = ('-created_at',)


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'course', 'order', 'created_at')
    list_filter = ('course',)
    search_fields = ('code', 'name')
    autocomplete_fields = ('course',)
    ordering = ('course', 'order')


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'material_type', 'topic', 'created_at')
    list_filter = ('material_type', 'topic')
    search_fields = ('code', 'name')
    autocomplete_fields = ('topic',)
    ordering = ('topic', 'code')
