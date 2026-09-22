from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.db import IntegrityError, transaction
from django.db.models import Max
from django.utils import timezone

import calendar
from datetime import date, timedelta

from .models import Course, Topic, Material, SyllabusDraftTopic
from .forms import TopicForm, MaterialForm, CourseScheduleForm, SyllabusUploadForm, TopicReviewForm
from schedule.models import CourseSchedule, CourseCalendar, NonWorkingDay
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
    """Display only courses whose period is currently active"""
    model = Course
    template_name = 'courses/course_list.html'
    context_object_name = 'courses'
    paginate_by = 20

    def get_queryset(self):
        today = timezone.now().date()
        return Course.objects.filter(
            period__start_date__lte=today, period__end_date__gte=today
        ).order_by('-created_at')


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

class CourseCalendarListView(TemplateView):
    """Display generated calendar sessions for a course as a month grid"""
    template_name = 'courses/calendar_list.html'

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ['courses/partials/calendar_grid.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = get_object_or_404(Course, pk=self.kwargs['course_id'])
        today = timezone.now().date()
        year = int(self.request.GET.get('year', today.year))
        month = int(self.request.GET.get('month', today.month))

        sessions = CourseCalendar.objects.filter(
            course=course, session_date__year=year, session_date__month=month
        ).select_related('topic').order_by('start_time')
        sessions_by_day = {}
        for session in sessions:
            sessions_by_day.setdefault(session.session_date.day, []).append(session)

        cal = calendar.Calendar(firstweekday=6)  # Sunday first, matches day_of_week convention
        weeks = [
            [(day, sessions_by_day.get(day, [])) for day in week]
            for week in cal.monthdayscalendar(year, month)
        ]

        prev_month = date(year, month, 1) - timedelta(days=1)
        next_month = date(year, month, 28) + timedelta(days=7)

        context.update({
            'course': course,
            'weeks': weeks,
            'month_name': date(year, month, 1).strftime('%B %Y'),
            'weekday_names': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
            'prev_year': prev_month.year,
            'prev_month': prev_month.month,
            'next_year': next_month.year,
            'next_month': next_month.month,
            'today': today,
            'current_year': year,
            'current_month': month,
        })
        return context


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
        ).order_by('start_time')

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
            'start_time': schedule.start_time.strftime('%H:%M'),
            'end_time': schedule.end_time.strftime('%H:%M'),
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


def _generate_calendar_sessions(course, schedule, non_working_days):
    """Create CourseCalendar sessions for one schedule across the course's period.
    Returns the number of sessions created."""
    period = course.period

    # Drop this schedule's sessions that no longer match; keep logged ones as-is.
    CourseCalendar.objects.filter(
        course=course,
        start_time=schedule.start_time,
        end_time=schedule.end_time,
        logs__isnull=True,
    ).delete()

    created_count = 0
    current = period.start_date
    while current <= period.end_date:
        day_of_week = (current.weekday() + 1) % 7  # model: 0=Sunday..6=Saturday
        if day_of_week in schedule.days and current not in non_working_days:
            _, created = CourseCalendar.objects.get_or_create(
                course=course,
                session_date=current,
                start_time=schedule.start_time,
                defaults={'day_of_week': day_of_week, 'end_time': schedule.end_time},
            )
            if created:
                created_count += 1
        current += timedelta(days=1)
    return created_count


def _assign_topics(course):
    """Assign topics in order across all of the course's unlogged sessions."""
    sessions = list(CourseCalendar.objects.filter(
        course=course, logs__isnull=True
    ).order_by('session_date', 'start_time'))
    topics = list(Topic.objects.filter(course=course).order_by('order'))
    for session, topic in zip(sessions, topics):
        if session.topic_id != topic.id:
            session.topic = topic
            session.save(update_fields=['topic'])
    for session in sessions[len(topics):]:
        if session.topic_id is not None:
            session.topic = None
            session.save(update_fields=['topic'])


class CourseCalendarGenerateView(View):
    """(Re)generate CourseCalendar sessions for one schedule, for every matching
    day between the course's period start and end date."""

    def post(self, request, course_id, schedule_id):
        course = get_object_or_404(Course, pk=course_id)
        schedule = get_object_or_404(CourseSchedule, pk=schedule_id, course=course)
        non_working_days = set(NonWorkingDay.objects.filter(
            date__range=(course.period.start_date, course.period.end_date)
        ).values_list('date', flat=True))

        created_count = _generate_calendar_sessions(course, schedule, non_working_days)
        _assign_topics(course)

        messages.success(request, f'{created_count} calendar session(s) generated.')
        return redirect('courses:schedule-list', course_id=course.id)


class CourseCalendarGenerateAllView(View):
    """(Re)generate CourseCalendar sessions for every schedule of a course."""

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        non_working_days = set(NonWorkingDay.objects.filter(
            date__range=(course.period.start_date, course.period.end_date)
        ).values_list('date', flat=True))

        created_count = sum(
            _generate_calendar_sessions(course, schedule, non_working_days)
            for schedule in course.schedules.all()
        )
        _assign_topics(course)

        messages.success(request, f'{created_count} calendar session(s) generated.')
        return redirect('courses:calendar-list', course_id=course.id)


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

                SyllabusDraftTopic.objects.filter(course=course).delete()
                SyllabusDraftTopic.objects.bulk_create([
                    SyllabusDraftTopic(course=course, **topic)
                    for topic in extracted_topics
                ])

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

        # Get extracted topics from the draft table
        draft_topics = list(SyllabusDraftTopic.objects.filter(course=course))

        if not draft_topics:
            messages.error(request, 'No draft topics found. Please upload a syllabus file.')
            return redirect('courses:syllabus-upload', course_id=course_id)

        form = TopicReviewForm(draft_topics)

        return render(
            request,
            'courses/syllabus_review.html',
            {
                'course': course,
                'form': form,
                'topic_count': len(draft_topics),
            }
        )

    def post(self, request, course_id):
        """Import reviewed topics into course"""
        course = get_object_or_404(Course, pk=course_id)

        # Get extracted topics from the draft table
        draft_topics = list(SyllabusDraftTopic.objects.filter(course=course))

        if not draft_topics:
            messages.error(request, 'No draft topics found.')
            return redirect('courses:syllabus-upload', course_id=course_id)

        form = TopicReviewForm(draft_topics, request.POST)

        if form.is_valid():
            reviewed_topics = form.get_reviewed_topics()

            if not reviewed_topics:
                messages.warning(request, 'No topics selected for import.')
                return redirect('courses:syllabus-review', course_id=course_id)

            # Save the reviewer's edits back onto the draft rows, so they survive
            # a failed import (see except blocks below) instead of reverting to the raw CSV values
            SyllabusDraftTopic.objects.bulk_update(
                [
                    SyllabusDraftTopic(
                        pk=topic_data['draft_id'],
                        code=topic_data['code'],
                        name=topic_data['name'],
                        description=topic_data['description'],
                        order=topic_data['order'],
                    )
                    for topic_data in reviewed_topics
                ],
                ['code', 'name', 'description', 'order']
            )

            # Create topics (all-or-nothing so a duplicate order doesn't leave a partial import)
            try:
                with transaction.atomic():
                    for topic_data in reviewed_topics:
                        Topic.objects.create(
                            course=course,
                            code=topic_data['code'],
                            name=topic_data['name'],
                            description=topic_data['description'],
                            order=topic_data['order']
                        )
                created_count = len(reviewed_topics)

                # Review is one-shot: drop the drafts now that they're either imported or skipped
                SyllabusDraftTopic.objects.filter(course=course).delete()

                messages.success(
                    request,
                    f'Successfully imported {created_count} topic(s) from syllabus!'
                )

                return redirect('courses:topic-list', course_id=course_id)

            except IntegrityError as e:
                messages.error(
                    request,
                    f'Import cancelled, no topics were saved: a topic with that order already exists ({e})'
                )
                return render(
                    request,
                    'courses/syllabus_review.html',
                    {
                        'course': course,
                        'form': form,
                        'topic_count': len(draft_topics),
                    }
                )
            except Exception as e:
                messages.error(request, f'Error creating topics: {str(e)}')
                return render(
                    request,
                    'courses/syllabus_review.html',
                    {
                        'course': course,
                        'form': form,
                        'topic_count': len(draft_topics),
                    }
                )
        else:
            return render(
                request,
                'courses/syllabus_review.html',
                {
                    'course': course,
                    'form': form,
                    'topic_count': len(draft_topics),
                }
            )


class SyllabusReviewCancelView(View):
    """Discard the pending syllabus draft without importing it"""

    def post(self, request, course_id):
        course = get_object_or_404(Course, pk=course_id)
        SyllabusDraftTopic.objects.filter(course=course).delete()
        messages.info(request, 'Syllabus import cancelled.')
        return redirect('courses:topic-list', course_id=course_id)
