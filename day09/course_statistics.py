"""
Course Statistics Script
Generates statistics on issues and course submissions based on issues.txt and course_readme.md
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
import re

# Define assignment deadlines (excluding Day07 which is TBD)
DEADLINES = {
    "Day01": "2025-11-01 22:00",
    "Day02": "2025-11-09 22:00",
    "Day03": "2025-11-16 22:00",
    "Day04": "2025-11-23 22:00",
    "Day05": "2025-11-29 22:00",
    "Day06": "2025-12-06 22:00",
    "Day08": "2025-12-30 22:00",
    "Day09": "2026-01-10 22:00",
    "Final Project proposal": "2026-01-11 22:00",
    "Final Project submission": "2026-01-25 22:00",
}

def load_issues_data(filepath):
    """Load issues.txt data into a pandas DataFrame."""
    df = pd.read_csv(
        filepath,
        sep='\t',
        header=None,
        names=['issue_id', 'status', 'title', 'opened_date', 'closed_date']
    )
    # Convert dates to datetime (utc aware)
    df['opened_date'] = pd.to_datetime(df['opened_date'], utc=True)
    df['closed_date'] = pd.to_datetime(df['closed_date'], utc=True, errors='coerce')
    
    # opened_date = submission date (when student submitted)
    df['submission_timestamp'] = df['opened_date']
    return df

def extract_students_from_readme(readme_path):
    """Extract the list of registered students from the README file.
    
    Parses the ## Students markdown table section.
    Looks for the pattern: | [StudentName](url) at the beginning of each table row.
    """
    with open(readme_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    students = []
    in_students_section = False
    
    for i, line in enumerate(lines):
        # Check if we entered the Students section
        if '## Students' in line:
            in_students_section = True
            continue
        
        # Check if we left the Students section (hit another ## header)
        if in_students_section and line.startswith('##') and '## Students' not in line:
            break
        
        # Process table rows in the students section
        if in_students_section and line.startswith('|'):
            # Skip header rows
            if 'Home page' in line or '-----' in line or line.strip() == '|':
                continue
            
            # Extract first link from the row [Name](url)
            match = re.search(r'\|\s*\[([^\]]+)\]\([^)]*\)', line)
            if match:
                name = match.group(1).strip()
                # Make sure it's a real name (not empty, not a generic label like "repo")
                if name and name not in ['', '[]', 'repo', 'Repo'] and not name.startswith('http'):
                    students.append(name)
    
    return list(dict.fromkeys(students))  # Remove duplicates while preserving order

def find_student_in_title(title, registered_students):
    """Find which registered student is mentioned in the issue title.
    
    Uses fuzzy matching to handle variations in names.
    """
    # Skip meta-issues about missing submissions
    if title.lower().startswith('missing') and 'issues' in title.lower():
        return None
    
    title_lower = title.lower()
    
    best_match = None
    best_score = 0
    
    for student in registered_students:
        student_lower = student.lower()
        # First, try exact match (case-insensitive)
        if student_lower in title_lower:
            return student  # Exact match found
        
        # Try partial match with scoring
        # Check if first name appears
        first_name = student.split()[0].lower()
        last_name = student.split()[-1].lower() if len(student.split()) > 1 else ""
        
        # Score based on how much of the name appears
        score = 0
        if first_name in title_lower:
            score += 50
        if last_name and last_name in title_lower:
            score += 50
        
        # Check for fuzzy matches (last few chars)
        if len(first_name) > 2 and first_name in title_lower:
            score += 10
        
        if score > best_score:
            best_score = score
            best_match = student
    
    # Return the best match if confidence is reasonable
    if best_score >= 50:
        return best_match
    
    return None

def extract_days_from_title(title):
    """Extract all day numbers mentioned in the issue title.
    
    Returns a list of normalized day strings like ['Day01', 'Day02']
    """
    title_lower = title.lower()
    days = []
    
    # Check for Final Project first
    if 'final project submission' in title_lower:
        return ['Final Project submission']
    elif 'final project proposal' in title_lower or 'project proposal' in title_lower:
        return ['Final Project proposal']
    elif 'final project' in title_lower or 'project proposal' in title_lower:
        return ['Final Project proposal']  # Assume proposal if not explicit
    
    # Look for patterns like "day X and Y" or "day X and day Y"
    day_range_pattern = r'day\s*(\d+)\s+and\s+(?:day\s*)?(\d+)'
    range_match = re.search(day_range_pattern, title_lower, re.IGNORECASE)
    
    if range_match:
        day1 = range_match.group(1).zfill(2)
        day2 = range_match.group(2).zfill(2)
        days.append(f"Day{day1}")
        days.append(f"Day{day2}")
        return days
    
    # Otherwise, look for all Day patterns: day## or day# (case-insensitive)
    day_pattern = r'day\s*(\d+)'
    matches = re.finditer(day_pattern, title_lower, re.IGNORECASE)
    
    for match in matches:
        day_num = match.group(1).zfill(2)
        day_key = f"Day{day_num}"
        if day_key not in days:
            days.append(day_key)
    
    return days

def get_registered_students(readme_path):
    """Get the number of unique registered students from README."""
    students = extract_students_from_readme(readme_path)
    return len(students), students

def get_open_issues(df):
    """Get the number of open issues."""
    return len(df[df['status'] == 'OPEN'])

def get_oldest_open_issues(df, n=10):
    """Get the n oldest open issues."""
    open_issues = df[df['status'] == 'OPEN'].copy()
    open_issues = open_issues.sort_values('opened_date').head(n)
    return open_issues[['issue_id', 'title', 'opened_date', 'status']]

def analyze_assignment_submissions(df, registered_students):
    """Analyze submission status for each assignment.
    
    Strategy: For each issue, extract the student and all days mentioned.
    """
    assignment_status = {}
    unparseable_issues = []
    
    # Initialize tracking for all assignments
    for assignment in sorted(DEADLINES.keys()):
        assignment_status[assignment] = {
            'submitted_students': set(),
            'late_submissions': []
        }
    
    # Process each issue
    for idx, row in df.iterrows():
        title = row['title']
        
        # Extract student from title
        student = find_student_in_title(title, registered_students)
        
        # Extract days from title
        days = extract_days_from_title(title)
        
        # Check if we couldn't parse this issue
        if not student and days:
            unparseable_issues.append({
                'issue_id': row['issue_id'],
                'title': title,
                'reason': 'Could not identify student'
            })
        elif not days:
            unparseable_issues.append({
                'issue_id': row['issue_id'],
                'title': title,
                'reason': 'Could not identify assignment days'
            })
        else:
            # We have both student and days - record submissions
            for day in days:
                if day in assignment_status:
                    assignment_status[day]['submitted_students'].add(student)
                    
                    # Check if late
                    if day in DEADLINES and DEADLINES[day]:
                        deadline_dt = pd.to_datetime(DEADLINES[day], utc=True)
                        if row['submission_timestamp'] > deadline_dt:
                            assignment_status[day]['late_submissions'].append({
                                'student': student,
                                'submitted': row['submission_timestamp'],
                                'deadline': deadline_dt,
                                'days_late': (row['submission_timestamp'] - deadline_dt).days
                            })
    
    # Convert to the format expected by print_statistics
    formatted_status = {}
    for assignment in sorted(DEADLINES.keys()):
        submitted_students = assignment_status[assignment]['submitted_students']
        missing_students = set(registered_students) - submitted_students
        
        formatted_status[assignment] = {
            'submitted': len(submitted_students),
            'missing': len(missing_students),
            'missing_students': list(missing_students),
            'total_students': len(registered_students),
            'late_submissions': assignment_status[assignment]['late_submissions']
        }
    
    return formatted_status, unparseable_issues

def print_statistics(df, readme_path, filepath):
    """Print all statistics."""
    print("=" * 80)
    print("COURSE STATISTICS REPORT")
    print("=" * 80)
    print()
    
    # 1. Number of registered students
    num_students, students = get_registered_students(readme_path)
    print(f"1. REGISTERED STUDENTS: {num_students}")
    print()
    
    # 2. Number of open issues
    num_open = get_open_issues(df)
    print(f"2. OPEN ISSUES: {num_open}")
    print()
    
    # 3. 10 oldest open issues
    print("3. 10 OLDEST OPEN ISSUES:")
    print("-" * 80)
    oldest_open = get_oldest_open_issues(df, 10)
    for idx, row in oldest_open.iterrows():
        days_open = (datetime.now(row['opened_date'].tz) - row['opened_date']).days
        print(f"   Issue #{row['issue_id']}: {row['title']}")
        print(f"   Opened: {row['opened_date']} ({days_open} days ago)")
    print()
    
    # 4. Missing submissions analysis
    print("4. MISSING SUBMISSIONS BY ASSIGNMENT:")
    print("-" * 80)
    assignment_status, unparseable_issues = analyze_assignment_submissions(df, students)
    
    for assignment in sorted(assignment_status.keys()):
        status = assignment_status[assignment]
        print(f"\n{assignment}:")
        print(f"  Submitted: {status['submitted']}/{status['total_students']}")
        print(f"  Missing: {status['missing']}/{status['total_students']}")
        
        if status['missing_students']:
            print(f"  Missing students:")
            for student in sorted(status['missing_students']):
                print(f"    - {student}")
    
    print()
    
    # 5. Late submissions
    print("5. LATE SUBMISSIONS:")
    print("-" * 80)
    has_late = False
    for assignment in sorted(assignment_status.keys()):
        late = assignment_status[assignment]['late_submissions']
        if late:
            has_late = True
            deadline = DEADLINES.get(assignment)
            print(f"\n{assignment} (Deadline: {deadline}):")
            for late_sub in sorted(late, key=lambda x: x['days_late'], reverse=True):
                print(f"  - {late_sub['student']}: {late_sub['days_late']} days late")
                print(f"    Submitted: {late_sub['submitted']}")
    
    if not has_late:
        print("No late submissions found!")
    
    print()
    
    # 6. Unparseable issues
    if unparseable_issues:
        print("6. ISSUES THAT COULDN'T BE PARSED:")
        print("-" * 80)
        for issue in unparseable_issues:
            print(f"\nIssue #{issue['issue_id']}: {issue['title']}")
            print(f"  Reason: {issue['reason']}")
    
    print()
    print("=" * 80)
    
    return assignment_status, unparseable_issues

def main():
    """Main function."""
    # Get the directory of this script
    script_dir = Path(__file__).parent
    issues_file = script_dir / 'issues.txt'
    readme_file = script_dir / 'course_readme.md'
    
    if not issues_file.exists():
        print(f"Error: {issues_file} not found")
        return
    
    if not readme_file.exists():
        print(f"Error: {readme_file} not found")
        return
    
    # Load data
    df = load_issues_data(issues_file)
    
    # Print statistics
    assignment_status, unparseable_issues = print_statistics(df, readme_file, issues_file)
    
    # Get registered students for CSV
    num_students, students = get_registered_students(readme_file)
    
    # Create summary dataframe
    summary_data = []
    for assignment in sorted(DEADLINES.keys()):
        status = assignment_status[assignment]
        summary_data.append({
            'Assignment': assignment,
            'Submitted': status['submitted'],
            'Missing': status['missing'],
            'Total': status['total_students'],
            'Completion %': f"{(status['submitted']/status['total_students']*100):.1f}%" if status['total_students'] > 0 else "N/A"
        })
    
    summary_df = pd.DataFrame(summary_data)
    summary_csv = script_dir / 'assignment_summary.csv'
    summary_df.to_csv(summary_csv, index=False)
    print(f"\nSummary saved to: {summary_csv}")
    
    # Save unparseable issues for review
    if unparseable_issues:
        unparseable_csv = script_dir / 'unparseable_issues.csv'
        unparseable_df = pd.DataFrame(unparseable_issues)
        unparseable_df.to_csv(unparseable_csv, index=False)
        print(f"Unparseable issues saved to: {unparseable_csv}")

if __name__ == '__main__':
    main()
