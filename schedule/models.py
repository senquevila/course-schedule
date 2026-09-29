from django.db import models
from django.utils.dates import WEEKDAYS, WEEKDAYS_ABBR
from django.utils.translation import gettext_lazy as _


class CourseSchedule(models.Model):
    """Represents the recurring weekly pattern for a course"""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='schedules')
    days = models.JSONField(default=list, help_text="List of day numbers: 0=Sunday, 1=Monday, ..., 6=Saturday")
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses_courseschedule'
        ordering = ['course', 'start_time']
        verbose_name = 'Course Schedule'
        verbose_name_plural = 'Course Schedules'
        unique_together = ['course', 'start_time', 'end_time']

    def __str__(self):
        day_names = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
        days_str = ', '.join([day_names.get(d, str(d)) for d in sorted(self.days)])
        return f"{self.course} - {days_str} {self.start_time}-{self.end_time}"

    def get_days_display(self):
        """Return a human-readable string of the scheduled days"""
        return ', '.join(str(WEEKDAYS[(d - 1) % 7]) for d in sorted(self.days))  # 0=Sunday

    def get_days_short(self):
        """Return abbreviated day names"""
        return ', '.join(str(WEEKDAYS_ABBR[(d - 1) % 7]) for d in sorted(self.days))  # 0=Sunday


class LogStatus(models.TextChoices):
    NONE = 'none', _('No log')
    OK = 'ok', _('As scheduled')
    DELAYED = 'delayed', _('Delayed')
    MANY = 'many', _('Many logs')

    @property
    def style(self):
        """Inline CSS painting a calendar session; the colors are tokens in style.css"""
        return f'background: var(--status-{self.value}-bg); color: var(--status-{self.value}-fg);'


class CourseCalendar(models.Model):
    """Represents the original scheduled date/time for a course topic"""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    # Real topic: what this slot holds after delays re-flow the calendar
    topic = models.ForeignKey('courses.Topic', on_delete=models.SET_NULL, blank=True, null=True, related_name='sessions')
    # Ideal topic: what this slot would hold with no delays (Nth slot -> Nth topic by order)
    ideal_topic = models.ForeignKey('courses.Topic', on_delete=models.SET_NULL, blank=True, null=True, related_name='ideal_sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses_coursesession'
        ordering = ['session_date', 'start_time']
        verbose_name = 'Course Calendar'
        verbose_name_plural = 'Course Calendars'
        unique_together = ['course', 'session_date', 'start_time']
        indexes = [
            models.Index(fields=['session_date']),
            models.Index(fields=['course', 'session_date']),
        ]

    def __str__(self):
        topic_name = self.topic.name if self.topic else 'Unassigned'
        return f"{self.course} - {self.session_date} {self.start_time} ({topic_name})"

    @property
    def log_status(self):
        """Session's LogStatus; its colors live on LogStatus.style"""
        logs = list(self.logs.all())  # uses prefetch_related('logs') when present
        if not logs:
            return LogStatus.NONE
        if len(logs) > 1:
            return LogStatus.MANY
        actual = logs[0].actual_date
        return LogStatus.DELAYED if actual and actual > self.session_date else LogStatus.OK


class NonWorkingDay(models.Model):
    """A date on which no sessions should be scheduled (holiday, vacation, etc.)"""
    date = models.DateField(unique=True)
    reason = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'schedule_nonworkingday'
        ordering = ['date']
        verbose_name = 'Non-Working Day'
        verbose_name_plural = 'Non-Working Days'

    def __str__(self):
        return f"{self.date}" + (f" ({self.reason})" if self.reason else "")


class CourseCalendarLog(models.Model):
    """Records what actually happened for one or more scheduled CourseCalendar entries (delay, merge, etc.)"""
    calendar_entries = models.ManyToManyField(CourseCalendar, related_name='logs')
    actual_date = models.DateField(null=True, blank=True, help_text="Leave blank if it happened as scheduled")
    problems = models.TextField(blank=True, help_text="Any problems encountered (optional)")
    solutions = models.TextField(blank=True, help_text="How problems were resolved (optional)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'schedule_coursecalendarlog'
        ordering = ['-created_at']
        verbose_name = 'Course Calendar Log'
        verbose_name_plural = 'Course Calendar Logs'

    def __str__(self):
        return f"Log #{self.pk} ({self.actual_date or 'as scheduled'})"
