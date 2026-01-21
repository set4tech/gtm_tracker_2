import csv
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from app.models import GTMActivity

def parse_date(date_str: Optional[str]) -> Optional[datetime.date]:
    """
    Parse date string in various formats.
    Returns None if date_str is None or empty.
    """
    if not date_str or date_str.strip() == "":
        return None

    date_str = date_str.strip()

    # Common date formats to try
    date_formats = [
        "%Y-%m-%d",           # 2024-01-15
        "%m/%d/%Y",           # 01/15/2024
        "%d/%m/%Y",           # 15/01/2024
        "%B %d, %Y",          # January 15, 2024
        "%b %d, %Y",          # Jan 15, 2024
        "%Y/%m/%d",           # 2024/01/15
        "%d-%m-%Y",           # 15-01-2024
    ]

    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue

    return None

def parse_int(value: Optional[str]) -> Optional[int]:
    """
    Parse integer value, return None if empty or invalid.
    """
    if not value or value.strip() == "":
        return None
    try:
        return int(value.strip())
    except ValueError:
        return None

def parse_float(value: Optional[str]) -> Optional[float]:
    """
    Parse float value, return None if empty or invalid.
    """
    if not value or value.strip() == "":
        return None
    try:
        return float(value.strip())
    except ValueError:
        return None

def import_csv_to_db(db: Session, csv_file_path: str) -> int:
    """
    Import activities from CSV file to database.
    Returns number of activities imported.
    """
    imported_count = 0

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            # Map CSV columns to database fields
            # Handle both CSV column names and database field names
            activity = GTMActivity(
                hypothesis=row.get('Hypothesis', '').strip() or row.get('hypothesis', '').strip(),
                audience=row.get('Audience', '').strip() or row.get('audience', '').strip() or None,
                channels=row.get('Channels', '').strip() or row.get('channels', '').strip() or None,
                description=row.get('Description/Activities', '').strip() or row.get('Description', '').strip() or row.get('description', '').strip() or None,
                list_size=parse_int(row.get('List size') or row.get('List Size') or row.get('list_size', '')),
                meetings_booked=parse_int(row.get('Meetings booked') or row.get('Meetings Booked') or row.get('meetings_booked', '')),
                start_date=parse_date(row.get('T1 Date or Start') or row.get('Start Date') or row.get('start_date', '')),
                end_date=parse_date(row.get('End Date') or row.get('end_date', '')),
                est_weekly_hrs=parse_float(row.get('Est weekly hrs') or row.get('Est Weekly Hrs') or row.get('est_weekly_hrs', ''))
            )

            db.add(activity)
            imported_count += 1

        db.commit()

    return imported_count
