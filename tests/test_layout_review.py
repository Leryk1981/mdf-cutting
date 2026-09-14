import unittest

from packer.layout_review import (
    LayoutSnapshot,
    Placement,
    guillotine_remnant,
    move_placement,
    repack_unlocked,
    refresh_guillotine_cut,
    rotate_placement,
    snap_placement,
    toggle_guillotine_cut,
    transfer_fit,
    transfer_placement_at,
)


class LayoutReviewTests(unittest.TestCase):
    def test_default_guillotine_cut_keeps_the_largest_outer_remnant(self):
        layout = refresh_guillotine_cut(LayoutSnapshot(
            "sheet-1", 1200, 1000,
            (Placement("A", 0, 0, 1000, 200),),
        ))

        self.assertEqual(layout.guillotine_cut.orientation, "horizontal")
        self.assertEqual(layout.guillotine_cut.position, 200)
        self.assertEqual(guillotine_remnant(layout), (1200, 800))

    def test_operator_can_select_vertical_guillotine_cut(self):
        layout = refresh_guillotine_cut(LayoutSnapshot(
            "sheet-1", 1200, 1000,
            (Placement("A", 0, 0, 1000, 200),),
        ))

        edited = toggle_guillotine_cut((layout,), "sheet-1")

        self.assertEqual(edited[0].guillotine_cut.orientation, "vertical")
        self.assertEqual(edited[0].guillotine_cut.position, 1000)
        self.assertEqual(guillotine_remnant(edited[0]), (1000, 200))

    def test_move_recalculates_cut_and_preserves_selected_direction(self):
        layout = refresh_guillotine_cut(LayoutSnapshot(
            "sheet-1", 1200, 1000,
            (Placement("A", 0, 0, 1000, 200),),
        ))

        edited = move_placement((layout,), "A", "sheet-1", 0, 100)

        self.assertEqual(edited[0].guillotine_cut.orientation, "horizontal")
        self.assertEqual(edited[0].guillotine_cut.position, 300)
        self.assertEqual(guillotine_remnant(edited[0]), (1200, 700))

    def test_transfer_fit_distinguishes_direct_rotated_and_impossible(self):
        layouts = (
            LayoutSnapshot(
                "source", 200, 200,
                (Placement("A", 0, 0, 100, 60, material_key="16_S"),),
                material_key="16_S",
            ),
            LayoutSnapshot("rotated", 80, 120, (), material_key="16_S"),
            LayoutSnapshot("impossible", 50, 50, (), material_key="16_S"),
        )

        self.assertEqual(transfer_fit(layouts, "A", "source"), "direct")
        self.assertEqual(transfer_fit(layouts, "A", "rotated"), "rotated")
        self.assertIsNone(transfer_fit(layouts, "A", "impossible"))

    def test_transfer_can_rotate_automatically_on_target_map(self):
        layouts = (
            LayoutSnapshot(
                "source", 200, 200,
                (Placement("A", 0, 0, 100, 60, material_key="16_S"),),
                material_key="16_S",
            ),
            LayoutSnapshot("target", 80, 120, (), material_key="16_S"),
        )

        edited, was_rotated = transfer_placement_at(
            layouts, "A", "target", center_x=40, center_y=60)
        moved = edited[1].placements[0]

        self.assertTrue(was_rotated)
        self.assertEqual((moved.width, moved.height), (60, 100))
        self.assertEqual((moved.x, moved.y), (0, 0))

    def test_snap_aligns_moving_edge_to_neighbour_without_overlap(self):
        layouts = (LayoutSnapshot(
            "sheet-1", 200, 100,
            (
                Placement("A", 0, 0, 50, 50),
                Placement("B", 100, 0, 50, 50),
            ),
        ),)

        x, y = snap_placement(
            layouts, "A", "sheet-1", 47, 2, tolerance=6)
        moved = move_placement(layouts, "A", "sheet-1", x, y)

        self.assertEqual((x, y), (50, 0))
        self.assertEqual(moved[0].placements[0].x, 50)

    def test_snap_uses_sheet_edges(self):
        layouts = (LayoutSnapshot(
            "sheet-1", 200, 100,
            (Placement("A", 20, 20, 50, 50),),
        ),)

        x, y = snap_placement(
            layouts, "A", "sheet-1", 147, 49, tolerance=5)

        self.assertEqual((x, y), (150, 50))

    def test_move_rejects_collision_and_preserves_original(self):
        layouts = (LayoutSnapshot(
            "sheet-1", 100, 100,
            (
                Placement("A", 0, 0, 40, 40),
                Placement("B", 50, 0, 40, 40),
            ),
        ),)

        with self.assertRaisesRegex(ValueError, "пересекается"):
            move_placement(layouts, "A", "sheet-1", 55, 0)

        self.assertEqual(layouts[0].placements[0].x, 0)

    def test_move_can_transfer_detail_between_compatible_maps(self):
        layouts = (
            LayoutSnapshot(
                "sheet-1", 100, 100,
                (Placement("A", 0, 0, 40, 40, material_key="16_S"),),
                material_key="16_S",
            ),
            LayoutSnapshot(
                "sheet-2", 100, 100, (), material_key="16_S"),
        )

        moved = move_placement(layouts, "A", "sheet-2", 50, 50)

        self.assertFalse(moved[0].placements)
        self.assertEqual(moved[1].placements[0].placement_id, "A")
        self.assertEqual((moved[1].placements[0].x, moved[1].placements[0].y),
                         (50, 50))

    def test_move_rejects_another_material(self):
        layouts = (
            LayoutSnapshot(
                "16-mm", 100, 100,
                (Placement("A", 0, 0, 40, 40, material_key="16_S"),),
                material_key="16_S",
            ),
            LayoutSnapshot(
                "19-mm", 100, 100, (), material_key="19_S"),
        )

        with self.assertRaisesRegex(ValueError, "материал"):
            move_placement(layouts, "A", "19-mm", 0, 0)

    def test_rotation_prefers_the_same_lower_left_position(self):
        layouts = (LayoutSnapshot(
            "sheet-1", 100, 100,
            (Placement("A", 10, 20, 60, 20),),
        ),)

        rotated = rotate_placement(layouts, "A")
        placement = rotated[0].placements[0]

        self.assertEqual((placement.x, placement.y), (10, 20))
        self.assertEqual((placement.width, placement.height), (20, 60))
        self.assertTrue(placement.rotated)

    def test_rotation_finds_nearby_valid_position_when_origin_is_blocked(self):
        layouts = (LayoutSnapshot(
            "sheet-1", 100, 100,
            (
                Placement("A", 0, 0, 60, 20),
                Placement("B", 0, 20, 40, 40),
            ),
        ),)

        rotated = rotate_placement(layouts, "A")
        placement = rotated[0].placements[0]

        self.assertEqual((placement.width, placement.height), (20, 60))
        self.assertNotEqual((placement.x, placement.y), (0, 0))

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

    def test_repack_never_mixes_material_groups(self):
        layouts = (
            LayoutSnapshot(
                layout_id="16-mm",
                width=100,
                height=100,
                placements=(Placement(
                    "A", 0, 0, 50, 100, material_key="16_S"),),
                material_key="16_S",
            ),
            LayoutSnapshot(
                layout_id="19-mm",
                width=100,
                height=100,
                placements=(Placement(
                    "B", 0, 0, 50, 100, material_key="19_S"),),
                material_key="19_S",
            ),
        )

        proposal = repack_unlocked(layouts, locked_ids=set())

        self.assertEqual(proposal.after.layout_count, 2)
        self.assertEqual(
            [layout.material_key for layout in proposal.layouts],
            ["16_S", "19_S"],
        )


if __name__ == "__main__":
    unittest.main()
