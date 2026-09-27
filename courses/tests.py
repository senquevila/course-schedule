from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from .models import Period, Assignature, Course, Topic
from schedule.models import CourseCalendarLog
from .syllabus_parser import parse_syllabus_csv, SyllabusCSVError


class ParseSyllabusCSVTestCase(TestCase):
    """Test the rigid CSV syllabus parser"""

    def test_parse_valid_csv(self):
        content = b"""code,name,description,order
T01,Introduction to Programming,Basic programming concepts,1
T02,Variables and Data Types,Understanding different data types,2
T03,Control Flow,if/else and loops,3"""

        topics = parse_syllabus_csv(content)

        self.assertEqual(len(topics), 3)
        self.assertEqual(topics[0], {
            'code': 'T01',
            'name': 'Introduction to Programming',
            'description': 'Basic programming concepts',
            'order': 1,
        })

    def test_empty_description_allowed(self):
        content = b"""code,name,description,order
T01,Introduction,,1"""

        topics = parse_syllabus_csv(content)
        self.assertEqual(topics[0]['description'], '')

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

        with self.assertRaisesMessage(SyllabusCSVError, 'code and name are required'):
            parse_syllabus_csv(content)

    def test_invalid_order_rejected(self):
        content = b"""code,name,description,order
T01,Introduction,Basic concepts,not-a-number"""

        with self.assertRaisesMessage(SyllabusCSVError, 'order must be a positive integer'):
            parse_syllabus_csv(content)

    def test_non_positive_order_rejected(self):
        content = b"""code,name,description,order
T01,Introduction,Basic concepts,0"""

        with self.assertRaisesMessage(SyllabusCSVError, 'order must be a positive integer'):
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
        self.user = User.objects.create_user(username='testuser', password='12345')

        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code='CS101', name='Test Course', uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test Section',
            period=period,
            instructor_name='Test Instructor',
            location='Test Location'
        )

        self.upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

    def test_get_upload_form(self):
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/syllabus_upload.html')

    def test_upload_valid_csv(self):
        content = b"""code,name,description,order
T01,Introduction to Programming,,1
T02,Variables and Data Types,,2
T03,Control Structures,,3"""

        file = SimpleUploadedFile("syllabus.csv", content, content_type="text/csv")
        response = self.client.post(self.upload_url, {'syllabus_file': file})

        self.assertEqual(response.status_code, 302)
        self.assertIn('review', response.url)
        self.assertEqual(len(self.client.session['extracted_topics']), 3)

    def test_upload_non_csv_extension_rejected(self):
        file = SimpleUploadedFile("syllabus.txt", b"1. Topic", content_type="text/plain")
        response = self.client.post(self.upload_url, {'syllabus_file': file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Only .csv files are supported')

    def test_upload_wrong_header_rejected(self):
        content = b"""name,code,description,order
T01,Introduction,Basic,1"""
        file = SimpleUploadedFile("syllabus.csv", content, content_type="text/csv")
        response = self.client.post(self.upload_url, {'syllabus_file': file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'CSV must have columns: code,name,description,order')

    def test_upload_file_too_large(self):
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile("large.csv", large_content, content_type="text/csv")

        response = self.client.post(self.upload_url, {'syllabus_file': file})

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'File size must not exceed 10MB')


class SyllabusReviewViewTestCase(TestCase):
    """Test the syllabus review and import functionality"""

    def setUp(self):
        self.client = Client()

        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code='CS101', name='Test Course', uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test Section',
            period=period,
            instructor_name='Test Instructor',
            location='Test Location'
        )

        self.review_url = reverse('courses:syllabus-review', args=[self.course.id])

        session = self.client.session
        session['extracted_topics'] = [
            {'code': 'T01', 'name': 'Introduction to Programming', 'description': '', 'order': 1},
            {'code': 'T02', 'name': 'Variables and Data Types', 'description': '', 'order': 2},
            {'code': 'T03', 'name': 'Control Structures', 'description': '', 'order': 3},
        ]
        session.save()

    def test_get_review_form(self):
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/syllabus_review.html')

    def test_import_selected_topics(self):
        data = {
            'topic_0_include': 'on',
            'topic_0_code': 'T01',
            'topic_0_name': 'Introduction to Programming',
            'topic_0_description': 'Learn the basics',
            'topic_0_order': '1',

            'topic_1_include': 'on',
            'topic_1_code': 'T02',
            'topic_1_name': 'Variables and Data Types',
            'topic_1_description': '',
            'topic_1_order': '2',

            'topic_2_include': '',  # Not selected
            'topic_2_code': 'T03',
            'topic_2_name': 'Control Structures',
            'topic_2_description': '',
            'topic_2_order': '3',
        }

        response = self.client.post(self.review_url, data)

        self.assertEqual(response.status_code, 302)

        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 2)

        t01 = topics.get(code='T01')
        self.assertEqual(t01.name, 'Introduction to Programming')
        self.assertEqual(t01.description, 'Learn the basics')

    def test_import_with_no_topics_selected(self):
        data = {
            'topic_0_include': '',
            'topic_0_code': 'T01',
            'topic_0_name': 'Introduction to Programming',
            'topic_0_description': '',
            'topic_0_order': '1',
        }

        response = self.client.post(self.review_url, data)

        self.assertEqual(response.status_code, 200)
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 0)

    def test_import_preserves_order(self):
        data = {
            'topic_0_include': 'on',
            'topic_0_code': 'T01',
            'topic_0_name': 'First Topic',
            'topic_0_order': '1',
            'topic_0_description': '',

            'topic_1_include': 'on',
            'topic_1_code': 'T02',
            'topic_1_name': 'Second Topic',
            'topic_1_order': '2',
            'topic_1_description': '',

            'topic_2_include': 'on',
            'topic_2_code': 'T03',
            'topic_2_name': 'Third Topic',
            'topic_2_order': '3',
            'topic_2_description': '',
        }

        self.client.post(self.review_url, data)

        topics = Topic.objects.filter(course=self.course).order_by('order')
        self.assertEqual(
            list(topics.values_list('name', flat=True)),
            ['First Topic', 'Second Topic', 'Third Topic']
        )


class TopicImportIntegrationTestCase(TestCase):
    """Integration tests for the complete CSV import workflow"""

    def setUp(self):
        self.client = Client()

        period = Period.objects.create(name='II PAC 2026', start_date=date(2026, 5, 1), end_date=date(2026, 8, 31))
        assignature = Assignature.objects.create(code='ISC-333', name='Sistemas Operativos I', uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name='Sección 1700',
            period=period,
            instructor_name='José Enrique Ávila',
            location='Room 101'
        )

    def test_complete_workflow(self):
        syllabus_content = b"""code,name,description,order
T01,Introduction to Programming,,1
T02,Variables and Data Types,,2
T03,Control Structures,,3
T04,Functions,,4
T05,Data Structures,,5"""

        file = SimpleUploadedFile("syllabus.csv", syllabus_content, content_type="text/csv")
        upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

        response = self.client.post(upload_url, {'syllabus_file': file})
        self.assertEqual(response.status_code, 302)

        review_url = reverse('courses:syllabus-review', args=[self.course.id])

        extracted = self.client.session['extracted_topics']
        self.assertEqual(len(extracted), 5)

        data = {}
        for i, topic in enumerate(extracted):
            data[f'topic_{i}_include'] = 'on'
            data[f'topic_{i}_code'] = topic['code']
            data[f'topic_{i}_name'] = topic['name']
            data[f'topic_{i}_description'] = topic['description']
            data[f'topic_{i}_order'] = str(topic['order'])

        response = self.client.post(review_url, data)
        self.assertEqual(response.status_code, 302)

        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 5)

        first_topic = topics.get(code='T01')
        self.assertEqual(first_topic.name, 'Introduction to Programming')
        self.assertEqual(first_topic.order, 1)

    def test_edit_topics_before_import(self):
        syllabus_content = b"""code,name,description,order
T01,Topic One,,1
T02,Topic Two,,2"""

        file = SimpleUploadedFile("syllabus.csv", syllabus_content, content_type="text/csv")
        upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

        self.client.post(upload_url, {'syllabus_file': file})

        review_url = reverse('courses:syllabus-review', args=[self.course.id])

        data = {
            'topic_0_include': 'on',
            'topic_0_code': 'T01',
            'topic_0_name': 'Modified Topic One',
            'topic_0_description': 'Added description',
            'topic_0_order': '1',

            'topic_1_include': 'on',
            'topic_1_code': 'T02',
            'topic_1_name': 'Modified Topic Two',
            'topic_1_description': '',
            'topic_1_order': '2',
        }

        self.client.post(review_url, data)

        topic = Topic.objects.get(code='T01')
        self.assertEqual(topic.name, 'Modified Topic One')
        self.assertEqual(topic.description, 'Added description')


class TopicCodeGenerationTestCase(TestCase):
    """Test automatic topic code generation"""

    def setUp(self):
        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(code='TEST101', name='Test', uv=4)
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test',
            period=period,
            instructor_name='Test',
            location='Test Location'
        )

    def test_code_format(self):
        topic = Topic.objects.create(course=self.course, code='T01', name='First Topic', order=1)
        self.assertEqual(topic.code, 'T01')

    def test_sequential_codes(self):
        for i in range(1, 6):
            Topic.objects.create(course=self.course, code=f'T{i:02d}', name=f'Topic {i}', order=i)

        topics = Topic.objects.filter(course=self.course).order_by('order')
        codes = [t.code for t in topics]

        expected = ['T01', 'T02', 'T03', 'T04', 'T05']
        self.assertEqual(codes, expected)


class CourseCalendarLogCreateViewTestCase(TestCase):
    """Saving a log re-flows the calendar after the log's date"""

    def setUp(self):
        from datetime import time
        from schedule.models import CourseSchedule

        period = Period.objects.create(name='P', start_date=date(2026, 9, 1), end_date=date(2026, 9, 30))
        assignature = Assignature.objects.create(code='CS101', name='Test Course', uv=4)
        self.course = Course.objects.create(assignature=assignature, name='S', period=period)
        CourseSchedule.objects.create(course=self.course, days=[6], start_time=time(8), end_time=time(9))
        for n in range(1, 5):
            Topic.objects.create(course=self.course, code=f'T{n}', name=f'T{n}', order=n)
        # Saturdays 5, 12, 19, 26 -> T1..T4
        self.client.post(reverse('courses:calendar-generate', args=[self.course.id]))

    def topics_by_day(self):
        from schedule.models import CourseCalendar
        return {
            s.session_date.day: s.topic and s.topic.name
            for s in CourseCalendar.objects.filter(course=self.course).select_related('topic')
        }

    def log(self, day, **data):
        from schedule.models import CourseCalendar
        session = CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, day))
        url = reverse('courses:calendar-log-create', args=[self.course.id, session.id])
        self.assertEqual(self.client.get(url).status_code, 200)
        response = self.client.post(url, data)
        self.assertEqual(response['HX-Trigger'], 'calendarChanged')
        self.assertEqual(session.logs.count(), 1)
        return response

    def test_as_scheduled_log_keeps_calendar(self):
        self.log(12, has_issues='no', problems='ignored')
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T3', 26: 'T4'})
        log = CourseCalendarLog.objects.get()
        self.assertEqual((log.actual_date, log.problems), (date(2026, 9, 12), ''))

    def test_delay_onto_class_day_shifts_following_topics(self):
        self.log(12, has_issues='yes', actual_date='2026-09-19')
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T2', 26: 'T3'})

    def test_delay_onto_off_day_keeps_following_topics(self):
        self.log(12, has_issues='yes', actual_date='2026-09-14')
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T3', 26: 'T4'})

    def test_delays_view(self):
        self.log(5, has_issues='no')
        self.log(12, has_issues='yes', actual_date='2026-09-15')
        response = self.client.get(reverse('courses:calendar-delays', args=[self.course.id]))
        self.assertEqual([row['delay'] for row in response.context['rows']], [0, 3])
        self.assertEqual((response.context['current_delay'], response.context['total_delay']), (3, 3))

    def test_log_status_colors(self):
        from schedule.models import CourseCalendar, LogStatus
        self.log(5, has_issues='no')
        self.log(12, has_issues='yes', actual_date='2026-09-15')
        self.log(19, has_issues='no')
        extra = CourseCalendarLog.objects.create(actual_date=date(2026, 9, 20))
        extra.calendar_entries.add(CourseCalendar.objects.get(course=self.course, session_date=date(2026, 9, 19)))
        statuses = {s.session_date.day: s.log_status for s in CourseCalendar.objects.filter(course=self.course)}
        self.assertEqual(statuses, {5: LogStatus.OK, 12: LogStatus.DELAYED, 19: LogStatus.MANY, 26: LogStatus.NONE})
        self.assertIn("--status-delayed-bg", statuses[12].style)

    def test_edit_and_delete_log(self):
        from schedule.models import CourseCalendar
        self.log(12, has_issues='yes', actual_date='2026-09-19')
        log = CourseCalendarLog.objects.get()
        list_url = reverse('courses:calendar-log-list', args=[self.course.id])
        self.assertEqual(list(self.client.get(list_url).context['logs']), [log])

        edit_url = reverse('courses:calendar-log-edit', args=[self.course.id, log.id])
        self.assertEqual(self.client.get(edit_url).status_code, 200)
        response = self.client.post(edit_url, {'has_issues': 'no'})
        self.assertEqual(response['HX-Refresh'], 'true')
        log.refresh_from_db()
        self.assertEqual(log.actual_date, date(2026, 9, 12))
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T3', 26: 'T4'})

        self.client.post(edit_url, {'has_issues': 'yes', 'actual_date': '2026-09-19'})
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T2', 26: 'T3'})

        self.client.delete(reverse('courses:calendar-log-delete', args=[self.course.id, log.id]))
        self.assertFalse(CourseCalendarLog.objects.exists())
        self.assertEqual(self.topics_by_day(), {5: 'T1', 12: 'T2', 19: 'T3', 26: 'T4'})
        self.assertFalse(CourseCalendar.objects.filter(course=self.course, logs__isnull=False).exists())
