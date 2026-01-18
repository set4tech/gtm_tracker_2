"""
Import GTM experiments data from CSV and markdown files
"""
import csv
import os
import re
import glob
from datetime import datetime
from app.storage import storage


def parse_date(date_str):
    """Parse various date formats"""
    if not date_str or not date_str.strip():
        return None

    date_str = date_str.strip()

    # Try different formats
    formats = [
        "%B %d, %Y",  # December 19, 2025
        "%Y-%m-%d",   # 2025-12-19
        "%m/%d/%Y",   # 12/19/2025
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return date_str  # Return as-is if can't parse


def find_md_file_for_hypothesis(hypothesis, data_dir='data'):
    """Find the markdown file for a given hypothesis"""
    if not hypothesis:
        return None

    # Clean hypothesis for filename matching
    hypothesis_clean = hypothesis.strip()

    # Find all .md files
    md_files = glob.glob(os.path.join(data_dir, '*.md'))

    for md_file in md_files:
        basename = os.path.basename(md_file)
        # Extract hypothesis from filename (everything before the Notion ID)
        # Format: "hypothesis NOTION_ID.md"
        match = re.match(r'^(.+?)\s+([0-9a-f]{32})\.md$', basename)
        if match:
            file_hypothesis = match.group(1).strip()
            if file_hypothesis == hypothesis_clean:
                return md_file

    return None


def read_md_content(md_file):
    """Read additional content from markdown file"""
    if not md_file or not os.path.exists(md_file):
        return None

    try:
        with open(md_file, 'r', encoding='utf-8') as f:
            content = f.read()

            # Extract everything after the structured metadata
            # Look for sections like "Copy:" or additional paragraphs
            lines = content.split('\n')

            # Skip the header and metadata lines
            additional_content = []
            in_additional = False

            for line in lines:
                # Start collecting after metadata
                if line.strip() and not line.startswith('#') and not ':' in line[:30]:
                    in_additional = True

                if in_additional:
                    additional_content.append(line)

            result = '\n'.join(additional_content).strip()
            return result if result else None

    except Exception as e:
        print(f"Error reading {md_file}: {e}")
        return None


def import_csv_data(csv_path='data/table.csv', data_dir='data'):
    """Import GTM experiments from CSV and markdown files"""

    if not os.path.exists(csv_path):
        print(f"CSV file not found: {csv_path}")
        return 0

    imported = 0

    with open(csv_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)

        for row in reader:
            hypothesis = row.get('Hypothesis', '').strip()

            if not hypothesis:
                continue  # Skip empty rows

            # Find corresponding .md file
            md_file = find_md_file_for_hypothesis(hypothesis, data_dir)
            additional_content = read_md_content(md_file) if md_file else None

            # Combine description from CSV and additional content
            description_parts = []
            if row.get('Description/Activities'):
                description_parts.append(row['Description/Activities'].strip())
            if additional_content:
                description_parts.append(additional_content)

            description = '\n\n'.join(description_parts) if description_parts else None

            # Parse numeric fields
            list_size = None
            try:
                if row.get('List size') and row['List size'].strip():
                    list_size = int(row['List size'].strip())
            except ValueError:
                pass

            meetings_booked = None
            try:
                if row.get('Meetings booked') and row['Meetings booked'].strip():
                    meetings_booked = int(row['Meetings booked'].strip())
            except ValueError:
                pass

            # Create activity
            activity = storage.create(
                hypothesis=hypothesis,
                audience=row.get('Audience', '').strip() or None,
                channels=row.get('Channels', '').strip() or None,
                description=description,
                list_size=list_size,
                meetings_booked=meetings_booked,
                start_date=parse_date(row.get('T1 Date or Start', '')),
                end_date=parse_date(row.get('End Date', ''))
            )

            imported += 1
            print(f"Imported: #{activity.id} - {hypothesis[:50]}...")

    return imported


if __name__ == '__main__':
    # Run import
    count = import_csv_data()
    print(f"\nImported {count} activities")
