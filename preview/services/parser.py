import csv
import io


REQUIRED_HEADERS = [
    "employee_id",
    "employee_name",
    "email",
    "manager_id",
    "manager_email",
    "department",
]


def normalize_value(value):
    """
    Trim surrounding whitespace from a value.
    """
    if value is None:
        return ""

    return value.strip()


def normalize_email(value):
    """
    Trim whitespace and lowercase an email address.
    """
    return normalize_value(value).lower()


def parse_csv(file_content):
    """
    Parse and normalize an HRIS CSV file.

    Supports:
    - UTF-8
    - UTF-8 with BOM
    - quoted CSV values
    - headers in any order
    - whitespace normalization
    - lowercase email normalization

    Returns:
        list of normalized employee rows
    """

    if isinstance(file_content, bytes):
        try:
            file_content = file_content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise ValueError(
                "The uploaded file must be a valid UTF-8 CSV file."
            ) from exc

    if not isinstance(file_content, str):
        raise ValueError("Invalid file content.")

    reader = csv.DictReader(io.StringIO(file_content))

    if reader.fieldnames is None:
        raise ValueError(
            "The uploaded file is empty or has no CSV headers."
        )

    # Remove whitespace around header names.
    headers = [
        normalize_value(header)
        for header in reader.fieldnames
        if header is not None
    ]

    # Check that every required header exists.
    missing_headers = set(REQUIRED_HEADERS) - set(headers)

    if missing_headers:
        raise ValueError(
            "Missing required headers: "
            + ", ".join(sorted(missing_headers))
        )

    rows = []

    # CSV header is row 1, so employee data starts at row 2.
    for source_row, raw_row in enumerate(reader, start=2):

        row = {
            "employee_id": normalize_value(
                raw_row.get("employee_id")
            ),
            "employee_name": normalize_value(
                raw_row.get("employee_name")
            ),
            "email": normalize_email(
                raw_row.get("email")
            ),
            "manager_id": normalize_value(
                raw_row.get("manager_id")
            ),
            "manager_email": normalize_email(
                raw_row.get("manager_email")
            ),
            "department": normalize_value(
                raw_row.get("department")
            ),
            "source_row": source_row,
        }

        rows.append(row)

    return rows


def validate_identity(rows):
    """
    Validate employee identity.

    employee_id and email are required.

    employee_id must be unique.

    email must be unique after normalization.

    If an employee ID or email is duplicated, every row
    sharing that duplicated identity is invalid.

    Returns:
        valid_rows, errors
    """

    errors = []

    employee_id_rows = {}
    email_rows = {}

    # ---------------------------------------------------------
    # First pass:
    # Find all employee IDs and emails and the rows where
    # they occur.
    # ---------------------------------------------------------

    for row in rows:
        employee_id = row["employee_id"]
        email = row["email"]

        if employee_id:
            employee_id_rows.setdefault(
                employee_id,
                [],
            ).append(row["source_row"])

        if email:
            email_rows.setdefault(
                email,
                [],
            ).append(row["source_row"])

    # ---------------------------------------------------------
    # Find duplicate employee IDs.
    # ---------------------------------------------------------

    duplicate_employee_ids = {
        employee_id
        for employee_id, source_rows in employee_id_rows.items()
        if len(source_rows) > 1
    }

    # ---------------------------------------------------------
    # Find duplicate emails.
    # Emails have already been lowercased by parse_csv().
    # ---------------------------------------------------------

    duplicate_emails = {
        email
        for email, source_rows in email_rows.items()
        if len(source_rows) > 1
    }

    # ---------------------------------------------------------
    # Second pass:
    # Validate every row.
    # ---------------------------------------------------------

    for row in rows:

        source_row = row["source_row"]
        employee_id = row["employee_id"]
        email = row["email"]

        row_errors = []

        # Required employee ID.
        if not employee_id:
            row_errors.append(
                "employee_id is required"
            )

        # Required email.
        if not email:
            row_errors.append(
                "email is required"
            )

        # Duplicate employee ID.
        if employee_id in duplicate_employee_ids:
            row_errors.append(
                f"Duplicate employee_id: {employee_id}"
            )

        # Duplicate email.
        if email in duplicate_emails:
            row_errors.append(
                f"Duplicate email: {email}"
            )

        if row_errors:
            errors.append(
                {
                    "source_row": source_row,
                    "employee_id": employee_id,
                    "employee_name": row["employee_name"],
                    "errors": row_errors,
                }
            )

    # ---------------------------------------------------------
    # Any row with an identity error is excluded from
    # hierarchy/manager analysis.
    # ---------------------------------------------------------

    invalid_rows = {
        error["source_row"]
        for error in errors
    }

    valid_rows = [
        row
        for row in rows
        if row["source_row"] not in invalid_rows
    ]

    return valid_rows, errors


def validate_managers(rows):
    """
    Validate manager references for employees with valid identity.

    Manager rules:

    1. Both manager fields blank:
       Employee is a root.

    2. Only manager_id:
       Find manager using employee ID.

    3. Only manager_email:
       Find manager using normalized email.

    4. Both manager fields:
       Both must identify the same employee.

    5. Manager cannot be missing.

    6. Employee cannot manage themselves.

    Important:
    Manager errors do NOT invalidate the employee.
    They simply prevent a reporting relationship from
    being created.

    Returns:
        {
            "relationships": {
                employee_id: manager_id
            },
            "manager_errors": [...],
            "roots": [...]
        }
    """

    # ---------------------------------------------------------
    # Build lookup dictionaries.
    # ---------------------------------------------------------

    employee_by_id = {
        row["employee_id"]: row
        for row in rows
    }

    employee_by_email = {
        row["email"]: row
        for row in rows
    }

    manager_relationships = {}
    manager_errors = []
    roots = []

    # ---------------------------------------------------------
    # Check every employee.
    # ---------------------------------------------------------

    for row in rows:

        employee_id = row["employee_id"]
        manager_id = row["manager_id"]
        manager_email = row["manager_email"]

        # -----------------------------------------------------
        # Case 1:
        # Both manager fields are blank.
        # This employee is a root.
        # -----------------------------------------------------

        if not manager_id and not manager_email:
            roots.append(row)
            continue

        manager_by_id = None
        manager_by_email = None

        # -----------------------------------------------------
        # Look up manager by employee ID if provided.
        # -----------------------------------------------------

        if manager_id:
            manager_by_id = employee_by_id.get(
                manager_id
            )

        # -----------------------------------------------------
        # Look up manager by email if provided.
        # -----------------------------------------------------

        if manager_email:
            manager_by_email = employee_by_email.get(
                manager_email
            )

        manager = None
        error = None

        # -----------------------------------------------------
        # Case 2:
        # Only manager_id supplied.
        # -----------------------------------------------------

        if manager_id and not manager_email:

            if manager_by_id is None:
                error = (
                    f"Manager employee_id "
                    f"'{manager_id}' could not be found."
                )
            else:
                manager = manager_by_id

        # -----------------------------------------------------
        # Case 3:
        # Only manager_email supplied.
        # -----------------------------------------------------

        elif manager_email and not manager_id:

            if manager_by_email is None:
                error = (
                    f"Manager email "
                    f"'{manager_email}' could not be found."
                )
            else:
                manager = manager_by_email

        # -----------------------------------------------------
        # Case 4:
        # Both manager_id and manager_email supplied.
        # Both must point to the same employee.
        # -----------------------------------------------------

        elif manager_id and manager_email:

            if manager_by_id is None:
                error = (
                    f"Manager employee_id "
                    f"'{manager_id}' could not be found."
                )

            elif manager_by_email is None:
                error = (
                    f"Manager email "
                    f"'{manager_email}' could not be found."
                )

            elif (
                manager_by_id["employee_id"]
                != manager_by_email["employee_id"]
            ):
                error = (
                    "Manager ID and manager email "
                    "refer to different employees."
                )

            else:
                manager = manager_by_id

        # -----------------------------------------------------
        # Check self-management.
        # -----------------------------------------------------

        if manager is not None:

            if manager["employee_id"] == employee_id:
                error = (
                    "Employee cannot manage themselves."
                )

                manager = None

        # -----------------------------------------------------
        # Create reporting relationship if manager is valid.
        # -----------------------------------------------------

        if manager is not None:
            manager_relationships[employee_id] = (
                manager["employee_id"]
            )

        # -----------------------------------------------------
        # Record manager error.
        # Employee remains accepted, but has no relationship.
        # -----------------------------------------------------

        if error is not None:

            manager_errors.append(
                {
                    "source_row": row["source_row"],
                    "employee_id": employee_id,
                    "employee_name": row["employee_name"],
                    "errors": [error],
                }
            )

    return {
        "relationships": manager_relationships,
        "manager_errors": manager_errors,
        "roots": roots,
    }