from datetime import date, time

from django.test import TestCase, Client
from django.urls import reverse

from courses.models import Assignature, Period, Course
from .models import CourseSchedule, CourseCalendar, CourseCalendarLog, NonWorkingDay


class CourseCalendarGenerateViewTestCase(TestCase):
    """Regenerating the calendar must skip non-working days and never touch
    sessions that already have a CourseCalendarLog."""

    def setUp(self):
        self.client = Client()
        assignature = Assignature.objects.create(code='A1', name='Assignature 1', uv=4)
        period = Period.objects.create(
            name='Period 1', start_date=date(2026, 1, 5), end_date=date(2026, 1, 16)
        )
        self.course = Course.objects.create(assignature=assignature, name='Course 1', period=period)
        # Mon(2026-01-05,12,19), Tue(2026-01-06,13), etc. Schedule: Mon+Wed 19:00-20:00
        self.schedule = CourseSchedule.objects.create(
            course=self.course, days=[1, 3], start_time=time(19, 0), end_time=time(20, 0)
        )
        self.url = reverse(
            'courses:schedule-generate-calendar',
            args=[self.course.id, self.schedule.id],
        )

    def generate(self):
        return self.client.post(self.url)

    def test_generates_sessions_for_matching_days(self):
        self.generate()
        dates = set(
            CourseCalendar.objects.filter(course=self.course).values_list('session_date', flat=True)
        )
        # Mondays/Wednesdays between 2026-01-05 and 2026-01-16
        self.assertEqual(
            dates,
            {date(2026, 1, 5), date(2026, 1, 7), date(2026, 1, 12), date(2026, 1, 14)},
        )

    def test_non_working_day_is_skipped(self):
        NonWorkingDay.objects.create(date=date(2026, 1, 7), reason='Holiday')
        self.generate()
        dates = set(
            CourseCalendar.objects.filter(course=self.course).values_list('session_date', flat=True)
        )
        self.assertNotIn(date(2026, 1, 7), dates)
        self.assertEqual(
            dates, {date(2026, 1, 5), date(2026, 1, 12), date(2026, 1, 14)}
        )

    def test_repeated_generation_preserves_logged_session(self):
        self.generate()
        logged_session = CourseCalendar.objects.get(session_date=date(2026, 1, 5))
        log = CourseCalendarLog.objects.create(description='Ran late')
        log.calendar_entries.add(logged_session)

        # Mark 2026-01-05 as a non-working day: it should stay untouched because it's logged.
        NonWorkingDay.objects.create(date=date(2026, 1, 5), reason='Holiday')
        self.generate()

        self.assertTrue(CourseCalendar.objects.filter(pk=logged_session.pk).exists())
        dates = set(
            CourseCalendar.objects.filter(course=self.course).values_list('session_date', flat=True)
        )
        self.assertIn(date(2026, 1, 5), dates)
        self.assertEqual(
            dates, {date(2026, 1, 5), date(2026, 1, 7), date(2026, 1, 12), date(2026, 1, 14)}
        )

    def test_pressing_generate_multiple_times_is_idempotent(self):
        self.generate()
        self.generate()
        self.generate()
        count = CourseCalendar.objects.filter(course=self.course).count()
        self.assertEqual(count, 4)
