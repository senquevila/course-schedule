from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0003_alter_courseschedule_options_and_more'),
        ('schedule', '0001_initial'),
    ]

    # ponytail: state-only, tables stay put — see schedule/migrations/0001_initial.py
    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[],
            state_operations=[
                migrations.DeleteModel(name='CourseSchedule'),
                migrations.DeleteModel(name='CourseSession'),
            ],
        ),
    ]
