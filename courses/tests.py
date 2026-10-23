from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from schedule.models import CourseCalendarLog

from .models import Assignature, Course, Material, Period, Topic
from .syllabus_parser import SyllabusCSVError, parse_syllabus_csv


class ParseSyllabusCSVTestCase(TestCase):
    """Test the rigid CSV syllabus parser"""

    def test_parse_valid_csv(self):
        content = b"""code,name,description,order
T01,Introduction to Programming,Basic programming concepts,1
T02,Variables and Data Types,Understanding different data types,2
T03,Control Flow,if/else and loops,3"""

        topics = parse_syllabus_csv(content)

        self.assertEqual(len(topics), 3)
        self.assertEqual(
            topics[0],
            {
                "code": "T01",
                "name": "Introduction to Programming",
                "description": "Basic programming concepts",
                "order": 1,
            },
        )

    def test_empty_description_allowed(self):
        content = b"""code,name,description,order
T01,Introduction,,1"""

        topics = parse_syllabus_csv(content)
        self.assertEqual(topics[0]["description"], "")

    def test_wrong_header_rejected(self):
        content = b"""name,code,description,order
T01,Introduction,Basic concepts,1"""

        with self.assertRaises(SyllabusCSVError):
            parse_syllabus_csv(content)

    def test_missing_column_rejected(self):
        content = b"""code,name,order
T01,Introduction,1"""

        with self.assertRaises(SyllabusCSVError):
            parse_syllabus_csv(content)

    def test_missing_name_rejected(self):
        content = b"""code,name,description,order
T01,,No name here,1"""

        with self.assertRaisesMessage(SyllabusCSVError, "code and name are required"):
            parse_syllabus_csv(content)

    def test_invalid_order_rejected(self):
        content = b"""code,name,description,order
T01,Introduction,Basic concepts,not-a-number"""

        with self.assertRaisesMessage(SyllabusCSVError, "order must be a positive integer"):
            parse_syllabus_csv(content)

    def test_non_positive_order_rejected(self):
        content = b"""code,name,description,order
T01,Introduction,Basic concepts,0"""

        with self.assertRaisesMessage(SyllabusCSVError, "order must be a positive integer"):
            parse_syllabus_csv(content)

    def test_empty_file_rejected(self):
        with self.assertRaises(SyllabusCSVError):
            parse_syllabus_csv(b"")

    def test_blank_rows_skipped(self):
        content = b"""code,name,description,order
T01,Introduction,Basic concepts,1

T02,Advanced,More detail,2"""

        topics = parse_syllabus_csv(content)
        self.assertEqual(len(topics), 2)


class SyllabusUploadViewTestCase(TestCase):
    """Test the syllabus upload view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username="testuser", password="12345")

        period = Period.objects.create(name="Test Period", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code="CS101", name="Test Course", uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name="Test Section",
            period=period,
            instructor_name="Test Instructor",
            location="Test Location",
        )

        self.upload_url = reverse("courses:syllabus-upload", args=[self.course.id])

    def test_get_upload_form(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/syllabus_upload.html")

    def test_upload_valid_csv(self):
        content = b"""code,name,description,order
T01,Introduction to Programming,,1
T02,Variables and Data Types,,2
T03,Control Structures,,3"""

        file = SimpleUploadedFile("syllabus.csv", content, content_type="text/csv")
        response = self.client.post(self.upload_url, {"syllabus_file": file})

        self.assertEqual(response.status_code, 302)
        self.assertIn("review", response.url)
        self.assertEqual(len(self.client.session["extracted_topics"]), 3)

    def test_upload_non_csv_extension_rejected(self):
        file = SimpleUploadedFile("syllabus.txt", b"1. Topic", content_type="text/plain")
        response = self.client.post(self.upload_url, {"syllabus_file": file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Only .csv files are supported")

    def test_upload_wrong_header_rejected(self):
        content = b"""name,code,description,order
T01,Introduction,Basic,1"""
        file = SimpleUploadedFile("syllabus.csv", content, content_type="text/csv")
        response = self.client.post(self.upload_url, {"syllabus_file": file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "CSV must have columns: code,name,description,order")

    def test_upload_file_too_large(self):
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("large.csv", large_content, content_type="text/csv")

        response = self.client.post(self.upload_url, {"syllabus_file": file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "File size must not exceed 10MB")


class SyllabusReviewViewTestCase(TestCase):
    """Test the syllabus review and import functionality"""

    def setUp(self):
        self.client = Client()

        period = Period.objects.create(name="Test Period", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code="CS101", name="Test Course", uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name="Test Section",
            period=period,
            instructor_name="Test Instructor",
            location="Test Location",
        )

        self.review_url = reverse("courses:syllabus-review", args=[self.course.id])

        session = self.client.session
        session["extracted_topics"] = [
            {"code": "T01", "name": "Introduction to Programming", "description": "", "order": 1},
            {"code": "T02", "name": "Variables and Data Types", "description": "", "order": 2},
            {"code": "T03", "name": "Control Structures", "description": "", "order": 3},
        ]
        session.save()

    def test_get_review_form(self):
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "courses/syllabus_review.html")

    def test_import_selected_topics(self):
        data = {
            "topic_0_include": "on",
            "topic_0_code": "T01",
            "topic_0_name": "Introduction to Programming",
            "topic_0_description": "Learn the basics",
            "topic_0_order": "1",
            "topic_1_include": "on",
            "topic_1_code": "T02",
            "topic_1_name": "Variables and Data Types",
            "topic_1_description": "",
            "topic_1_order": "2",
            "topic_2_include": "",  # Not selected
            "topic_2_code": "T03",
            "topic_2_name": "Control Structures",
            "topic_2_description": "",
            "topic_2_order": "3",
        }

        response = self.client.post(self.review_url, data)

        self.assertEqual(response.status_code, 302)

        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 2)

        t01 = topics.get(code="T01")
        self.assertEqual(t01.name, "Introduction to Programming")
        self.assertEqual(t01.description, "Learn the basics")

    def test_import_with_no_topics_selected(self):
        data = {
            "topic_0_include": "",
            "topic_0_code": "T01",
            "topic_0_name": "Introduction to Programming",
            "topic_0_description": "",
            "topic_0_order": "1",
        }

        response = self.client.post(self.review_url, data)

        self.assertEqual(response.status_code, 200)
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 0)

    def test_import_preserves_order(self):
        data = {
            "topic_0_include": "on",
            "topic_0_code": "T01",
            "topic_0_name": "First Topic",
            "topic_0_order": "1",
            "topic_0_description": "",
            "topic_1_include": "on",
            "topic_1_code": "T02",
            "topic_1_name": "Second Topic",
            "topic_1_order": "2",
            "topic_1_description": "",
            "topic_2_include": "on",
            "topic_2_code": "T03",
            "topic_2_name": "Third Topic",
            "topic_2_order": "3",
            "topic_2_description": "",
        }

        self.client.post(self.review_url, data)

        topics = Topic.objects.filter(course=self.course).order_by("order")
        self.assertEqual(list(topics.values_list("name", flat=True)), ["First Topic", "Second Topic", "Third Topic"])


class TopicImportIntegrationTestCase(TestCase):
    """Integration tests for the complete CSV import workflow"""

    def setUp(self):
        self.client = Client()

        period = Period.objects.create(name="II PAC 2026", start_date=date(2026, 5, 1), end_date=date(2026, 8, 31))
        assignature = Assignature.objects.create(code="ISC-333", name="Sistemas Operativos I", uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name="Sección 1700",
            period=period,
            instructor_name="José Enrique Ávila",
            location="Room 101",
        )

    def test_complete_workflow(self):
        syllabus_content = b"""code,name,description,order
T01,Introduction to Programming,,1
T02,Variables and Data Types,,2
T03,Control Structures,,3
T04,Functions,,4
T05,Data Structures,,5"""

        file = SimpleUploadedFile("syllabus.csv", syllabus_content, content_type="text/csv")
        upload_url = reverse("courses:syllabus-upload", args=[self.course.id])

        response = self.client.post(upload_url, {"syllabus_file": file})
        self.assertEqual(response.status_code, 302)

        review_url = reverse("courses:syllabus-review", args=[self.course.id])

        extracted = self.client.session["extracted_topics"]
        self.assertEqual(len(extracted), 5)

        data = {}
        for i, topic in enumerate(extracted):
            data[f"topic_{i}_include"] = "on"
            data[f"topic_{i}_code"] = topic["code"]
            data[f"topic_{i}_name"] = topic["name"]
            data[f"topic_{i}_description"] = topic["description"]
            data[f"topic_{i}_order"] = str(topic["order"])

        response = self.client.post(review_url, data)
        self.assertEqual(response.status_code, 302)

        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 5)

        first_topic = topics.get(code="T01")
        self.assertEqual(first_topic.name, "Introduction to Programming")
        self.assertEqual(first_topic.order, 1)

    def test_edit_topics_before_import(self):
        syllabus_content = b"""code,name,description,order
T01,Topic One,,1
T02,Topic Two,,2"""

        file = SimpleUploadedFile("syllabus.csv", syllabus_content, content_type="text/csv")
        upload_url = reverse("courses:syllabus-upload", args=[self.course.id])

        self.client.post(upload_url, {"syllabus_file": file})

        review_url = reverse("courses:syllabus-review", args=[self.course.id])

        data = {
            "topic_0_include": "on",
            "topic_0_code": "T01",
            "topic_0_name": "Modified Topic One",
            "topic_0_description": "Added description",
            "topic_0_order": "1",
            "topic_1_include": "on",
            "topic_1_code": "T02",
            "topic_1_name": "Modified Topic Two",
            "topic_1_description": "",
            "topic_1_order": "2",
        }

        self.client.post(review_url, data)

        topic = Topic.objects.get(code="T01")
        self.assertEqual(topic.name, "Modified Topic One")
        self.assertEqual(topic.description, "Added description")


class TopicCodeGenerationTestCase(TestCase):
    """Test automatic topic code generation"""

    def setUp(self):
        period = Period.objects.create(name="Test Period", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code="TEST101", name="Test", uv=4)
        self.course = Course.objects.create(
            assignature=assignature, name="Test", period=period, instructor_name="Test", location="Test Location"
        )

    def test_code_format(self):
        topic = Topic.objects.create(course=self.course, code="T01", name="First Topic", order=1)
        self.assertEqual(topic.code, "T01")

    def test_sequential_codes(self):
        for i in range(1, 6):
            Topic.objects.create(course=self.course, code=f"T{i:02d}", name=f"Topic {i}", order=i)

        topics = Topic.objects.filter(course=self.course).order_by("order")
        codes = [t.code for t in topics]

        expected = ["T01", "T02", "T03", "T04", "T05"]
        self.assertEqual(codes, expected)


class CourseCalendarLogCreateViewTestCase(TestCase):
    """Saving a log re-flows the calendar after the log's date"""

    def setUp(self):
        from datetime import time

        from schedule.models import CourseSchedule

        period = Period.objects.create(name="P", start_date=date(2026, 9, 1), end_date=date(2026, 9, 30))
        assignature = Assignature.objects.create(code="CS101", name="Test Course", uv=4)
        self.course = Course.objects.create(assignature=assignature, name="S", period=period)
        CourseSchedule.objects.create(course=self.course, days=[6], start_time=time(8), end_time=time(9))
        for n in range(1, 5):
            Topic.objects.create(course=self.course, code=f"T{n}", name=f"T{n}", order=n)
        # Saturdays 5, 12, 19, 26 -> T1..T4
        self.client.post(reverse("courses:calendar-generate", args=[self.course.id]))

    def topics_by_day(self):
        from schedule.models import CourseCalendar

        return {
            s.session_date.day: s.topic and s.topic.name
            for s in CourseCalendar.objects.filter(course=self.course).select_related("topic")
        }

    def log(self, day, **data):
        from schedule.models import CourseCalendar

        session = CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, day))
        url = reverse("courses:calendar-log-create", args=[self.course.id, session.id])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, data)
        self.assertEqual(response["HX-Trigger"], "calendarChanged")
        self.assertEqual(session.logs.count(), 1)
        return response

    def test_as_scheduled_log_keeps_calendar(self):
        self.log(12, has_issues="no", problems="ignored")
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T4"})
        log = CourseCalendarLog.objects.get()
        self.assertEqual((log.actual_date, log.problems), (date(2026, 9, 12), ""))

    def test_delay_onto_class_day_shifts_following_topics(self):
        self.log(12, has_issues="yes", actual_date="2026-09-19")
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T2", 26: "T3"})

    def test_calendar_shows_delayed_topic_once(self):
        self.log(12, has_issues="yes", actual_date="2026-09-19")
        response = self.client.get(reverse("courses:calendar-list", args=[self.course.id]), {"year": 2026, "month": 9})
        delays = {s.session_date.day: s.is_delay for week in response.context["weeks"] for _, day in week for s in day}
        self.assertEqual(delays, {5: False, 12: False, 19: True, 26: False})

    def test_regenerate_keeps_delays(self):
        self.log(12, has_issues="yes", actual_date="2026-09-19")
        self.client.post(reverse("courses:calendar-generate", args=[self.course.id]))
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T2", 26: "T3"})

    def test_later_log_on_earlier_session_keeps_delay(self):
        self.log(19, has_issues="yes", actual_date="2026-09-26")
        self.log(12, has_issues="no")
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T3"})

    def test_delay_onto_off_day_keeps_following_topics(self):
        self.log(12, has_issues="yes", actual_date="2026-09-14")
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T4"})

    def test_early_log_frees_its_slot(self):
        from schedule.models import CourseCalendar

        self.log(19, has_issues="yes", actual_date="2026-09-12")
        slots = CourseCalendar.objects.filter(course=self.course).exclude(logs__isnull=False)
        self.assertEqual(
            {s.session_date.day: s.topic and s.topic.name for s in slots}, {5: "T1", 12: "T2", 19: "T4", 26: None}
        )
        response = self.client.get(reverse("courses:calendar-list", args=[self.course.id]), {"year": 2026, "month": 9})
        shown = {
            (d, s.topic and s.topic.name, tuple(o.topic.name for o in s.others))
            for week in response.context["weeks"]
            for d, day in week
            for s in day
        }
        self.assertEqual(shown, {(5, "T1", ()), (12, "T2", ("T3",)), (19, "T4", ()), (26, None, ())})
        self.assertContains(response, "calendar-session-badge")
        t2 = CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, 12))
        detail = self.client.get(reverse("courses:calendar-session-detail", args=[self.course.id, t2.id]))
        self.assertEqual([o.topic.name for o in detail.context["others"]], ["T3"])

        log = CourseCalendarLog.objects.get()
        self.client.post(reverse("courses:calendar-log-edit", args=[self.course.id, log.id]), {"has_issues": "no"})
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T4"})

    def test_delays_view(self):
        self.log(5, has_issues="no")
        self.log(12, has_issues="yes", actual_date="2026-09-15")
        response = self.client.get(reverse("courses:calendar-delays", args=[self.course.id]))
        self.assertEqual([row["delay"] for row in response.context["rows"]], [0, 3])
        self.assertEqual((response.context["current_delay"], response.context["total_delay"]), (3, 3))

    def test_log_status_colors(self):
        from schedule.models import CourseCalendar, LogStatus

        self.log(5, has_issues="no")
        self.log(12, has_issues="yes", actual_date="2026-09-15")
        self.log(19, has_issues="no")
        extra = CourseCalendarLog.objects.create(actual_date=date(2026, 9, 20))
        extra.calendar_entries.add(CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, 19)))
        statuses = {s.session_date.day: s.log_status for s in CourseCalendar.objects.filter(course=self.course)}
        self.assertEqual(statuses, {5: LogStatus.OK, 12: LogStatus.DELAYED, 19: LogStatus.MANY, 26: LogStatus.NONE})
        self.assertIn("--status-delayed-bg", statuses[12].style)

    def test_edit_and_delete_log(self):
        from schedule.models import CourseCalendar

        self.log(12, has_issues="yes", actual_date="2026-09-19")
        log = CourseCalendarLog.objects.get()
        list_url = reverse("courses:calendar-log-list", args=[self.course.id])
        self.assertEqual(list(self.client.get(list_url).context["logs"]), [log])

        edit_url = reverse("courses:calendar-log-edit", args=[self.course.id, log.id])
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        response = self.client.post(edit_url, {"has_issues": "no"})
        self.assertEqual(response["HX-Refresh"], "true")
        log.refresh_from_db()
        self.assertEqual(log.actual_date, date(2026, 9, 12))
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T4"})

        self.client.post(edit_url, {"has_issues": "yes", "actual_date": "2026-09-19"})
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T2", 26: "T3"})

        self.client.delete(reverse("courses:calendar-log-delete", args=[self.course.id, log.id]))
        self.assertFalse(CourseCalendarLog.objects.exists())
        self.assertEqual(self.topics_by_day(), {5: "T1", 12: "T2", 19: "T3", 26: "T4"})
        self.assertFalse(CourseCalendar.objects.filter(course=self.course, logs__isnull=False).exists())

    def test_topic_progress_and_lost_topics(self):
        from .views import _topic_progress

        self.log(12, has_issues="yes", actual_date="2026-09-19")  # T4 pushed off the calendar
        progress = _topic_progress(self.course, date(2026, 9, 19))
        self.assertEqual((progress["current_topic"].name, progress["ideal_topic"].name), ("T2", "T3"))
        self.assertEqual(progress["topics_behind"], 1)
        self.assertEqual([t.name for t in progress["lost_topics"]], ["T4"])
        response = self.client.get(reverse("courses:topic-list", args=[self.course.id]))
        self.assertContains(response, "T4")

    def test_session_ideal_topic(self):
        from schedule.models import CourseCalendar

        self.log(12, has_issues="yes", actual_date="2026-09-19")
        session = CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, 26))
        self.assertEqual((session.topic.name, session.ideal_topic.name), ("T3", "T4"))
        url = reverse("courses:calendar-session-detail", args=[self.course.id, session.id])
        self.assertContains(self.client.get(url), "T4")


class TopicMoveViewTestCase(TestCase):
    def setUp(self):
        period = Period.objects.create(name="P", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code="CS101", name="Test", uv=4)
        self.course = Course.objects.create(
            assignature=assignature, name="Test", period=period, instructor_name="Test", location="Test"
        )
        self.topics = [
            Topic.objects.create(course=self.course, code=f"T{i}", name=f"T{i}", order=i) for i in range(1, 6)
        ]

    def move(self, topic, order):
        self.client.post(reverse("courses:topic-move", args=[self.course.id, topic.id]), {"order": order})
        return [(t.name, t.order) for t in Topic.objects.filter(course=self.course).order_by("order")]

    def test_reorder_modal(self):
        url = reverse("courses:topic-move", args=[self.course.id, self.topics[1].id])
        self.assertContains(self.client.get(url), 'name="order"')

    def test_move_up_shifts_following_topics(self):
        self.assertEqual(self.move(self.topics[4], 2), [("T1", 1), ("T5", 2), ("T2", 3), ("T3", 4), ("T4", 5)])

    def test_move_down_and_clamp(self):
        self.assertEqual(self.move(self.topics[0], 99), [("T2", 1), ("T3", 2), ("T4", 3), ("T5", 4), ("T1", 5)])

    def test_move_reflows_calendar(self):
        from schedule.models import CourseCalendar

        for day in (1, 2):
            CourseCalendar.objects.create(
                course=self.course,
                session_date=date(2026, 9, day),
                day_of_week=0,
                start_time="08:00",
                end_time="09:00",
                topic=self.topics[day - 1],
            )
        self.move(self.topics[2], 1)
        sessions = CourseCalendar.objects.filter(course=self.course).order_by("session_date")
        self.assertEqual([(s.topic.name, s.ideal_topic.name) for s in sessions], [("T3", "T3"), ("T1", "T1")])

    def test_move_with_logs_only_reflows_unlogged_sessions(self):
        from schedule.models import CourseCalendar

        for day in (1, 2, 3):
            CourseCalendar.objects.create(
                course=self.course,
                session_date=date(2026, 9, day),
                day_of_week=0,
                start_time="08:00",
                end_time="09:00",
                topic=self.topics[day - 1],
                ideal_topic=self.topics[day - 1],
            )
        logged = CourseCalendar.objects.get(session_date=date(2026, 9, 1))
        CourseCalendarLog.objects.create().calendar_entries.add(logged)
        self.move(self.topics[4], 1)
        sessions = CourseCalendar.objects.filter(course=self.course).order_by("session_date")
        # Logged session keeps T1 as topic and ideal; the rest take the new order, skipping T1
        self.assertEqual(
            [(s.topic.name, s.ideal_topic.name) for s in sessions], [("T1", "T1"), ("T5", "T1"), ("T2", "T2")]
        )


class ListQueryCountTestCase(TestCase):
    """List pages run the same number of queries however many rows they show (no N+1)"""

    def setUp(self):
        today = timezone.localdate()
        self.period = Period.objects.create(
            name="Now", start_date=today - timedelta(days=30), end_date=today + timedelta(days=30)
        )
        self.assignature = Assignature.objects.create(code="CS101", name="Test", uv=4)
        self.course = self._add_course("A")

    def _add_course(self, name):
        course = Course.objects.create(assignature=self.assignature, period=self.period, name=name)
        self._add_topics(course, 1, 2)
        return course

    def _add_topics(self, course, first, last):
        for order in range(first, last + 1):
            topic = Topic.objects.create(course=course, code=f"T{order}", name=f"Topic {order}", order=order)
            Material.objects.create(topic=topic, code="M1", name="Slides", material_type="url", url_or_path="x")

    def assertQueriesDontGrow(self, url, add_rows):
        with CaptureQueriesContext(connection) as before:
            self.client.get(url)
        add_rows()
        with CaptureQueriesContext(connection) as after:
            self.client.get(url)
        self.assertEqual(len(before), len(after))

    def test_topic_list(self):
        self.assertQueriesDontGrow(
            reverse("courses:topic-list", args=[self.course.pk]), lambda: self._add_topics(self.course, 3, 8)
        )

    def test_course_list(self):
        self.assertQueriesDontGrow(reverse("courses:course-list"), lambda: [self._add_course(n) for n in "BCD"])

    def test_home(self):
        self.assertQueriesDontGrow(reverse("courses:home"), lambda: [self._add_course(n) for n in "BCD"])
