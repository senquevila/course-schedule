"""
Syllabus parser module for extracting topics from various document formats
"""
import re
from typing import List, Dict, Tuple
import mimetypes


class SyllabusParser:
    """Base parser for extracting topics from syllabus documents"""

    def __init__(self, content: str, file_type: str = None):
        self.content = content
        self.file_type = file_type

    def parse(self) -> List[Dict[str, str]]:
        """
        Parse syllabus content and extract topics.
        Returns list of dicts with 'code', 'name', and 'description'
        """
        # Try different parsing strategies
        topics = self._parse_numbered_list()
        if not topics:
            topics = self._parse_bullet_list()
        if not topics:
            topics = self._parse_lines_with_colon()
        if not topics:
            topics = self._parse_simple_lines()

        return topics

    def _parse_numbered_list(self) -> List[Dict[str, str]]:
        """Parse numbered list format: 1. Topic Name, 2. Topic Name, etc."""
        topics = []
        # Pattern: number followed by optional closing paren/period, then text
        pattern = r'^\s*(\d+)[.):\s]+(.+?)(?:\s*[-–]\s*(.+?))?$'

        for i, line in enumerate(self.content.split('\n')):
            match = re.match(pattern, line.strip())
            if match:
                order_num = int(match.group(1))
                name = match.group(2).strip()
                description = match.group(3).strip() if match.group(3) else ''

                if name:
                    topics.append({
                        'code': f'T{order_num:02d}',
                        'name': name,
                        'description': description,
                        'order': order_num
                    })

        return topics

    def _parse_bullet_list(self) -> List[Dict[str, str]]:
        """Parse bullet list format: - Topic, • Topic, * Topic, etc."""
        topics = []
        order = 1

        # Pattern: bullet character followed by text
        pattern = r'^\s*[-•*+]\s+(.+?)(?:\s*[-–:]\s*(.+?))?$'

        for line in self.content.split('\n'):
            match = re.match(pattern, line.strip())
            if match:
                name = match.group(1).strip()
                description = match.group(2).strip() if match.group(2) else ''

                if name:
                    topics.append({
                        'code': f'T{order:02d}',
                        'name': name,
                        'description': description,
                        'order': order
                    })
                    order += 1

        return topics

    def _parse_lines_with_colon(self) -> List[Dict[str, str]]:
        """Parse format with colon separator: Code: Name or Name: Description"""
        topics = []
        order = 1

        for line in self.content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Look for patterns like "Topic 1: Name" or "Chapter 5: Title - Description"
            if ':' in line:
                parts = line.split(':', 1)
                if len(parts) == 2:
                    first_part = parts[0].strip()
                    second_part = parts[1].strip()

                    # Check if first part is a code/number
                    if any(char.isdigit() for char in first_part):
                        name = second_part.split('-')[0].strip()
                        description = second_part.split('-', 1)[1].strip() if '-' in second_part else ''

                        if name:
                            topics.append({
                                'code': f'T{order:02d}',
                                'name': name,
                                'description': description,
                                'order': order
                            })
                            order += 1
                    else:
                        # Simple colon separator, treat first part as name
                        if first_part and second_part:
                            topics.append({
                                'code': f'T{order:02d}',
                                'name': first_part,
                                'description': second_part[:200],
                                'order': order
                            })
                            order += 1

        return topics

    def _parse_simple_lines(self) -> List[Dict[str, str]]:
        """Fallback: parse simple lines, filtering empty lines and headers"""
        topics = []
        order = 1

        for line in self.content.split('\n'):
            line = line.strip()

            # Skip empty lines
            if not line:
                continue

            # Skip common headers/metadata
            if any(header in line.lower() for header in [
                'syllabus', 'course', 'table of contents', 'topics', 'contents',
                'outline', 'schedule', 'week', 'module', 'unit', 'chapter',
                'introduction', 'overview', 'description', 'objective', 'goal'
            ]):
                continue

            # Skip lines with special characters only
            if not any(char.isalnum() for char in line):
                continue

            # Skip very short lines (likely headers)
            if len(line) < 5:
                continue

            # Add as topic
            topics.append({
                'code': f'T{order:02d}',
                'name': line[:100],  # Limit name length
                'description': '',
                'order': order
            })
            order += 1

            # Limit number of topics from simple parsing
            if order > 20:
                break

        return topics


class TextParser(SyllabusParser):
    """Parser for plain text files"""

    def parse(self) -> List[Dict[str, str]]:
        return super().parse()


class PDFParser(SyllabusParser):
    """Parser for PDF files"""

    def parse(self) -> List[Dict[str, str]]:
        # PDF content is already extracted to text before reaching here
        return super().parse()


class DocxParser(SyllabusParser):
    """Parser for Word documents"""

    def parse(self) -> List[Dict[str, str]]:
        # DOCX content is already extracted to text before reaching here
        return super().parse()


def extract_text_from_file(file_content: bytes, filename: str) -> str:
    """
    Extract text content from different file formats
    """
    file_type = mimetetype_from_filename(filename)

    if file_type == 'text/plain':
        return file_content.decode('utf-8', errors='ignore')

    elif file_type == 'application/pdf':
        return extract_text_from_pdf(file_content)

    elif file_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                       'application/msword']:
        return extract_text_from_docx(file_content)

    else:
        # Try UTF-8 decoding as fallback
        return file_content.decode('utf-8', errors='ignore')


def mimetetype_from_filename(filename: str) -> str:
    """Get MIME type from filename"""
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or 'text/plain'


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF file"""
    try:
        import PyPDF2
        from io import BytesIO

        pdf_reader = PyPDF2.PdfReader(BytesIO(file_content))
        text = []

        for page in pdf_reader.pages:
            text.append(page.extract_text())

        return '\n'.join(text)
    except ImportError:
        return "PDF support requires PyPDF2. Please install: pip install PyPDF2"
    except Exception as e:
        return f"Error extracting PDF: {str(e)}"


def extract_text_from_docx(file_content: bytes) -> str:
    """Extract text from DOCX file"""
    try:
        from docx import Document
        from io import BytesIO

        doc = Document(BytesIO(file_content))
        text = []

        for para in doc.paragraphs:
            text.append(para.text)

        return '\n'.join(text)
    except ImportError:
        return "DOCX support requires python-docx. Please install: pip install python-docx"
    except Exception as e:
        return f"Error extracting DOCX: {str(e)}"


def parse_syllabus(file_content: bytes, filename: str) -> List[Dict[str, str]]:
    """
    Main function to parse a syllabus file and extract topics
    """
    # Extract text from file
    text = extract_text_from_file(file_content, filename)

    # Parse extracted text
    parser = SyllabusParser(text, filename)
    topics = parser.parse()

    return topics
