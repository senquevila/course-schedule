from datetime import datetime, time as time_cls

from django import forms
from django.conf import settings
from django.utils.dates import WEEKDAYS
from django.utils.translation import gettext_lazy as _
from .models import Topic, Material, Course
from schedule.models import CourseSchedule, CourseCalendarLog


class TopicForm(forms.ModelForm):
    """Form for creating and editing topics"""

    class Meta:
        model = Topic
        fields = ['code', 'name', 'description', 'order']
        labels = {'code': _('Code'), 'name': _('Name'), 'description': _('Description'), 'order': _('Order')}
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('e.g., T01'),
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Topic name'),
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': _('Description (optional)'),
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': _('Order/sequence number'),
                'required': True
            }),
        }


class MaterialForm(forms.ModelForm):
    """Form for creating and editing materials"""

    class Meta:
        model = Material
        fields = ['code', 'name', 'material_type', 'url_or_path']
        labels = {'code': _('Code'), 'name': _('Name'), 'material_type': _('Material type'), 'url_or_path': _('URL or path')}
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('e.g., M01'),
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('Material name'),
                'required': True
            }),
            'material_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'url_or_path': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': _('URL or file path'),
                'required': True
            }),
        }


class CourseScheduleForm(forms.Form):
    """Form for creating and editing course schedules with multiple days"""

    DAY_CHOICES = [(d, WEEKDAYS[(d - 1) % 7]) for d in range(7)]  # 0=Sunday

    # Multiple checkboxes for selecting days
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        }),
        required=True,
        label=_('Days of Week'),
        help_text=_('Select all days this schedule applies to')
    )

    HOUR_CHOICES = [
        (f'{h:02d}:00', time_cls(h, 0).strftime('%I:%M %p').lstrip('0'))
        for h in range(settings.MIN_VALID_HOUR, settings.MAX_VALID_HOUR + 1)
    ]

    start_time = forms.ChoiceField(
        choices=HOUR_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label=_('Start Time')
    )

    end_time = forms.ChoiceField(
        choices=HOUR_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'required': True
        }),
        label=_('End Time')
    )

    def clean(self):
        cleaned_data = super().clean()
        days = cleaned_data.get('days')

        if cleaned_data.get('start_time'):
            cleaned_data['start_time'] = datetime.strptime(cleaned_data['start_time'], '%H:%M').time()
        if cleaned_data.get('end_time'):
            cleaned_data['end_time'] = datetime.strptime(cleaned_data['end_time'], '%H:%M').time()

        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError(
                    _("End time must be after start time.")
                )

        if not days:
            raise forms.ValidationError(
                _("Please select at least one day.")
            )

        # Convert days to integers
        cleaned_data['days'] = [int(d) for d in days]
        return cleaned_data


class SyllabusUploadForm(forms.Form):
    """Form for uploading a syllabus CSV to extract topics"""

    syllabus_file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-input',
            'accept': '.csv',
            'required': True
        }),
        label=_('Syllabus CSV'),
        help_text=_('Upload a CSV file with columns: code,name,description,order')
    )

    def clean_syllabus_file(self):
        """Validate file type and size"""
        file = self.cleaned_data.get('syllabus_file')

        if file:
            if not file.name.lower().endswith('.csv'):
                raise forms.ValidationError(_('Only .csv files are supported'))

            if file.size > 10 * 1024 * 1024:
                raise forms.ValidationError(_('File size must not exceed 10MB'))

        return file


class TopicReviewForm(forms.Form):
    """Form for reviewing and editing extracted topics before saving"""

    def __init__(self, draft_topics, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Dynamically create fields for each draft topic, keyed by its DB id
        for draft in draft_topics:
            i = draft.pk
            self.fields[f'topic_{i}_code'] = forms.CharField(
                initial=draft.code,
                widget=forms.TextInput(attrs={
                    'class': 'form-input',
                    'placeholder': 'T01',
                    'size': '10'
                }),
                label=_('Code')
            )

            self.fields[f'topic_{i}_name'] = forms.CharField(
                initial=draft.name,
                widget=forms.TextInput(attrs={
                    'class': 'form-input',
                    'placeholder': _('Topic name')
                }),
                label=_('Name')
            )

            self.fields[f'topic_{i}_description'] = forms.CharField(
                initial=draft.description,
                widget=forms.Textarea(attrs={
                    'class': 'form-textarea',
                    'rows': 2,
                    'placeholder': _('Topic description (optional)')
                }),
                label=_('Description'),
                required=False
            )

            self.fields[f'topic_{i}_order'] = forms.IntegerField(
                initial=draft.order,
                widget=forms.NumberInput(attrs={
                    'class': 'form-input',
                    'size': '5'
                }),
                label=_('Order')
            )

            self.fields[f'topic_{i}_include'] = forms.BooleanField(
                initial=True,
                widget=forms.CheckboxInput(attrs={
                    'class': 'form-checkbox'
                }),
                label=_('Include this topic'),
                required=False
            )

    def get_reviewed_topics(self):
        """Extract reviewed and cleaned topics from form data, keyed by draft id"""
        topics = []

        for key, value in self.cleaned_data.items():
            if key.startswith('topic_') and key.endswith('_code'):
                # Extract draft id
                parts = key.split('_')
                draft_id = int(parts[1])

                # Check if topic should be included
                include_key = f'topic_{draft_id}_include'
                if not self.cleaned_data.get(include_key, False):
                    continue

                topics.append({
                    'draft_id': draft_id,
                    'code': self.cleaned_data.get(f'topic_{draft_id}_code', ''),
                    'name': self.cleaned_data.get(f'topic_{draft_id}_name', ''),
                    'description': self.cleaned_data.get(f'topic_{draft_id}_description', ''),
                    'order': self.cleaned_data.get(f'topic_{draft_id}_order', draft_id),
                })

        # Sort by order
        return sorted(topics, key=lambda x: x['order'])


class CourseCalendarLogForm(forms.ModelForm):
    """Form for logging what actually happened in a calendar session"""
    has_issues = forms.ChoiceField(
        choices=[('no', _('No problem')), ('yes', _('I have issues'))],
        initial='no',
        widget=forms.RadioSelect,
        label=_('How did it go?'),
    )

    class Meta:
        model = CourseCalendarLog
        fields = ['actual_date', 'problems', 'solutions']
        labels = {
            'actual_date': _('Actual date'),
            'problems': _('Problems'),
            'solutions': _('Solutions'),
        }
        widgets = {
            'actual_date': forms.DateInput(attrs={'class': 'form-input', 'type': 'date'}),
            'problems': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
            'solutions': forms.Textarea(attrs={'class': 'form-textarea', 'rows': 2}),
        }
