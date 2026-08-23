# Diversio HRIS Import Preview

A small Django application that previews an HRIS CSV before employee or reporting data is persisted.

The application:

* Accepts an HRIS CSV upload from a browser.
* Parses standard CSV files, including quoted values such as names containing commas.
* Supports UTF-8 files with or without a byte-order mark (BOM).
* Trims surrounding whitespace from every value.
* Normalizes email addresses to lowercase.
* Keeps employee IDs case-sensitive.
* Validates required employee IDs and email addresses.
* Detects duplicate employee IDs and email addresses.
* Reports row-level validation errors with source row numbers.
* Identifies root employees who have no manager.
* Identifies managers and their direct-report counts.
* Identifies employees that participate directly in reporting cycles.
* Handles missing managers, conflicting manager references, and self-management.
* Performs analysis in memory without persisting employee or relationship data to the database.

## Requirements

* Python 3.11+
* Django 6.x

## Setup

Clone or extract the project and open a terminal in the project directory.

### 1. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
```

Activate the virtual environment:

```powershell
venv\Scripts\activate
```

### 2. Install dependencies

```powershell
pip install -r requirements.txt
```

### 3. Apply Django migrations

```powershell
python manage.py migrate
```

The application does not persist employee or reporting relationship data. Django's default database is only used for the framework's normal requirements.

## Run the Application

Start the Django development server:

```powershell
python manage.py runserver
```

Open the application in a browser:

```text
http://127.0.0.1:8000/
```

Upload the supplied `sample_hris.csv` file to view the HRIS import preview.

## Run Tests

Run the automated tests with:

```powershell
python manage.py test
```

The test suite covers important parsing, validation, manager relationship, and hierarchy behavior.

## Application Flow

The application processes the uploaded CSV in the following stages:

```text
CSV Upload
    ↓
CSV Parsing
    ↓
Value Normalization
    ↓
Identity Validation
    ↓
Employee Indexing
    ↓
Manager Resolution
    ↓
Hierarchy Analysis
    ↓
Cycle Detection
    ↓
Preview Results
```

### 1. CSV Parsing

The application uses Python's standard CSV parser so that normal CSV formatting is handled correctly, including quoted values containing commas.

UTF-8 files with and without a BOM are supported.

### 2. Normalization

Before validation and analysis:

* Surrounding whitespace is removed from every value.
* `email` is converted to lowercase.
* `manager_email` is converted to lowercase.
* Employee IDs remain case-sensitive.

### 3. Identity Validation

`employee_id` and `email` are required.

Each must be unique after normalization.

Rows containing duplicate employee IDs or duplicate email addresses are considered invalid and are excluded from manager lookup and hierarchy analysis.

### 4. Manager Resolution

Manager references are resolved after all valid employees have been indexed, so managers can appear either before or after their reports in the CSV.

The rules are:

* Both manager fields blank → employee is a root.
* Only `manager_id` supplied → manager is looked up by employee ID.
* Only `manager_email` supplied → manager is looked up by normalized email.
* Both supplied → both references must identify the same employee.
* Missing manager → validation error.
* Conflicting manager references → validation error.
* Employee managing themselves → validation error.

An employee with a manager error remains an accepted employee, but no reporting relationship is created and the employee is not classified as a root.

## Reporting Cycles

Reporting cycles are detected by following each employee's manager chain.

For example:

```text
Employee A
    ↓
Employee B
    ↓
Employee A
```

Both Employee A and Employee B are members of a reporting cycle.

An employee that only reports into a cycle is not considered cyclic.

For example:

```text
Employee C
    ↓
Employee A
    ↓
Employee B
    ↓
Employee A
```

Only Employee A and Employee B are cycle members. Employee C is not.

## Complexity

Employee IDs and normalized email addresses are stored in dictionaries for efficient lookup.

For `n` employees:

* CSV parsing and normalization: O(n)
* Identity validation: O(n)
* Employee indexing: O(n)
* Manager resolution: O(n)
* Hierarchy and cycle analysis: approximately O(n)
* Overall expected time complexity: O(n)
* Space complexity: O(n)

This approach is suitable for HRIS files approaching approximately 100,000 employees.

## Assumptions

* `employee_id` is case-sensitive.
* Email addresses are normalized to lowercase.
* Surrounding whitespace is removed from every CSV value.
* `employee_id` and `email` are required.
* Invalid identity rows are excluded from manager lookup and hierarchy analysis.
* Each employee can have at most one resolved manager.
* If both manager ID and manager email are supplied, both must identify the same employee.
* An employee with a manager error remains accepted for analysis but does not create a reporting relationship.
* An employee with a manager error is not considered a root.
* A root employee is an accepted employee with both manager fields blank.
* Only employees actually belonging to a cycle are classified as cyclic.

## Error Handling

Malformed uploads and invalid CSV input are handled with a clear user-facing error rather than allowing an unhandled exception to reach the browser.

Row-level validation problems include the source CSV row number and a useful description of the problem.

## Known Limitations

* The application is designed as an import preview and does not persist employee or reporting relationship data.
* Authentication and user accounts are not included because they are outside the exercise requirements.
* Production deployment configuration is not included.
* The application uses a simple HTML interface because visual styling was not a priority for this exercise.
* Uploaded data is processed in memory. For significantly larger production files, streaming processing or additional resource limits could be considered.

## Testing

The application includes focused automated tests for important behavior such as:

* CSV parsing and normalization.
* Duplicate identity validation.
* Manager resolution.
* Reporting hierarchy behavior.
* Reporting cycle detection.

Run all tests using:

```powershell
python manage.py test
```

## AI Tools Used

AI tools were used as development assistants during the exercise for understanding the requirements, discussing implementation approaches, reviewing edge cases, and improving parts of the implementation.

All AI-generated suggestions and code were reviewed, understood, tested, and adapted before being included in the project.

One useful suggestion was to represent the reporting hierarchy using employee-to-manager references and detect cycles by following manager chains. This approach was used because each employee can have at most one manager, making the hierarchy straightforward to traverse while keeping the expected time complexity approximately O(n).

AI assistance was treated as a development tool rather than a replacement for testing or technical understanding.

## Time Spent

Implementation and testing: **[ENTER YOUR ACTUAL TIME]**

Video recording: **[ENTER YOUR ACTUAL TIME]**

## Submission

Source repository:

**[PASTE YOUR GITHUB REPOSITORY LINK]**

Video walkthrough:

**[PASTE YOUR VIDEO LINK]**
