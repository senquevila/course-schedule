from django.db import models


class Period(models.Model):
    """Represents a 3-month teaching period (e.g., Spring 2026, Fall 2026)"""
    name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Period'
        verbose_name_plural = 'Periods'

    def __str__(self):
        return f"{self.name} ({self.start_date} - {self.end_date})"


class Assignature(models.Model):
    """Represents a course subject/discipline with standard weekly hours"""
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=255)
    uv = models.IntegerField(help_text="Hours per week")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['code']
        verbose_name = 'Assignature'
        verbose_name_plural = 'Assignatures'

    def __str__(self):
        return f"{self.code} - {self.name}"


class Course(models.Model):
    """Represents a specific instance of an assignature taught in a period"""
    assignature = models.ForeignKey(Assignature, on_delete=models.CASCADE)
    period = models.ForeignKey(Period, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    instructor_name = models.CharField(max_length=255, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['period', 'name']
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'
        unique_together = ['assignature', 'name', 'period']

    def __str__(self):
        return f"{self.name} ({self.period.name})"


class Topic(models.Model):
    """Represents a teaching topic within a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='topics')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    order = models.IntegerField(help_text="Sequence position within course")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['course', 'order']
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'
        unique_together = ['course', 'order']

    def __str__(self):
        return f"{self.code} - {self.name}"


class Material(models.Model):
    """Represents teaching materials attached to a topic"""
    MATERIAL_TYPES = [
        ('pdf', 'PDF'),
        ('url', 'URL'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('document', 'Document'),
    ]

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='materials')
    code = models.CharField(max_length=50)
    name = models.CharField(max_length=255)
    material_type = models.CharField(max_length=50, choices=MATERIAL_TYPES)
    url_or_path = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['topic', 'code']
        verbose_name = 'Material'
        verbose_name_plural = 'Materials'

    def __str__(self):
        return f"{self.code} - {self.name}"


class CourseSchedule(models.Model):
    """Represents the recurring weekly pattern for a course"""
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='schedules')
    days = models.JSONField(default=list, help_text="List of day numbers: 0=Sunday, 1=Monday, ..., 6=Saturday")
    start_time = models.TimeField()
    end_time = models.TimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='sessions')
    session_date = models.DateField()
    day_of_week = models.IntegerField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, blank=True, null=True, related_name='sessions')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
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
