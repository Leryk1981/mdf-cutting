import unittest

from packer.layout_review import (
    LayoutSnapshot,
    Placement,
    repack_unlocked,
)


class LayoutReviewTests(unittest.TestCase):
    def test_repack_can_free_the_last_sheet(self):
        layouts = (
            LayoutSnapshot(
                layout_id="sheet-1",
                width=100,
                height=100,
                placements=(Placement("A", 0, 0, 50, 100),),
            ),
            LayoutSnapshot(
                layout_id="sheet-2",
                width=100,
                height=100,
                placements=(Placement("B", 0, 0, 50, 100),),
            ),
        )

        proposal = repack_unlocked(layouts, locked_ids=set())

        self.assertTrue(proposal.feasible)
        self.assertEqual(proposal.before.layout_count, 2)
        self.assertEqual(proposal.after.layout_count, 1)
        self.assertEqual(
            {item.placement_id for item in proposal.layouts[0].placements},
            {"A", "B"},
        )

    def test_locked_placement_keeps_its_sheet_position_and_orientation(self):
        layouts = (
            LayoutSnapshot(
                layout_id="sheet-1",
                width=100,
                height=100,
                placements=(Placement("A", 25, 0, 50, 100, rotated=True),),
            ),
            LayoutSnapshot(
                layout_id="sheet-2",
                width=100,
                height=100,
                placements=(Placement("B", 0, 0, 25, 100),),
            ),
        )

        proposal = repack_unlocked(layouts, locked_ids={"A"})

        locked = next(
            item
            for layout in proposal.layouts
            for item in layout.placements
            if item.placement_id == "A"
        )
        self.assertEqual(locked, layouts[0].placements[0])
        self.assertEqual(proposal.after.layout_count, 1)

    def test_lock_on_last_sheet_prevents_it_from_being_removed(self):
        layouts = (
            LayoutSnapshot(
                layout_id="sheet-1",
                width=100,
                height=100,
                placements=(Placement("A", 0, 0, 50, 100),),
            ),
            LayoutSnapshot(
                layout_id="sheet-2",
                width=100,
                height=100,
                placements=(Placement("B", 0, 0, 50, 100),),
            ),
        )

        proposal = repack_unlocked(layouts, locked_ids={"B"})

        self.assertTrue(proposal.feasible)
        self.assertEqual(proposal.after.layout_count, 2)

    def test_invalid_overlapping_locks_reject_the_candidate(self):
        layouts = (
            LayoutSnapshot(
                layout_id="sheet-1",
                width=100,
                height=100,
                placements=(
                    Placement("A", 0, 0, 60, 60),
                    Placement("B", 50, 50, 40, 40),
                ),
            ),
        )

        proposal = repack_unlocked(layouts, locked_ids={"A", "B"})

        self.assertFalse(proposal.feasible)
        self.assertEqual(proposal.layouts, layouts)
        self.assertIn("пересекаются", proposal.reason)


if __name__ == "__main__":
    unittest.main()
