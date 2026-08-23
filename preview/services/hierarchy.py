def build_direct_report_counts(rows, relationships):
    """
    Count the direct reports for each employee.

    relationships has this format:

        {
            "employee_id": "manager_id"
        }

    Example:

        {
            "DIV-1002": "DIV-1001",
            "DIV-1003": "DIV-1001",
        }

    Result:

        {
            "DIV-1001": 2,
            "DIV-1002": 0,
            "DIV-1003": 0,
        }
    """

    counts = {
        row["employee_id"]: 0
        for row in rows
    }

    for employee_id, manager_id in relationships.items():
        if manager_id in counts:
            counts[manager_id] += 1

    return counts


def find_roots(rows, relationships, manager_error_employee_ids=None):
    """
    Find employees who have no manager.

    Employees with manager errors are NOT roots.
    """

    if manager_error_employee_ids is None:
        manager_error_employee_ids = set()

    employees_with_manager = set(relationships.keys())

    return [
        row
        for row in rows
        if (
            row["employee_id"] not in employees_with_manager
            and row["employee_id"]
            not in manager_error_employee_ids
        )
    ]


def find_cycles(rows, relationships):
    """
    Find employees that participate in reporting cycles.

    An employee is cyclic only if that employee is part of
    the actual cycle.

    Example:

        A -> B
        B -> C
        C -> A
        D -> A

    Cyclic employees:
        A, B, C

    D is NOT cyclic because D only reports into the cycle.

    Returns:
        A set containing employee IDs that are members of
        reporting cycles.
    """

    cycle_members = set()

    # Every employee has at most one manager, so each employee
    # has at most one outgoing edge in the reporting graph.
    for employee_id in relationships:
        path = []
        position = {}

        current = employee_id

        while current in relationships:

            # We have encountered the same employee again
            # while following this path.
            if current in position:
                cycle_start = position[current]

                cycle = path[cycle_start:]

                cycle_members.update(cycle)

                break

            position[current] = len(path)
            path.append(current)

            current = relationships[current]

    return cycle_members


def analyze_hierarchy(
    rows,
    relationships,
    manager_error_employee_ids=None,
):
    """
    Perform all hierarchy analysis.
    """

    direct_report_counts = build_direct_report_counts(
        rows,
        relationships,
    )

    cycle_members = find_cycles(
        rows,
        relationships,
    )

    roots = find_roots(
        rows,
        relationships,
        manager_error_employee_ids,
    )

    return {
        "direct_report_counts": direct_report_counts,
        "roots": roots,
        "cycle_members": cycle_members,
    }