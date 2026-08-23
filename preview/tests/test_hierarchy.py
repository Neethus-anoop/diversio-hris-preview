from django.test import SimpleTestCase

from preview.services.hierarchy import (
    build_direct_report_counts,
    find_cycles,
)


class HierarchyTests(SimpleTestCase):

    def test_direct_report_counts(self):
        rows = [
            {
                "employee_id": "A",
            },
            {
                "employee_id": "B",
            },
            {
                "employee_id": "C",
            },
            {
                "employee_id": "D",
            },
        ]

        relationships = {
            "B": "A",
            "C": "A",
            "D": "B",
        }

        counts = build_direct_report_counts(
            rows,
            relationships,
        )

        self.assertEqual(counts["A"], 2)
        self.assertEqual(counts["B"], 1)
        self.assertEqual(counts["C"], 0)
        self.assertEqual(counts["D"], 0)

    def test_cycle_detection_finds_only_cycle_members(self):
        rows = [
            {"employee_id": "A"},
            {"employee_id": "B"},
            {"employee_id": "C"},
            {"employee_id": "D"},
        ]

        relationships = {
            "A": "B",
            "B": "C",
            "C": "A",
            "D": "A",
        }

        cycles = find_cycles(
            rows,
            relationships,
        )

        self.assertEqual(
            cycles,
            {"A", "B", "C"},
        )

        self.assertNotIn(
            "D",
            cycles,
        )

    def test_no_cycle_returns_empty_set(self):
        rows = [
            {"employee_id": "A"},
            {"employee_id": "B"},
            {"employee_id": "C"},
        ]

        relationships = {
            "B": "A",
            "C": "B",
        }

        cycles = find_cycles(
            rows,
            relationships,
        )

        self.assertEqual(
            cycles,
            set(),
        )