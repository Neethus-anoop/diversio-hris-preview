from .parser import (
    parse_csv,
    validate_identity,
    validate_managers,
)

from .hierarchy import analyze_hierarchy


def process_import(file_content):
    """
    Run the complete HRIS import-preview pipeline.

    The CSV is parsed and analyzed entirely in memory.
    No employee or relationship data is written to the database.
    """

    # ---------------------------------------------------------
    # Step 1: Parse the CSV
    # ---------------------------------------------------------

    rows = parse_csv(file_content)

    total_rows = len(rows)

    # ---------------------------------------------------------
    # Step 2: Validate employee identity
    # ---------------------------------------------------------

    valid_rows, identity_errors = validate_identity(rows)

    accepted_employees = len(valid_rows)

    # ---------------------------------------------------------
    # Step 3: Validate manager relationships
    # ---------------------------------------------------------

    manager_result = validate_managers(valid_rows)

    relationships = manager_result["relationships"]

    manager_errors = manager_result["manager_errors"]

    # ---------------------------------------------------------
    # Step 4: Find employees with manager errors
    # ---------------------------------------------------------

    manager_error_employee_ids = {
        error["employee_id"]
        for error in manager_errors
    }

    # ---------------------------------------------------------
    # Step 5: Analyze hierarchy
    # ---------------------------------------------------------

    hierarchy_result = analyze_hierarchy(
        valid_rows,
        relationships,
        manager_error_employee_ids,
    )

    # ---------------------------------------------------------
    # Step 6: Build manager table for the UI
    # ---------------------------------------------------------

    direct_report_counts = hierarchy_result[
        "direct_report_counts"
    ]

    employee_by_id = {
        row["employee_id"]: row
        for row in valid_rows
    }

    managers = []

    for employee_id, report_count in direct_report_counts.items():

        # Only show employees who actually have
        # at least one direct report.
        if report_count == 0:
            continue

        employee = employee_by_id.get(employee_id)

        if employee is None:
            continue

        managers.append(
            {
                "employee_id": employee["employee_id"],
                "employee_name": employee["employee_name"],
                "department": employee["department"],
                "direct_reports": report_count,
            }
        )

    # ---------------------------------------------------------
    # Step 7: Total validation errors
    # ---------------------------------------------------------

    total_errors = (
        len(identity_errors)
        + len(manager_errors)
    )

    # ---------------------------------------------------------
    # Step 8: Return everything required by the UI
    # ---------------------------------------------------------

    return {
        "total_rows": total_rows,

        "accepted_employees": accepted_employees,

        "total_errors": total_errors,

        "identity_errors": identity_errors,

        "manager_errors": manager_errors,

        "managers": managers,

        "direct_report_counts": direct_report_counts,

        "roots": hierarchy_result["roots"],

        "cycle_members": hierarchy_result["cycle_members"],

        "relationships": relationships,

        "rows": valid_rows,
    }