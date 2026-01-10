# Course Statistics Script - Summary

## Overview

I've created a comprehensive Python script that analyzes course submission data from GitHub issues. The script generates detailed statistics about student registrations, open issues, missing submissions, and late submissions.

## Files Created

1. **course_statistics.py** - Main analysis script
2. **STATISTICS_README.md** - Complete documentation
3. **assignment_summary.csv** - Summary data in CSV format (auto-generated)

## Key Features

### 1. **Registered Students Count**

- Extracts unique student names from issue titles
- Normalizes names for consistency
- Current count: 30 students

### 2. **Open Issues Tracking**

- Lists all currently open GitHub issues
- Shows the 10 oldest open issues with timestamps
- Indicates how long each issue has been open

### 3. **Missing Submissions Analysis**

- Tracks which students haven't submitted each assignment
- Provides submission counts (submitted/total)
- Lists missing students for each assignment

Assignment completion rates:

- Day 01: 36.7% (11/30)
- Day 02: 76.7% (23/30)
- Day 03: 63.3% (19/30)
- Day 04: 86.7% (26/30)
- Day 05: 83.3% (25/30)
- Day 06: 76.7% (23/30)
- Day 07: 0.0% (0/30) - Assignment TBD
- Day 08: 66.7% (20/30)
- Day 09: 0.0% (0/30) - Due Jan 10, 2026
- Final Project Proposal: 43.3% (13/30) - Due Jan 11, 2026
- Final Project Submission: 0.0% (0/30) - Due Jan 25, 2026

### 4. **Late Submissions Tracking**

- Compares submission timestamps against deadlines
- Calculates days late for each submission
- Organizes by assignment and student
- Shows exact submission timestamps

Example findings:

- Day 01: Some students submitted 14+ days late
- Day 02-06: Various submissions 5-10+ days late
- Day 08: Recent submissions 1-4 days late

## How to Use

```bash
python course_statistics.py
```

The script will:

1. Read `subjects.txt` from the same directory
2. Parse deadlines from the course structure (hardcoded)
3. Generate console output with all statistics
4. Create `assignment_summary.csv` with a summary table

## Data Sources Used

- **subjects.txt**: GitHub issue data (tab-separated)

  - Issue ID, Status (OPEN/CLOSED), Title, Timestamp

- **course_readme.md**: Course deadlines and schedule
  - Parsed assignment dates and deadlines

## Key Insights from Current Data

1. **Best-performing assignments**: Day 04 (86.7%) and Day 05 (83.3%)
2. **Lowest-performing assignments**: Day 01 (36.7%), Day 09 (0%, future deadline)
3. **Open issues**: 27 issues still open, oldest from Dec 16, 2025
4. **Late submission patterns**: Most common among early assignments
5. **Project status**: 43.3% have submitted proposals, 0% submitted final projects (still pending)

## Technical Details

- **Language**: Python 3.7+
- **Dependencies**: pandas
- **Data parsing**: Regex for student name and assignment extraction
- **Timezone handling**: UTC normalization for accurate comparisons
- **CSV export**: Summary statistics saved for further analysis

## Customization

To modify assignment deadlines, edit the `DEADLINES` dictionary in `course_statistics.py`:

```python
DEADLINES = {
    "Day01": "2025-11-01 22:00",
    "Day02": "2025-11-09 22:00",
    # ... etc
}
```

To add new assignments, follow the same format and run the script to regenerate statistics.
