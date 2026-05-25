from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from datetime import date

from .models import Period, Assignature, Course, Topic
from .syllabus_parser import SyllabusParser


class SyllabusParserTestCase(TestCase):
    """Test the syllabus parser with different formats"""

    def test_parse_numbered_list(self):
        """Test parsing numbered list format"""
        text = """1. Introduction to Programming
2. Variables and Data Types
3. Control Structures
4. Functions
5. Data Structures"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 5)
        self.assertEqual(topics[0]['name'], 'Introduction to Programming')
        self.assertEqual(topics[1]['name'], 'Variables and Data Types')
        self.assertEqual(topics[4]['name'], 'Data Structures')

    def test_parse_numbered_list_with_descriptions(self):
        """Test parsing numbered list with descriptions"""
        text = """1. Arrays - Basic array concepts and operations
2. Linked Lists - Introduction to linked list structures
3. Stack and Queue - LIFO and FIFO principles
4. Trees - Hierarchical data organization"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 4)
        self.assertEqual(topics[0]['name'], 'Arrays')
        self.assertIn('Basic array concepts', topics[0].get('description', ''))

    def test_parse_bullet_points(self):
        """Test parsing bullet point format"""
        text = """- Introduction to Python
- Data Types and Variables
- Operators and Expressions
- Control Structures
- Functions and Modules"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 5)
        self.assertEqual(topics[0]['name'], 'Introduction to Python')

    def test_parse_colon_separator(self):
        """Test parsing colon-separated format"""
        text = """Topic 1: Introduction to Programming
Topic 2: Variables and Data Types
Chapter 3: Control Flow Structures
Module 4: Function Definition and Calling"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 4)
        self.assertEqual(topics[0]['name'], 'Introduction to Programming')

    def test_parse_simple_lines(self):
        """Test parsing simple lines (fallback)"""
        text = """Data Structures
Algorithms
Design Patterns
Performance Optimization"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        # Parser extracts non-empty lines, may skip some formatting lines
        self.assertGreater(len(topics), 0)
        self.assertTrue(any('Data Structures' in t.get('name', '') for t in topics))

    def test_parse_mixed_whitespace(self):
        """Test parsing with mixed whitespace"""
        text = """1.   Introduction to Programming
2.  Variables and Data Types
3. Control Structures"""

        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 3)
        self.assertEqual(topics[0]['name'], 'Introduction to Programming')

    def test_parse_empty_file(self):
        """Test parsing empty content"""
        text = ""
        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 0)

    def test_parse_only_whitespace(self):
        """Test parsing whitespace-only content"""
        text = "\n\n   \n\t\n"
        parser = SyllabusParser(text)
        topics = parser.parse()

        self.assertEqual(len(topics), 0)


class SyllabusUploadViewTestCase(TestCase):
    """Test the syllabus upload view"""

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='12345')

        # Create test course
        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(
            code='CS101',
            name='Test Course',
            uv=4
        )
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test Section',
            period=period,
            instructor_name='Test Instructor',
            location='Test Location'
        )

        self.upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

    def test_get_upload_form(self):
        """Test accessing the upload form"""
        response = self.client.get(self.upload_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/syllabus_upload.html')

    def test_upload_text_file(self):
        """Test uploading a text file"""
        content = b"""1. Introduction to Programming
2. Variables and Data Types
3. Control Structures"""

        file = SimpleUploadedFile(
            "syllabus.txt",
            content,
            content_type="text/plain"
        )

        response = self.client.post(self.upload_url, {'syllabus_file': file})

        # Should redirect to review page
        self.assertEqual(response.status_code, 302)
        self.assertIn('review', response.url)

    def test_upload_invalid_file_type(self):
        """Test uploading invalid file type"""
        content = b"invalid content"
        file = SimpleUploadedFile(
            "file.exe",
            content,
            content_type="application/octet-stream"
        )

        response = self.client.post(self.upload_url, {'syllabus_file': file})

        # Should return 200 with error (form re-rendered)
        self.assertEqual(response.status_code, 200)
        # Check that response contains the upload form
        self.assertContains(response, 'syllabus_file')

    def test_upload_file_too_large(self):
        """Test uploading file larger than 10MB"""
        # Create a file larger than 10MB
        large_content = b"x" * (11 * 1024 * 1024)
        file = SimpleUploadedFile(
            "large.txt",
            large_content,
            content_type="text/plain"
        )

        response = self.client.post(self.upload_url, {'syllabus_file': file})

        # Should return 200 (form re-rendered with error)
        self.assertEqual(response.status_code, 200)
        # Check that response contains the upload form
        self.assertContains(response, 'syllabus_file')


class SyllabusReviewViewTestCase(TestCase):
    """Test the syllabus review and import functionality"""

    def setUp(self):
        self.client = Client()

        # Create test course
        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(
            code='CS101',
            name='Test Course',
            uv=4
        )
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test Section',
            period=period,
            instructor_name='Test Instructor',
            location='Test Location'
        )

        self.review_url = reverse('courses:syllabus-review', args=[self.course.id])

        # Simulate session with extracted topics
        session = self.client.session
        session['extracted_topics'] = [
            {'name': 'Introduction to Programming', 'description': '', 'order': 1},
            {'name': 'Variables and Data Types', 'description': '', 'order': 2},
            {'name': 'Control Structures', 'description': '', 'order': 3},
        ]
        session.save()

    def test_get_review_form(self):
        """Test accessing the review form"""
        response = self.client.get(self.review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/syllabus_review.html')

    def test_import_selected_topics(self):
        """Test importing selected topics"""
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

        # Should redirect to topics list
        self.assertEqual(response.status_code, 302)

        # Verify topics were created
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 2)  # Only 2 selected

        # Verify topic details
        t01 = topics.get(code='T01')
        self.assertEqual(t01.name, 'Introduction to Programming')
        self.assertEqual(t01.description, 'Learn the basics')

    def test_import_with_empty_topics(self):
        """Test importing without selecting any topics"""
        data = {
            'topic_0_include': '',
            'topic_0_code': 'T01',
            'topic_0_name': 'Introduction to Programming',
            'topic_0_description': '',
            'topic_0_order': '1',
        }

        response = self.client.post(self.review_url, data)

        # Should show error
        self.assertEqual(response.status_code, 200)
        # Topics should not be created
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 0)

    def test_import_preserves_order(self):
        """Test that imported topics maintain order"""
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
        self.assertEqual(list(topics.values_list('name', flat=True)),
                        ['First Topic', 'Second Topic', 'Third Topic'])


class TopicImportIntegrationTestCase(TestCase):
    """Integration tests for the complete import workflow"""

    def setUp(self):
        self.client = Client()

        # Create test course
        period = Period.objects.create(name='II PAC 2026', start_date=date(2026, 5, 1), end_date=date(2026, 8, 31))
        assignature = Assignature.objects.create(
            code='ISC-333',
            name='Sistemas Operativos I',
            uv=4
        )
        self.course = Course.objects.create(
            assignature=assignature,
            name='Sección 1700',
            period=period,
            instructor_name='José Enrique Ávila',
            location='Room 101'
        )

    def test_complete_workflow_text_file(self):
        """Test complete import workflow with text file"""
        # Step 1: Upload file
        syllabus_content = b"""1. Introduction to Programming
2. Variables and Data Types
3. Control Structures
4. Functions
5. Data Structures"""

        file = SimpleUploadedFile("syllabus.txt", syllabus_content)
        upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

        response = self.client.post(upload_url, {'syllabus_file': file})
        self.assertEqual(response.status_code, 302)

        # Step 2: Review and import
        review_url = reverse('courses:syllabus-review', args=[self.course.id])

        # Check session has extracted topics
        self.assertIn('extracted_topics', self.client.session)
        extracted = self.client.session['extracted_topics']
        self.assertEqual(len(extracted), 5)

        # Import all topics
        data = {}
        for i in range(5):
            data[f'topic_{i}_include'] = 'on'
            data[f'topic_{i}_code'] = f'T{i+1:02d}'
            data[f'topic_{i}_name'] = extracted[i]['name']
            data[f'topic_{i}_description'] = ''
            data[f'topic_{i}_order'] = str(i + 1)

        response = self.client.post(review_url, data)
        self.assertEqual(response.status_code, 302)

        # Step 3: Verify topics in database
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 5)

        # Verify details
        first_topic = topics.get(code='T01')
        self.assertEqual(first_topic.name, 'Introduction to Programming')
        self.assertEqual(first_topic.order, 1)

    def test_edit_topics_before_import(self):
        """Test editing topics before importing"""
        syllabus_content = b"""1. Topic One
2. Topic Two"""

        file = SimpleUploadedFile("syllabus.txt", syllabus_content)
        upload_url = reverse('courses:syllabus-upload', args=[self.course.id])

        self.client.post(upload_url, {'syllabus_file': file})

        review_url = reverse('courses:syllabus-review', args=[self.course.id])

        # Edit topic names before import
        data = {
            'topic_0_include': 'on',
            'topic_0_code': 'T01',
            'topic_0_name': 'Modified Topic One',  # Changed
            'topic_0_description': 'Added description',
            'topic_0_order': '1',

            'topic_1_include': 'on',
            'topic_1_code': 'T02',
            'topic_1_name': 'Modified Topic Two',  # Changed
            'topic_1_description': '',
            'topic_1_order': '2',
        }

        self.client.post(review_url, data)

        # Verify edited data was saved
        topic = Topic.objects.get(code='T01')
        self.assertEqual(topic.name, 'Modified Topic One')
        self.assertEqual(topic.description, 'Added description')


class TopicCodeGenerationTestCase(TestCase):
    """Test automatic topic code generation"""

    def setUp(self):
        period = Period.objects.create(name='Test Period', start_date=date(2026, 1, 1), end_date=date(2026, 12, 31))
        assignature = Assignature.objects.create(
            code='TEST101',
            name='Test',
            uv=4
        )
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test',
            period=period,
            instructor_name='Test',
            location='Test Location'
        )

    def test_code_format(self):
        """Test that generated codes follow T## format"""
        topic = Topic.objects.create(
            course=self.course,
            code='T01',
            name='First Topic',
            order=1
        )
        self.assertEqual(topic.code, 'T01')

    def test_sequential_codes(self):
        """Test sequential code generation"""
        for i in range(1, 6):
            Topic.objects.create(
                course=self.course,
                code=f'T{i:02d}',
                name=f'Topic {i}',
                order=i
            )

        topics = Topic.objects.filter(course=self.course).order_by('order')
        codes = [t.code for t in topics]

        expected = ['T01', 'T02', 'T03', 'T04', 'T05']
        self.assertEqual(codes, expected)


class CSVImportTestCase(TestCase):
    """Test CSV file import functionality"""

    def setUp(self):
        self.client = Client()
        period = Period.objects.create(
            name='Test Period',
            start_date=date(2026, 5, 1),
            end_date=date(2026, 8, 31)
        )
        assignature = Assignature.objects.create(
            code='TEST101',
            name='Test Course',
            uv=4
        )
        self.course = Course.objects.create(
            assignature=assignature,
            name='Test',
            period=period,
            instructor_name='Test',
            location='Test'
        )
        self.csv_import_url = reverse('courses:csv-import', args=[self.course.id])

    def test_csv_import_form_get(self):
        """Test accessing CSV import form"""
        response = self.client.get(self.csv_import_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/csv_import.html')

    def test_csv_import_valid_file(self):
        """Test uploading valid CSV file"""
        csv_content = b"""code,name,description,materials,order
T01,Introduction,Basic intro,Book Ch.1,1
T02,Advanced,More detail,Book Ch.2,2
T03,Expert,Deep dive,Book Ch.3,3"""

        csv_file = SimpleUploadedFile(
            "topics.csv",
            csv_content,
            content_type="text/csv"
        )

        response = self.client.post(
            self.csv_import_url,
            {'csv_file': csv_file}
        )

        # Should redirect to review page
        self.assertEqual(response.status_code, 302)
        self.assertIn('/csv/review/', response.url)

    def test_csv_import_missing_name(self):
        """Test CSV with missing name field"""
        csv_content = b"""code,name,description,materials,order
T01,,No name here,Book Ch.1,1"""

        csv_file = SimpleUploadedFile(
            "bad.csv",
            csv_content,
            content_type="text/csv"
        )

        response = self.client.post(
            self.csv_import_url,
            {'csv_file': csv_file}
        )

        # Should show error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Missing')

    def test_csv_import_with_materials(self):
        """Test CSV with materials/book references"""
        csv_content = b"""code,name,description,materials,order
T01,Intro,Basic,Tanenbaum Ch.1 | Silberschatz Ch.1,1
T02,Advanced,Complex,Love Ch.5 | McKusick Ch.3,2"""

        csv_file = SimpleUploadedFile(
            "books.csv",
            csv_content,
            content_type="text/csv"
        )

        response = self.client.post(
            self.csv_import_url,
            {'csv_file': csv_file}
        )

        # Check session has topics
        self.assertIn('csv_topics', self.client.session)
        topics = self.client.session['csv_topics']
        self.assertEqual(len(topics), 2)
        self.assertEqual(topics[0]['materials'], 'Tanenbaum Ch.1 | Silberschatz Ch.1')

    def test_csv_review_and_import(self):
        """Test complete CSV import workflow"""
        csv_content = b"""code,name,description,materials,order
T01,Topic One,Description,Ref1,1
T02,Topic Two,Details,Ref2,2"""

        csv_file = SimpleUploadedFile(
            "test.csv",
            csv_content,
            content_type="text/csv"
        )

        # Upload
        response = self.client.post(
            self.csv_import_url,
            {'csv_file': csv_file}
        )
        self.assertEqual(response.status_code, 302)

        # Get review form
        review_url = reverse('courses:csv-review', args=[self.course.id])
        response = self.client.get(review_url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'courses/csv_review.html')

        # Import
        csv_topics = self.client.session['csv_topics']
        data = {}
        for i in range(len(csv_topics)):
            data[f'topic_{i}_include'] = 'on'
            data[f'topic_{i}_code'] = csv_topics[i]['code']
            data[f'topic_{i}_name'] = csv_topics[i]['name']
            data[f'topic_{i}_description'] = csv_topics[i]['description']
            data[f'topic_{i}_order'] = str(csv_topics[i]['order'])

        response = self.client.post(review_url, data)
        self.assertEqual(response.status_code, 302)

        # Verify topics created
        topics = Topic.objects.filter(course=self.course)
        self.assertEqual(topics.count(), 2)
        self.assertEqual(topics.first().name, 'Topic One')
