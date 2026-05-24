from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView
from django.http import HttpResponse
from django.contrib import messages
from django.urls import reverse_lazy
from django.db.models import Max

from .models import Course, Topic, Material, CourseSchedule
from .forms import TopicForm, MaterialForm, CourseScheduleForm


# ==================== HOME VIEWS ====================

class HomeView(TemplateView):
    """Display home page with menu and course overview"""
    template_name = 'courses/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all().count()
        context['topics'] = Topic.objects.all().count()
        context['materials'] = Material.objects.all().count()
        context['schedules'] = CourseSchedule.objects.all().count()
        context['recent_courses'] = Course.objects.all().order_by('-created_at')[:5]
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
        """Handle form submission and create schedules"""
        course = get_object_or_404(Course, pk=course_id)
        form = CourseScheduleForm(request.POST)

        if form.is_valid():
            days = [int(d) for d in form.cleaned_data['days']]
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            created_schedules = []
            for day in days:
                # Check if schedule already exists
                existing = CourseSchedule.objects.filter(
                    course=course,
                    day_of_week=day,
                    start_time=start_time
                ).exists()

                if not existing:
                    schedule = CourseSchedule.objects.create(
                        course=course,
                        day_of_week=day,
                        start_time=start_time,
                        end_time=end_time
                    )
                    created_schedules.append(schedule)

            if created_schedules:
                messages.success(
                    request,
                    f'Created {len(created_schedules)} schedule(s) successfully.'
                )
                # Return all created schedules
                return render(
                    request,
                    'courses/partials/schedule_list_items.html',
                    {'schedules': created_schedules}
                )
            else:
                messages.warning(request, 'All selected schedules already exist.')
                return HttpResponse(status=400)
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
            'days': [str(schedule.day_of_week)],
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
            days = [int(d) for d in form.cleaned_data['days']]
            start_time = form.cleaned_data['start_time']
            end_time = form.cleaned_data['end_time']

            # For simplicity, update only if a single day is selected
            if len(days) == 1:
                schedule.day_of_week = days[0]
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
                messages.error(request, 'Please select only one day for editing.')
                return HttpResponse(status=400)
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
        day_display = schedule.get_day_of_week_display()
        schedule.delete()

        messages.success(request, f'Schedule for {day_display} deleted successfully.')
        return HttpResponse(status=200)
