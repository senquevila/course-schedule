# Syllabus Import Feature

## Overview

Users can import course topics in bulk from a CSV file. The file must follow a fixed column template — no flexible parsing, no other file formats. Extracted rows can be reviewed and edited before importing.

## Features

✅ **File Format Support**
- CSV files (.csv) only
- File size limit: 10MB

✅ **Rigid Template**
- Fixed columns, in order: `code,name,description,order`
- Header row required, exact column names
- One topic per row

✅ **Review & Edit Before Import**
- Preview parsed rows
- Edit topic code, name, and description
- Adjust topic order
- Select which topics to include
- Validate before importing

✅ **One-Click Import**
- Create multiple topics at once
- Success notification with count

## CSV Template

```csv
code,name,description,order
T01,Introduction to Programming,Basic programming concepts,1
T02,Variables and Data Types,Understanding different data types,2
T03,Control Flow,if/else and loops,3
```

Rules:
- Header row is required and must match exactly: `code,name,description,order`
- `code` and `name` are required; `description` may be empty
- `order` must be a positive integer; rows are otherwise imported in file order
- Extra or missing columns → the whole file is rejected with an error

## How to Use

### Step 1: Upload CSV

1. Navigate to a course's Topics page
2. Click **"📄 Import from Syllabus"** button
3. Select a `.csv` file matching the template
4. Click **"Upload & Extract Topics"**

### Step 2: Review Topics

The system parses the CSV rows and displays them in editable cards:

```
[✓] Code: T01
    Name: Introduction to Programming
    Description: Basic programming concepts
    Order: 1

[✓] Code: T02
    Name: Variables and Data Types
    Description: Understanding different data types
    Order: 2
```

Features:
- **Checkbox**: Toggle to include/exclude topic
- **Code**: Topic identifier (from CSV, editable)
- **Name**: Topic title
- **Description**: Optional details
- **Order**: Sequence number

### Step 3: Import

1. Review and edit as needed
2. Check topics to import (uncheck to skip)
3. Click **"Import Selected Topics"**
4. Topics are created in your course

## Architecture

### Module: `courses/syllabus_parser.py`

**Function:**
- `parse_syllabus_csv(file_content: bytes)` - Reads the CSV, validates the header, and returns a list of `{code, name, description, order}` dicts. Raises a validation error if the header doesn't match the template.

### Forms: `courses/forms.py`

**SyllabusUploadForm**
- File input with validation
- Supported file type: `.csv` only
- Max file size: 10MB

**TopicReviewForm**
- Dynamic form fields for each parsed row
- Fields per topic: code, name, description, order, include checkbox
- Validation and cleanup methods
- Returns reviewed topics list

### Views: `courses/views.py`

**SyllabusUploadView**
- GET: Display upload form
- POST: Process file, parse rows, store in session

**SyllabusReviewView**
- GET: Display review form with parsed topics
- POST: Import selected topics into course

### Templates

**syllabus_upload.html**
- File upload form
- Link/description of the required CSV template
- Help text

**syllabus_review.html**
- Topic cards with editable fields
- Checkbox to include/exclude
- Import button
- Cancel option

### URL Routes

```python
path('courses/<int:course_id>/syllabus/upload/', 
     views.SyllabusUploadView.as_view(), 
     name='syllabus-upload')

path('courses/<int:course_id>/syllabus/review/', 
     views.SyllabusReviewView.as_view(), 
     name='syllabus-review')
```

## Data Flow

```
CSV Upload
    ↓
Validate Header (must match template exactly)
    ↓
Parse Rows
    ↓
Store in Session
    ↓
Display Review Form
    ↓
User Edits (optional)
    ↓
Validate Form
    ↓
Create Topics in Database
    ↓
Success Message + Redirect
```

## Error Handling

**File Upload Errors:**
- Wrong file extension → "Only .csv files are supported"
- File too large → "File size must not exceed 10MB"
- Read error → "Error processing file: {details}"

**Template Errors:**
- Missing/incorrect header → "CSV must have columns: code,name,description,order"
- Missing required field in a row → "Row {n}: code and name are required"
- Invalid order value → "Row {n}: order must be a positive integer"

**Import Errors:**
- No topics selected → "No topics selected for import"
- Database error → "Error creating topics: {details}"

## Testing the Feature

1. **Create a test CSV file** matching the template:
   ```csv
   code,name,description,order
   T01,Introduction to Programming,,1
   T02,Variables and Data Types,,2
   T03,Control Structures,,3
   T04,Functions,,4
   T05,Data Structures,,5
   ```

2. **Navigate to Topics page** of a course
3. **Click "Import from Syllabus"**
4. **Upload the file**
5. **Review extracted topics** - Should show 5 topics
6. **Edit if needed** - Change names, descriptions, order
7. **Click "Import"** - Topics created successfully
8. **Verify** - Topics appear in the topics list

## Limitations & Future Enhancements

### Current Limitations
- CSV only — no PDF, Word, or free-text syllabus parsing
- No automatic topic-to-session assignment

### Future Enhancements
- [ ] Downloadable CSV template from the upload page
- [ ] Automatic session assignment based on topics
- [ ] Bulk edit capabilities
- [ ] Import multiple files at once

## Files Created/Modified

**New Files:**
- `courses/syllabus_parser.py` - CSV parsing logic
- `courses/templatetags/__init__.py` - Template tags package
- `courses/templatetags/custom_filters.py` - Custom template filters
- `courses/templates/courses/syllabus_upload.html` - Upload form
- `courses/templates/courses/syllabus_review.html` - Review form
- `SYLLABUS_IMPORT.md` - This documentation

**Modified Files:**
- `courses/forms.py` - Added SyllabusUploadForm and TopicReviewForm
- `courses/views.py` - Added SyllabusUploadView and SyllabusReviewView
- `courses/urls.py` - Added routes for syllabus import
- `courses/templates/courses/topics_list.html` - Added import button
- `static/css/style.css` - Added .header-actions styling

## Dependencies

**Required:**
- Django 6.0.5+
- Python 3.13+

No optional dependencies — CSV parsing uses Python's built-in `csv` module.

## Example Workflow

### Scenario: Importing CS101 Topics

**Input File (topics.csv):**
```csv
code,name,description,order
T01,Arrays and Lists,,1
T02,Linked Lists and Pointers,,2
T03,Stacks and Queues,,3
T04,Trees and Graphs,,4
T05,Sorting Algorithms,,5
T06,Searching and Hashing,,6
```

**After Parsing (Review Page):**
```
[✓] T01 | Arrays and Lists | Order 1
[✓] T02 | Linked Lists and Pointers | Order 2
[✓] T03 | Stacks and Queues | Order 3
[✓] T04 | Trees and Graphs | Order 4
[✓] T05 | Sorting Algorithms | Order 5
[✓] T06 | Searching and Hashing | Order 6
```

**After Import:**
- 6 topics created in course
- Ready to attach materials
- Can assign to schedule

## Best Practices

1. **Prepare the CSV before upload:**
   - Use the exact header row: `code,name,description,order`
   - One topic per row
   - Keep `order` sequential

2. **Review parsed topics:**
   - Check topic names are correct
   - Verify order is sequential
   - Add descriptions if needed

3. **After import:**
   - Attach materials to topics
   - Assign topics to schedules
   - Verify topic sequence

4. **Use appropriate codes:**
   - T01, T02, T03 or your own scheme
   - Keep them short and memorable

## Support & Troubleshooting

**Q: My file is rejected**
A: Confirm it's a `.csv` and the header row is exactly `code,name,description,order`

**Q: Topics imported in wrong order**
A: Review page shows the order field - adjust before importing

**Q: Can't select topics to exclude**
A: Uncheck the checkbox next to topics you don't want

**Q: Missing descriptions**
A: `description` can be left empty in the CSV, or filled in during the review step

## Summary

The Syllabus Import feature streamlines course setup by importing topics from a rigid CSV template. Users can quickly populate a course with topics while retaining full control through the review and edit process.
</content>
