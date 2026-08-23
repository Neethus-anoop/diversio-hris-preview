from django.test import SimpleTestCase

from preview.services.parser import (
    parse_csv,
    validate_identity,
    validate_managers,
)


class ParserTests(SimpleTestCase):

    # ---------------------------------------------------------
    # CSV PARSING TESTS
    # ---------------------------------------------------------

    def test_parse_csv_normalizes_values(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
 DIV-1001 , Avery Morgan , DEMO.AVERY@DIVERSIO.COM , , , Executive
"""

        rows = parse_csv(csv_content)

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["employee_id"], "DIV-1001")
        self.assertEqual(rows[0]["employee_name"], "Avery Morgan")
        self.assertEqual(rows[0]["email"], "demo.avery@diversio.com")
        self.assertEqual(rows[0]["department"], "Executive")
        self.assertEqual(rows[0]["source_row"], 2)

    def test_parse_csv_handles_quoted_comma(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1412,"Alvarez, Renée",demo.renee@diversio.com,DIV-1400,,Operations
"""

        rows = parse_csv(csv_content)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["employee_name"],
            "Alvarez, Renée",
        )

    def test_parse_csv_handles_utf8_bom(self):
        csv_content = (
            "\ufeffemployee_id,employee_name,email,manager_id,"
            "manager_email,department\n"
            "DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive\n"
        )

        rows = parse_csv(csv_content.encode("utf-8"))

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["employee_id"],
            "DIV-1001",
        )

    def test_parse_csv_accepts_headers_in_different_order(self):
        csv_content = """email,employee_id,department,employee_name,manager_email,manager_id
demo.avery@diversio.com,DIV-1001,Executive,Avery Morgan,,
"""

        rows = parse_csv(csv_content)

        self.assertEqual(len(rows), 1)
        self.assertEqual(
            rows[0]["employee_id"],
            "DIV-1001",
        )
        self.assertEqual(
            rows[0]["email"],
            "demo.avery@diversio.com",
        )

    def test_parse_csv_rejects_missing_header(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email
DIV-1001,Avery Morgan,demo.avery@diversio.com,,
"""

        with self.assertRaises(ValueError):
            parse_csv(csv_content)

    # ---------------------------------------------------------
    # EMPLOYEE IDENTITY VALIDATION TESTS
    # ---------------------------------------------------------

    def test_missing_employee_id_is_invalid(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
,Noa Williams,demo.noa@diversio.com,,,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, errors = validate_identity(rows)

        self.assertEqual(len(valid_rows), 0)
        self.assertEqual(len(errors), 1)

        self.assertIn(
            "employee_id is required",
            errors[0]["errors"],
        )

    def test_missing_email_is_invalid(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,,,,,Executive
"""

        rows = parse_csv(csv_content)

        valid_rows, errors = validate_identity(rows)

        self.assertEqual(len(valid_rows), 0)
        self.assertEqual(len(errors), 1)

        self.assertIn(
            "email is required",
            errors[0]["errors"],
        )

    def test_duplicate_employee_id_invalidates_all_duplicate_rows(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1001,Another Person,demo.another@diversio.com,,,Engineering
DIV-1002,Noa Williams,demo.noa@diversio.com,,,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, errors = validate_identity(rows)

        # Only DIV-1002 should remain valid.
        self.assertEqual(len(valid_rows), 1)
        self.assertEqual(
            valid_rows[0]["employee_id"],
            "DIV-1002",
        )

        # Both rows containing DIV-1001 must be invalid.
        self.assertEqual(len(errors), 2)

    def test_duplicate_email_is_case_insensitive(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.test@diversio.com,,,Executive
DIV-1002,Noa Williams,DEMO.TEST@DIVERSIO.COM,,,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, errors = validate_identity(rows)

        # Both rows have the same normalized email.
        self.assertEqual(len(valid_rows), 0)
        self.assertEqual(len(errors), 2)

    # ---------------------------------------------------------
    # MANAGER VALIDATION TESTS
    # ---------------------------------------------------------

    def test_manager_id_creates_relationship(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1002,Noa Williams,demo.noa@diversio.com,DIV-1001,,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        result = validate_managers(valid_rows)

        self.assertEqual(
            result["relationships"]["DIV-1002"],
            "DIV-1001",
        )

        self.assertEqual(
            len(result["manager_errors"]),
            0,
        )

    def test_manager_email_creates_relationship(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1002,Noa Williams,demo.noa@diversio.com,,DEMO.AVERY@DIVERSIO.COM,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        result = validate_managers(valid_rows)

        self.assertEqual(
            result["relationships"]["DIV-1002"],
            "DIV-1001",
        )

        self.assertEqual(
            len(result["manager_errors"]),
            0,
        )

    def test_both_manager_fields_must_match(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1002,Noa Williams,demo.noa@diversio.com,DIV-1001,demo.avery@diversio.com,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        result = validate_managers(valid_rows)

        self.assertEqual(
            result["relationships"]["DIV-1002"],
            "DIV-1001",
        )

        self.assertEqual(
            len(result["manager_errors"]),
            0,
        )

    def test_conflicting_manager_id_and_email_is_error(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1002,Sofia Chen,demo.sofia@diversio.com,,,Engineering
DIV-1003,Riley Cooper,demo.riley@diversio.com,DIV-1001,demo.sofia@diversio.com,Engineering
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        result = validate_managers(valid_rows)

        self.assertEqual(
            len(result["manager_errors"]),
            1,
        )

        self.assertIn(
            "different employees",
            result["manager_errors"][0]["errors"][0],
        )

        # Riley must not have a reporting relationship.
        self.assertNotIn(
            "DIV-1003",
            result["relationships"],
        )

    def test_missing_manager_is_error_but_employee_remains_accepted(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,,,Executive
DIV-1002,Casey Bell,demo.casey@diversio.com,DIV-9999,,Operations
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        # Casey is still an accepted employee.
        self.assertEqual(len(valid_rows), 2)

        result = validate_managers(valid_rows)

        self.assertEqual(
            len(result["manager_errors"]),
            1,
        )

        self.assertEqual(
            result["manager_errors"][0]["employee_id"],
            "DIV-1002",
        )

        # Casey must not have a relationship.
        self.assertNotIn(
            "DIV-1002",
            result["relationships"],
        )

        # Only Avery is a root.
        self.assertEqual(
            len(result["roots"]),
            1,
        )

        self.assertEqual(
            result["roots"][0]["employee_id"],
            "DIV-1001",
        )

    def test_self_manager_is_error(self):
        csv_content = """employee_id,employee_name,email,manager_id,manager_email,department
DIV-1001,Avery Morgan,demo.avery@diversio.com,DIV-1001,,Executive
"""

        rows = parse_csv(csv_content)

        valid_rows, identity_errors = validate_identity(rows)

        self.assertEqual(len(identity_errors), 0)

        result = validate_managers(valid_rows)

        self.assertEqual(
            len(result["manager_errors"]),
            1,
        )

        self.assertIn(
            "cannot manage themselves",
            result["manager_errors"][0]["errors"][0],
        )

        # Self-manager must not create a relationship.
        self.assertNotIn(
            "DIV-1001",
            result["relationships"],
        )

        # An employee with a manager error is NOT a root.
        self.assertEqual(
            len(result["roots"]),
            0,
        )