from django import forms
from .models import Topic, Material, CourseSchedule


class TopicForm(forms.ModelForm):
    """Form for creating and editing topics"""

    class Meta:
        model = Topic
        fields = ['code', 'name', 'description', 'order']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., T01',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Topic name',
                'required': True
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Description (optional)',
                'rows': 3
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'placeholder': 'Order/sequence number',
                'required': True
            }),
        }


class MaterialForm(forms.ModelForm):
    """Form for creating and editing materials"""

    class Meta:
        model = Material
        fields = ['code', 'name', 'material_type', 'url_or_path']
        widgets = {
            'code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., M01',
                'required': True
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Material name',
                'required': True
            }),
            'material_type': forms.Select(attrs={
                'class': 'form-select',
                'required': True
            }),
            'url_or_path': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'URL or file path',
                'required': True
            }),
        }


class CourseScheduleForm(forms.Form):
    """Form for creating and editing course schedules"""

    DAY_CHOICES = [
        (0, 'Sunday'),
        (1, 'Monday'),
        (2, 'Tuesday'),
        (3, 'Wednesday'),
        (4, 'Thursday'),
        (5, 'Friday'),
        (6, 'Saturday'),
    ]

    # Multiple checkboxes for selecting days
    days = forms.MultipleChoiceField(
        choices=DAY_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-checkbox'
        }),
        required=True,
        label='Days of Week'
    )

    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-input',
            'type': 'time',
            'required': True
        }),
        label='Start Time'
    )

    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={
            'class': 'form-input',
            'type': 'time',
            'required': True
        }),
        label='End Time'
    )

    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')

        if start_time and end_time:
            if start_time >= end_time:
                raise forms.ValidationError(
                    "End time must be after start time."
                )

        return cleaned_data
