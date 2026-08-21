from django.db import models


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
        return f"{self.course.name} - {days_str} {self.start_time}-{self.end_time}"

    def get_days_display(self):
        """Return a human-readable string of the scheduled days"""
        day_names = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
        return ', '.join([day_names[d] for d in sorted(self.days)])

    def get_days_short(self):
        """Return abbreviated day names"""
        day_names = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        return ', '.join([day_names[d] for d in sorted(self.days)])


class CourseSession(models.Model):
    """Represents a specific course session instance on a particular date"""
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.ForeignKey('courses.Topic', on_delete=models.SET_NULL, blank=True, null=True, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'courses_coursesession'
        ordering = ['session_date', 'start_time']
        verbose_name = 'Course Session'
        verbose_name_plural = 'Course Sessions'
        unique_together = ['course', 'session_date', 'start_time']
        indexes = [
            models.Index(fields=['session_date']),
            models.Index(fields=['course', 'session_date']),
        ]

    def __str__(self):
        topic_name = self.topic.name if self.topic else 'Unassigned'
        return f"{self.course.name} - {self.session_date} {self.start_time} ({topic_name})"
