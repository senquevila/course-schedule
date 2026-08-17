"""CSV syllabus parser: rigid template, no flexible parsing."""
import csv
from io import StringIO
from typing import List, Dict

REQUIRED_HEADER = ['code', 'name', 'description', 'order']


class SyllabusCSVError(Exception):
    """Raised when the CSV doesn't match the required template."""


def parse_syllabus_csv(file_content: bytes) -> List[Dict]:
    """Parse a syllabus CSV matching the fixed template and return topic dicts."""
    try:
        text = file_content.decode('utf-8-sig')
    except UnicodeDecodeError as e:
        raise SyllabusCSVError(f'Error processing file: {e}')

    reader = csv.reader(StringIO(text))
    try:
        header = next(reader)
    except StopIteration:
        header = []

    if header != REQUIRED_HEADER:
        raise SyllabusCSVError(
            'CSV must have columns: code,name,description,order'
        )

    topics = []
    for row_num, row in enumerate(reader, start=2):
        if not row or not any(cell.strip() for cell in row):
            continue
        if len(row) != len(REQUIRED_HEADER):
            raise SyllabusCSVError(
                'CSV must have columns: code,name,description,order'
            )

        code, name, description, order_raw = (cell.strip() for cell in row)

        if not code or not name:
            raise SyllabusCSVError(f'Row {row_num}: code and name are required')

        try:
            order = int(order_raw)
            if order <= 0:
                raise ValueError
        except ValueError:
            raise SyllabusCSVError(f'Row {row_num}: order must be a positive integer')

        topics.append({
            'code': code,
            'name': name,
            'description': description,
            'order': order,
        })

    return topics
