# Syllabus Import Feature

## Overview

Users can now import course topics directly from a syllabus document (PDF, Word, or text file). The system automatically extracts topics and allows for review and editing before importing them into the course.

## Features

✅ **Multiple File Format Support**
- Text files (.txt)
- PDF documents (.pdf)
- Word documents (.docx, .doc)
- File size limit: 10MB

✅ **Intelligent Topic Extraction**
- Numbered lists (1. Topic, 2. Topic)
- Bullet points (- Topic, • Topic, * Topic)
- Colon-separated format (Topic: Description)
- Flexible parsing for various syllabus formats

✅ **Review & Edit Before Import**
- Preview extracted topics
- Edit topic code, name, and description
- Adjust topic order
- Select which topics to include
- Validate before importing

✅ **One-Click Import**
- Create multiple topics at once
- Automatic code generation (T01, T02, etc.)
- Success notification with count

## How to Use

### Step 1: Upload Syllabus

1. Navigate to a course's Topics page
2. Click **"📄 Import from Syllabus"** button
3. Select a document from your computer
4. Click **"Upload & Extract Topics"**

### Step 2: Review Topics

The system extracts topics and displays them in editable cards:

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
- **Code**: Topic identifier (auto-generated)
- **Name**: Topic title
- **Description**: Optional details
- **Order**: Sequence number

### Step 3: Import

1. Review and edit as needed
2. Check topics to import (uncheck to skip)
3. Click **"Import Selected Topics"**
4. Topics are created in your course

## Supported Syllabus Formats

### Format 1: Numbered List
```
1. Introduction to Programming
2. Variables and Data Types
3. Control Flow (if/else)
4. Functions and Methods
5. Data Structures
```

### Format 2: Numbered with Descriptions
```
1. Arrays - Basic array concepts and operations
2. Linked Lists - Introduction to linked list structures
3. Stack and Queue - LIFO and FIFO principles
4. Trees - Hierarchical data organization
5. Graphs - Network representations
```

### Format 3: Bullet Points
```
- Introduction to Python
- Data Types and Variables
- Operators and Expressions
- Control Structures
- Functions and Modules
```

### Format 4: Colon Separator
```
Topic 1: Introduction to Programming
Topic 2: Variables and Data Types
Chapter 3: Control Flow Structures
Module 4: Function Definition and Calling
Unit 5: Working with Collections
```

## Architecture

### Module: `courses/syllabus_parser.py`

**Main Classes:**
- `SyllabusParser` - Base parser with multiple extraction strategies
- `TextParser` - Plain text file parser
- `PDFParser` - PDF document parser
- `DocxParser` - Word document parser

**Key Methods:**
- `parse()` - Main extraction method
- `_parse_numbered_list()` - Extract from numbered lists
- `_parse_bullet_list()` - Extract from bullet points
- `_parse_lines_with_colon()` - Extract from colon-separated format
- `_parse_simple_lines()` - Fallback simple line parsing

**Functions:**
- `extract_text_from_file()` - Convert file to text
- `extract_text_from_pdf()` - PDF text extraction
- `extract_text_from_docx()` - Word document text extraction
- `parse_syllabus()` - Main entry point

### Forms: `courses/forms.py`

**SyllabusUploadForm**
- File input with validation
- Supported file types: .txt, .pdf, .docx, .doc
- Max file size: 10MB

**TopicReviewForm**
- Dynamic form fields for each extracted topic
- Fields per topic: code, name, description, order, include checkbox
- Validation and cleanup methods
- Returns reviewed topics list

### Views: `courses/views.py`

**SyllabusUploadView**
- GET: Display upload form
- POST: Process file, extract topics, store in session

**SyllabusReviewView**
- GET: Display review form with extracted topics
- POST: Import selected topics into course

### Templates

**syllabus_upload.html**
- File upload form
- Format recommendations
- Example formats
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

## Parsing Strategy

The system uses a fallback approach:

1. **Try Numbered List** - Matches `1. Topic`, `1) Topic`, `1: Topic`
2. **Try Bullet List** - Matches `- Topic`, `• Topic`, `* Topic`, `+ Topic`
3. **Try Colon Format** - Matches `Code: Name` or `Name: Description`
4. **Fallback Simple** - Parse any non-empty, meaningful lines

## Data Flow

```
File Upload
    ↓
Extract Text (based on file type)
    ↓
Parse Text (extraction strategies)
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
- Invalid file type → "File type not supported"
- File too large → "File size must not exceed 10MB"
- Read error → "Error processing file: {details}"

**Parsing Errors:**
- No topics found → "No topics could be extracted from the document"
- Parse error → "Error processing file: {details}"

**Import Errors:**
- No topics selected → "No topics selected for import"
- Database error → "Error creating topics: {details}"

## Requirements for PDF & DOCX Support

To support PDF and Word documents, install optional dependencies:

```bash
pip install PyPDF2 python-docx
```

If not installed:
- PDF: Returns error message
- DOCX: Returns error message
- TXT: Works without additional packages

## Testing the Feature

1. **Create a test syllabus file:**
   ```
   1. Introduction to Programming
   2. Variables and Data Types
   3. Control Structures
   4. Functions
   5. Data Structures
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
- No OCR for scanned PDFs (text-based PDFs only)
- Limited to simple, linear list extraction
- No multi-level hierarchy support
- No automatic topic-to-session assignment

### Future Enhancements
- [ ] OCR support for scanned documents
- [ ] Table of contents extraction
- [ ] Hierarchical topic structure (chapters/sections/topics)
- [ ] Topic grouping by sections
- [ ] Automatic session assignment based on topics
- [ ] Custom extraction rules per course type
- [ ] AI-powered extraction using Claude API
- [ ] Drag-to-reorder in review step
- [ ] Bulk edit capabilities
- [ ] Import multiple files at once

## Files Created/Modified

**New Files:**
- `courses/syllabus_parser.py` - Document parsing logic
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

**Optional (for PDF & DOCX support):**
- PyPDF2 (for PDF text extraction)
- python-docx (for Word document support)

## Example Workflow

### Scenario: Importing CS101 Topics

**Input File (Syllabus.txt):**
```
CS101 - Data Structures

Topics:
1. Arrays and Lists
2. Linked Lists and Pointers
3. Stacks and Queues
4. Trees and Graphs
5. Sorting Algorithms
6. Searching and Hashing
```

**After Extraction (Review Page):**
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

1. **Format syllabus before upload:**
   - Use numbered or bullet lists
   - One topic per line
   - Avoid extra formatting

2. **Review extracted topics:**
   - Check topic names are correct
   - Verify order is sequential
   - Add descriptions if needed

3. **After import:**
   - Attach materials to topics
   - Assign topics to schedules
   - Verify topic sequence

4. **Use appropriate codes:**
   - T01, T02, T03 (auto-generated)
   - Or customize with meaningful codes
   - Keep them short and memorable

## Support & Troubleshooting

**Q: PDF extraction not working**
A: Install PyPDF2: `pip install PyPDF2`

**Q: No topics extracted**
A: Check format - try numbered list (1. Topic) or bullets (- Topic)

**Q: Topics imported in wrong order**
A: Review page shows order field - adjust before importing

**Q: Can't select topics to exclude**
A: Uncheck the checkbox next to topics you don't want

**Q: Missing descriptions**
A: Add them in the review step before importing

## Summary

The Syllabus Import feature streamlines course setup by automating topic extraction from documents. Users can quickly populate a course with topics while retaining full control through the review and edit process.
