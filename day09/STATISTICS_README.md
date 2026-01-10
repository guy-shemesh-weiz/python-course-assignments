# Course Statistics Script

This script analyzes course submission data from GitHub issues and generates comprehensive statistics about student submissions and deadlines.

## Features

The script provides the following statistics:

1. **Registered Students**: Count of unique students who have made submissions
2. **Open Issues**: Total number of currently open GitHub issues
3. **Oldest Open Issues**: The 10 issues that have been open the longest
4. **Missing Submissions**: Analysis of which students haven't submitted each assignment
5. **Late Submissions**: Identification and tracking of all submissions made after deadlines

## Data Sources

The script uses two input files:

- **subjects.txt**: Tab-separated values file containing GitHub issue data with columns:

  - Issue ID
  - Status (OPEN/CLOSED)
  - Title (containing student name and assignment info)
  - Empty column
  - Timestamp (ISO 8601 format)

- **course_readme.md**: Course README file containing assignment deadlines

## Requirements

- Python 3.7+
- pandas

Install dependencies:

```bash
pip install pandas
```

## Usage

Run the script from the command line:

```bash
python course_statistics.py
```

The script will:

1. Load the data from `subjects.txt` in the same directory
2. Parse assignment information and deadlines from the course structure
3. Display comprehensive statistics in the console
4. Generate a CSV summary file: `assignment_summary.csv`

## Output

The script produces:

### Console Output

- Detailed statistics organized by category
- Lists of missing students for each assignment
- Details on late submissions including days late

### CSV Output

- `assignment_summary.csv`: Summary table with submission counts and completion percentages

## Assignment Deadlines

The script includes the following assignment deadlines:

| Assignment               | Deadline         | Status           |
| ------------------------ | ---------------- | ---------------- |
| Day 01                   | 2025-11-01 22:00 | Completed        |
| Day 02                   | 2025-11-09 22:00 | Completed        |
| Day 03                   | 2025-11-16 22:00 | Completed        |
| Day 04                   | 2025-11-23 22:00 | Completed        |
| Day 05                   | 2025-11-29 22:00 | Completed        |
| Day 06                   | 2025-12-06 22:00 | Completed        |
| Day 07                   | TBD              | Not yet assigned |
| Day 08                   | 2025-12-30 22:00 | Completed        |
| Day 09                   | 2026-01-10 22:00 | Due              |
| Final Project Proposal   | 2026-01-11 22:00 | Due              |
| Final Project Submission | 2026-01-25 22:00 | Upcoming         |

## How It Works

### Name Extraction

The script extracts student names from GitHub issue titles using regex pattern matching. It looks for the pattern "by StudentName" in issue titles and normalizes names to their capitalized first name form.

### Assignment Detection

The script identifies assignments by searching for "Day##" or "Final Project" patterns in issue titles (case-insensitive).

### Late Detection

Submissions are compared against their corresponding deadline. If a submission timestamp is after the deadline, it's flagged as late with the number of days late calculated.

### Data Normalization

- Student names are normalized to first-name-only format with consistent capitalization
- Timestamps are converted to UTC for consistent comparison
- Assignment titles are standardized regardless of case variations in the original data

## Example Output

```
================================================================================
COURSE STATISTICS REPORT
================================================================================

1. REGISTERED STUDENTS: 30

2. OPEN ISSUES: 27

3. 10 OLDEST OPEN ISSUES:
   Issue #183: Day08 by Arad Zulti
   Opened: 2025-12-16 11:14:56+00:00 (24 days ago)
   ...

4. MISSING SUBMISSIONS BY ASSIGNMENT:

Day01:
  Submitted: 11/30
  Missing: 19/30
  Missing students:
    - Achinoam
    - Adi
    ...

5. LATE SUBMISSIONS:

Day01 (Deadline: 2025-11-01 22:00):
  - Raz: 14 days late
    Submitted: 2025-11-16 09:37:37+00:00
  ...
```

## Notes

- The script is designed for the WIS Python Programming Course
- All deadlines are hardcoded based on the course schedule
- Student count may vary slightly depending on data quality (e.g., students with multiple formatting variations in names)
- Day 07 assignment has no deadline in the current course schedule
