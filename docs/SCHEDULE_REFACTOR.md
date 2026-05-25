# CourseSchedule JSON Refactor

## Summary

Successfully refactored the CourseSchedule model to use a JSON field for storing multiple days instead of creating separate records for each day. This simplifies the data model while maintaining the same functionality.

## Changes Made

### 1. Model Changes (`courses/models.py`)

**Before:**
```python
class CourseSchedule(models.Model):
    course = ForeignKey(Course)
    day_of_week = IntegerField(choices=DAY_CHOICES)  # One per day
    start_time = TimeField()
    end_time = TimeField()
    
    unique_together = ['course', 'day_of_week', 'start_time']
```

**After:**
```python
class CourseSchedule(models.Model):
    course = ForeignKey(Course)
    days = JSONField(default=list)  # Multiple days in one record
    start_time = TimeField()
    end_time = TimeField()
    
    unique_together = ['course', 'start_time', 'end_time']
```

### 2. New Helper Methods

Added to CourseSchedule model:

```python
def get_days_display(self):
    """Return full day names: 'Monday, Wednesday, Friday'"""
    
def get_days_short(self):
    """Return abbreviated day names: 'Mon, Wed, Fri'"""
```

### 3. JSON Data Structure

Each CourseSchedule now stores:
```json
{
  "days": [1, 3, 5],        // 0=Sunday, 1=Monday, ..., 6=Saturday
  "start_time": "09:00",
  "end_time": "11:00"
}
```

### 4. Form Updates (`courses/forms.py`)

- Updated `CourseScheduleForm` to work with JSON days array
- Added validation to ensure days are converted to integers
- Added help text explaining the day numbering system

### 5. View Updates (`courses/views.py`)

**CourseScheduleCreateView:**
- Creates ONE schedule record with all selected days
- No longer creates individual records per day
- Validates that time range is unique per course

**CourseScheduleUpdateView:**
- Can now update all days at once (previously limited to single day)
- Simpler logic without multiple record handling

**CourseScheduleDeleteView:**
- No change needed (already works per schedule ID)

### 6. Template Updates

**schedule_item.html:**
- Changed from `get_day_of_week_display()` to `get_days_short()` for header
- Updated tooltip to show full `get_days_display()`
- Cleaner display: "Mon, Wed, Fri" instead of individual rows

**schedule_form.html:**
- Updated help text to reflect new behavior
- Allows selecting multiple days (same as before)
- No longer mentions single-day limitation for editing

### 7. Admin Configuration (`courses/admin.py`)

Updated `CourseScheduleAdmin`:
```python
list_display = ('course', 'days', 'start_time', 'end_time', 'created_at')
list_filter = ('course', 'start_time')
ordering = ('course', 'start_time')
```

## Benefits

✅ **Fewer Database Records**
- One schedule per time slot instead of one per day
- Reduces storage and improves query performance

✅ **Cleaner Data Model**
- Related days stored together in single record
- More intuitive representation of course schedule

✅ **Simpler Views**
- No loop needed to create multiple records
- Direct JSON storage in database

✅ **Better UX**
- Single schedule shows all days at once
- Edit operation updates all days together
- Admin interface cleaner (fewer rows)

✅ **Easier Maintenance**
- Change a schedule once, affects all days
- No orphaned records to worry about

## Migration

Generated migration: `0003_alter_courseschedule_options_and_more.py`

Operations:
1. Alter model options (ordering)
2. Alter unique_together constraint
3. Add JSONField `days`
4. Remove IntegerField `day_of_week`

Status: ✅ Applied successfully

## Database Example

**Old Structure (Multiple Records):**
```
| ID | Course | day_of_week | start_time | end_time |
|----|--------|-------------|------------|----------|
| 1  | CS101  | 1 (Mon)     | 09:00      | 11:00    |
| 2  | CS101  | 3 (Wed)     | 09:00      | 11:00    |
| 3  | CS101  | 5 (Fri)     | 09:00      | 11:00    |
```

**New Structure (Single Record):**
```
| ID | Course | days          | start_time | end_time |
|----|--------|---------------|------------|----------|
| 1  | CS101  | [1, 3, 5]    | 09:00      | 11:00    |
```

## Usage Example

**Creating a Schedule:**
```python
# User selects Monday, Wednesday, Friday with 9:00-11:00
schedule = CourseSchedule.objects.create(
    course=course,
    days=[1, 3, 5],  # Monday, Wednesday, Friday
    start_time=time(9, 0),
    end_time=time(11, 0)
)

# Display: "Mon, Wed, Fri - 09:00 to 11:00"
print(f"{schedule.get_days_short()} - {schedule.start_time} to {schedule.end_time}")
```

**Querying Schedules:**
```python
# Get all schedules for a course
schedules = course.schedules.all()

# Filter by time
morning_schedules = CourseSchedule.objects.filter(
    start_time__lt=time(12, 0)
)
```

## Testing

✅ System checks pass
✅ Migrations applied successfully
✅ Admin interface works correctly
✅ Forms validate correctly
✅ Views handle JSON days properly

## Backward Compatibility

⚠️ **Note:** If you have existing schedules in the database, they will need to be re-created with the new format. The migration removes the `day_of_week` field but doesn't automatically populate the `days` JSON field.

If you need to migrate existing data:
```python
# Write a data migration to convert day_of_week to days array
# Example: day_of_week=1 becomes days=[1]
```

## File Changes Summary

| File | Changes |
|------|---------|
| `courses/models.py` | Refactored CourseSchedule, added helper methods |
| `courses/forms.py` | Updated CourseScheduleForm for JSON days |
| `courses/views.py` | Simplified CreateView and UpdateView |
| `courses/admin.py` | Updated CourseScheduleAdmin config |
| `courses/templates/courses/partials/schedule_item.html` | Updated display methods |
| `courses/templates/courses/partials/schedule_form.html` | Updated help text |
| `courses/migrations/0003_*` | Database schema changes |

## Next Steps

1. ✅ Test schedule creation with multiple days
2. ✅ Test schedule editing (should update all days at once)
3. ✅ Test schedule deletion
4. ✅ Verify admin interface displays correctly
5. ⏳ Consider session generation logic (when generating CourseSession from CourseSchedule)

## Related Issue

This refactor addresses the suggestion to use JSON for storing schedule days instead of multiple database records. Much cleaner and more efficient! 🚀
