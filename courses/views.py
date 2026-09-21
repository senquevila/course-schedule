from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Max
from django.utils import timezone

from .models import Course, Topic, Material
from .forms import TopicForm, MaterialForm, CourseScheduleForm, SyllabusUploadForm, TopicReviewForm
from schedule.models import CourseSchedule
from .syllabus_parser import parse_syllabus_csv, SyllabusCSVError


# ==================== HOME VIEWS ====================

class HomeView(TemplateView):
    """Display home page with menu and course overview"""
    template_name = 'courses/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()
        active_courses = Course.objects.filter(
            period__start_date__lte=today, period__end_date__gte=today
        )
        context['courses'] = active_courses.count()
        context['topics'] = Topic.objects.filter(course__in=active_courses).count()
        context['materials'] = Material.objects.filter(topic__course__in=active_courses).count()
        context['schedules'] = CourseSchedule.objects.filter(course__in=active_courses).count()
        context['recent_courses'] = active_courses.order_by('-created_at')[:5]
        return context


class CourseListView(ListView):
    """Display all courses"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        return Course.objects.all().order_by('-created_at')


# ==================== TOPIC VIEWS ====================

class TopicListView(ListView):
    """Display list of all topics for a course"""
    model = Topic
    template_name = 'courses/topics_list.html'
    context_object_name = 'topics'
    paginate_by = 50

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return Topic.objects.filter(course_id=course_id).order_by('order')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return context


class TopicCreateView(View):
    """Handle HTMX request to create a new topic - returns modal form"""

    def get(self, request, course_id):
        """Return the form modal"""
        course = get_object_or_404(Course, pk=course_id)

        # Get next order number
        last_topic = Topic.objects.filter(course=course).aggregate(
            max_order=Max('order')
        )
        next_order = (last_topic['max_order'] or 0) + 1

        form = TopicForm(initial={'order': next_order})
        return render(
            request,
            'courses/partials/topic_form.html',
            {
                'form': form,
                'course': course,
                'is_create': True,
            }
        )

    def post(self, request, course_id):
        """Handle form submission and create topic"""
        course = get_object_or_404(Course, pk=course_id)
        form = TopicForm(request.POST)

        if form.is_valid():
            topic = form.save(commit=False)
            topic.course = course
            topic.save()
            messages.success(request, f'Topic "{topic.name}" created successfully.')

            # Return the new topic row
            return render(
                request,
                'courses/partials/topic_item.html',
                {'topic': topic}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/topic_form.html',
                {
                    'form': form,
                    'course': course,
                    'is_create': True,
                },
                status=400
            )


class TopicUpdateView(View):
    """Handle HTMX request to update a topic"""

    def get(self, request, course_id, topic_id):
        """Return the edit form modal"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        form = TopicForm(instance=topic)

        return render(
            request,
            'courses/partials/topic_form.html',
            {
                'form': form,
                'course': course,
                'topic': topic,
                'is_create': False,
            }
        )

    def post(self, request, course_id, topic_id):
        """Handle form submission and update topic"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        form = TopicForm(request.POST, instance=topic)

        if form.is_valid():
            topic = form.save()
            messages.success(request, f'Topic "{topic.name}" updated successfully.')

            # Return the updated topic row
            return render(
                request,
                'courses/partials/topic_item.html',
                {'topic': topic}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/topic_form.html',
                {
                    'form': form,
                    'course': course,
                    'topic': topic,
                    'is_create': False,
                },
                status=400
            )


class TopicDeleteView(View):
    """Handle HTMX request to delete a topic"""

    def delete(self, request, course_id, topic_id):
        """Delete the topic and return empty response"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        topic_name = topic.name
        topic.delete()

        messages.success(request, f'Topic "{topic_name}" deleted successfully.')
        return HttpResponse(status=200)


# ==================== MATERIAL VIEWS ====================

class MaterialListView(ListView):
    """Display list of materials for a topic"""
    model = Material
    template_name = 'courses/materials_list.html'
    context_object_name = 'materials'
    paginate_by = 50

    def get_queryset(self):
        topic_id = self.kwargs['topic_id']
        return Material.objects.filter(topic_id=topic_id).order_by('code')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        context['topic'] = get_object_or_404(Topic, pk=self.kwargs['topic_id'])
        return context


class MaterialCreateView(View):
    """Handle HTMX request to create a new material - returns modal form"""

    def get(self, request, course_id, topic_id):
        """Return the form modal"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        form = MaterialForm()

        return render(
            request,
            'courses/partials/material_form.html',
            {
                'form': form,
                'course': course,
                'topic': topic,
                'is_create': True,
            }
        )

    def post(self, request, course_id, topic_id):
        """Handle form submission and create material"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        form = MaterialForm(request.POST)

        if form.is_valid():
            material = form.save(commit=False)
            material.topic = topic
            material.save()
            messages.success(request, f'Material "{material.name}" added successfully.')

            # Return the new material row
            return render(
                request,
                'courses/partials/material_item.html',
                {'material': material}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/material_form.html',
                {
                    'form': form,
                    'course': course,
                    'topic': topic,
                    'is_create': True,
                },
                status=400
            )


class MaterialUpdateView(View):
    """Handle HTMX request to update a material"""

    def get(self, request, course_id, topic_id, material_id):
        """Return the edit form modal"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        material = get_object_or_404(Material, pk=material_id, topic=topic)
        form = MaterialForm(instance=material)

        return render(
            request,
            'courses/partials/material_form.html',
            {
                'form': form,
                'course': course,
                'topic': topic,
                'material': material,
                'is_create': False,
            }
        )

    def post(self, request, course_id, topic_id, material_id):
        """Handle form submission and update material"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        material = get_object_or_404(Material, pk=material_id, topic=topic)
        form = MaterialForm(request.POST, instance=material)

        if form.is_valid():
            material = form.save()
            messages.success(request, f'Material "{material.name}" updated successfully.')

            # Return the updated material row
            return render(
                request,
                'courses/partials/material_item.html',
                {'material': material}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/material_form.html',
                {
                    'form': form,
                    'course': course,
                    'topic': topic,
                    'material': material,
                    'is_create': False,
                },
                status=400
            )


class MaterialDeleteView(View):
    """Handle HTMX request to delete a material"""

    def delete(self, request, course_id, topic_id, material_id):
        """Delete the material and return empty response"""
        course = get_object_or_404(Course, pk=course_id)
        topic = get_object_or_404(Topic, pk=topic_id, course=course)
        material = get_object_or_404(Material, pk=material_id, topic=topic)
        material_name = material.name
        material.delete()

        messages.success(request, f'Material "{material_name}" deleted successfully.')
        return HttpResponse(status=200)


# ==================== COURSE SCHEDULE VIEWS ====================

class CourseScheduleListView(ListView):
    """Display list of all schedules for a course"""
    model = CourseSchedule
    template_name = 'courses/schedule_list.html'
    context_object_name = 'schedules'
    paginate_by = 50

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        return CourseSchedule.objects.filter(
            course_id=course_id
        ).order_by('day_of_week', 'start_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['course'] = get_object_or_404(Course, pk=self.kwargs['course_id'])
        return context


class CourseScheduleCreateView(View):
    """Handle HTMX request to create a new schedule - returns modal form"""

    def get(self, request, course_id):
        """Return the form modal"""
        course = get_object_or_404(Course, pk=course_id)
        form = CourseScheduleForm()

        return render(
            request,
            'courses/partials/schedule_form.html',
            {
                'form': form,
                'course': course,
                'is_create': True,
            }
        )

    def post(self, request, course_id):
        """Handle form submission and create schedule"""
        course = get_object_or_404(Course, pk=course_id)
        form = CourseScheduleForm(request.POST)

        if form.is_valid():
            days = form.cleaned_data['days']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # Check if schedule already exists
            existing = CourseSchedule.objects.filter(
                course=course,
                start_time=start_time,
                end_time=end_time
            ).exists()

            if existing:
                messages.warning(
                    request,
                    'A schedule with this time range already exists. Please edit it to add more days.'
                )
                return HttpResponse(status=400)

            # Create single schedule with all days
            schedule = CourseSchedule.objects.create(
                course=course,
                days=days,
                start_time=start_time,
                end_time=end_time
            )

            messages.success(
                request,
                f'Schedule created for {schedule.get_days_display()} successfully.'
            )

            # Return the new schedule
            return render(
                request,
                'courses/partials/schedule_item.html',
                {'schedule': schedule}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/schedule_form.html',
                {
                    'form': form,
                    'course': course,
                    'is_create': True,
                },
                status=400
            )


class CourseScheduleUpdateView(View):
    """Handle HTMX request to update a schedule"""

    def get(self, request, course_id, schedule_id):
        """Return the edit form modal"""
        course = get_object_or_404(Course, pk=course_id)
        schedule = get_object_or_404(CourseSchedule, pk=schedule_id, course=course)

        # Initialize form with current schedule data
        form = CourseScheduleForm(initial={
            'days': [str(d) for d in schedule.days],
            'start_time': schedule.start_time,
            'end_time': schedule.end_time,
        })

        return render(
            request,
            'courses/partials/schedule_form.html',
            {
                'form': form,
                'course': course,
                'schedule': schedule,
                'is_create': False,
            }
        )

    def post(self, request, course_id, schedule_id):
        """Handle form submission and update schedule"""
        course = get_object_or_404(Course, pk=course_id)
        schedule = get_object_or_404(CourseSchedule, pk=schedule_id, course=course)
        form = CourseScheduleForm(request.POST)

        if form.is_valid():
            days = form.cleaned_data['days']
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            schedule.days = days
            schedule.start_time = start_time
            schedule.end_time = end_time
            schedule.save()
            messages.success(request, 'Schedule updated successfully.')

            # Return the updated schedule row
            return render(
                request,
                'courses/partials/schedule_item.html',
                {'schedule': schedule}
            )
        else:
            # Return form with errors
            return render(
                request,
                'courses/partials/schedule_form.html',
                {
                    'form': form,
                    'course': course,
                    'schedule': schedule,
                    'is_create': False,
                },
                status=400
            )


class CourseScheduleDeleteView(View):
    """Handle HTMX request to delete a schedule"""

    def delete(self, request, course_id, schedule_id):
        """Delete the schedule and return empty response"""
        course = get_object_or_404(Course, pk=course_id)
        schedule = get_object_or_404(CourseSchedule, pk=schedule_id, course=course)
        schedule.delete()

        messages.success(request, f'Schedule deleted successfully.')
        return HttpResponse(status=200)


# ==================== SYLLABUS IMPORT VIEWS ====================

class SyllabusUploadView(View):
    """Handle syllabus file upload and topic extraction"""

    def get(self, request, course_id):
        """Display syllabus upload form"""
        course = get_object_or_404(Course, pk=course_id)
        form = SyllabusUploadForm()

        return render(
            request,
            'courses/syllabus_upload.html',
            {
                'course': course,
                'form': form,
            }
        )

    def post(self, request, course_id):
        """Handle file upload and extract topics"""
        course = get_object_or_404(Course, pk=course_id)
        form = SyllabusUploadForm(request.POST, request.FILES)

        if form.is_valid():
            uploaded_file = request.FILES['syllabus_file']

            try:
                file_content = uploaded_file.read()
                extracted_topics = parse_syllabus_csv(file_content)

                if not extracted_topics:
                    messages.warning(request, 'No topics found in the CSV file.')
                    return render(
                        request,
                        'courses/syllabus_upload.html',
                        {
                            'course': course,
                            'form': form,
                        }
                    )

                # Store extracted topics in session for next step
                request.session['extracted_topics'] = extracted_topics
                request.session['course_id'] = course_id

                # Redirect to review page
                return redirect('courses:syllabus-review', course_id=course_id)

            except SyllabusCSVError as e:
                messages.error(request, str(e))
                return render(
                    request,
                    'courses/syllabus_upload.html',
                    {
                        'course': course,
                        'form': form,
                    }
                )
            except Exception as e:
                messages.error(
                    request,
                    f'Error processing file: {str(e)}'
                )
                return render(
                    request,
                    'courses/syllabus_upload.html',
                    {
                        'course': course,
                        'form': form,
                    }
                )
        else:
            return render(
                request,
                'courses/syllabus_upload.html',
                {
                    'course': course,
                    'form': form,
                }
            )


class SyllabusReviewView(View):
    """Review and edit extracted topics before importing"""

    def get(self, request, course_id):
        """Display topic review form"""
        course = get_object_or_404(Course, pk=course_id)

        # Get extracted topics from session
        extracted_topics = request.session.get('extracted_topics', [])

        if not extracted_topics:
            messages.error(request, 'No topics in session. Please upload a syllabus file.')
            return redirect('courses:syllabus-upload', course_id=course_id)

        form = TopicReviewForm(extracted_topics)

        return render(
            request,
            'courses/syllabus_review.html',
            {
                'course': course,
                'form': form,
                'topic_count': len(extracted_topics),
            }
        )

    def post(self, request, course_id):
        """Import reviewed topics into course"""
        course = get_object_or_404(Course, pk=course_id)

        # Get extracted topics from session
        extracted_topics = request.session.get('extracted_topics', [])

        if not extracted_topics:
            messages.error(request, 'No topics in session.')
            return redirect('courses:syllabus-upload', course_id=course_id)

        form = TopicReviewForm(extracted_topics, request.POST)

        if form.is_valid():
            reviewed_topics = form.get_reviewed_topics()

            if not reviewed_topics:
                messages.warning(request, 'No topics selected for import.')
                return redirect('courses:syllabus-review', course_id=course_id)

            # Create topics
            created_count = 0
            try:
                for topic_data in reviewed_topics:
                    Topic.objects.create(
                        course=course,
                        code=topic_data['code'],
                        name=topic_data['name'],
                        description=topic_data['description'],
                        order=topic_data['order']
                    )
                    created_count += 1

                # Clear session
                if 'extracted_topics' in request.session:
                    del request.session['extracted_topics']
                if 'course_id' in request.session:
                    del request.session['course_id']

                messages.success(
                    request,
                    f'Successfully imported {created_count} topic(s) from syllabus!'
                )

                return redirect('courses:topic-list', course_id=course_id)

            except Exception as e:
                messages.error(request, f'Error creating topics: {str(e)}')
                return render(
                    request,
                    'courses/syllabus_review.html',
                    {
                        'course': course,
                        'form': form,
                        'topic_count': len(extracted_topics),
                    }
                )
        else:
            return render(
                request,
                'courses/syllabus_review.html',
                {
                    'course': course,
                    'form': form,
                    'topic_count': len(extracted_topics),
                }
            )
