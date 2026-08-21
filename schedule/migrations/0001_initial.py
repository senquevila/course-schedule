from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('courses', '0003_alter_courseschedule_options_and_more'),
    ]

    # ponytail: state-only move, tables already exist under courses_* names
    # (see Meta.db_table on the models) so no database operations are needed.
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.CreateModel(
                    name='CourseSchedule',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('days', models.JSONField(default=list, help_text='List of day numbers: 0=Sunday, 1=Monday, ..., 6=Saturday')),
                        ('start_time', models.TimeField()),
                        ('end_time', models.TimeField()),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='schedules', to='courses.course')),
                    ],
                    options={
                        'verbose_name': 'Course Schedule',
                        'verbose_name_plural': 'Course Schedules',
                        'db_table': 'courses_courseschedule',
                        'ordering': ['course', 'start_time'],
                        'unique_together': {('course', 'start_time', 'end_time')},
                    },
                ),
                migrations.CreateModel(
                    name='CourseSession',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('session_date', models.DateField()),
                        ('day_of_week', models.IntegerField()),
                        ('start_time', models.TimeField()),
                        ('end_time', models.TimeField()),
                        ('created_at', models.DateTimeField(auto_now_add=True)),
                        ('course', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='sessions', to='courses.course')),
                        ('topic', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sessions', to='courses.topic')),
                    ],
                    options={
                        'verbose_name': 'Course Session',
                        'verbose_name_plural': 'Course Sessions',
                        'db_table': 'courses_coursesession',
                        'ordering': ['session_date', 'start_time'],
                        'unique_together': {('course', 'session_date', 'start_time')},
                    },
                ),
                migrations.AddIndex(
                    model_name='coursesession',
                    index=models.Index(fields=['session_date'], name='courses_cou_session_4eaccd_idx'),
                ),
                migrations.AddIndex(
                    model_name='coursesession',
                    index=models.Index(fields=['course', 'session_date'], name='courses_cou_course__2ed5d9_idx'),
                ),
            ],
        ),
    ]
