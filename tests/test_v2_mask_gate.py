"""Contract-only tests; no photo, Adobe account or model review is exercised."""
import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "experiments" / "v2_local_light"))
from mask_gate import SelectionReceipt, allow_local_edit, edited_photo_acceptable


def approved():
    return SelectionReceipt(
        region="hotel", geometry_id="photo-A:geometry-1",
        mask_url="https://example.invalid/actual-mask-result",
        normalized_bbox=(0.26, 0.04, 0.28, 0.77),
        visual_status="verified",
        reviewer_note="Hotel silhouette matched the original and protected nearby signs.")


def gate(receipt=None, **changes):
    args = dict(current_geometry_id="photo-A:geometry-1", region="hotel",
                intensity="moderate", fixed_content_protected=True,
                image_preview_inspected=True)
    args.update(changes)
    return allow_local_edit(approved() if receipt is None else receipt, **args)


class MaskRoutingTests(unittest.TestCase):

    def test_verified_mask_is_only_permission_to_try_an_edit(self):
        result = gate()
        self.assertTrue(result.allowed)
        self.assertIn("requires image-to-source review", result.reason)

    def test_wrong_target_is_rejected_even_when_tool_says_success(self):
        result = gate(replace(approved(), visual_status="wrong_target",
                              reviewer_note="The returned white pixels select sky, not stonework."))
        self.assertFalse(result.allowed)

    def test_partial_street_mask_rejected(self):
        self.assertFalse(gate(replace(approved(), visual_status="partial")).allowed)

    def test_leak_into_signs_rejected(self):
        self.assertFalse(gate(replace(approved(), visual_status="leaking")).allowed)

    def test_missing_selection_and_unreviewed_selection_rejected(self):
        self.assertFalse(allow_local_edit(None, current_geometry_id="x",
            region="hotel", image_preview_inspected=True).allowed)
        self.assertFalse(gate(replace(approved(), visual_status="unverified")).allowed)

    def test_color_edit_reuses_geometry_but_crop_never_does(self):
        self.assertTrue(gate(replace(approved(), geometry_id="photo-A:geometry-1")).allowed)
        self.assertFalse(gate(replace(approved(), geometry_id="photo-A:geometry-2")).allowed)

    def test_no_visual_preview_means_no_adjustment(self):
        self.assertFalse(gate(image_preview_inspected=False).allowed)

    def test_missing_fixed_content_protection_is_blocker(self):
        self.assertFalse(gate(fixed_content_protected=False).allowed)

    def test_wrong_region_fails(self):
        self.assertFalse(gate(region="road").allowed)

    def test_invalid_or_untrusted_mask_output_fails(self):
        self.assertFalse(gate(replace(approved(), normalized_bbox=(0.8,0.1,0.5,0.6))).allowed)
        self.assertFalse(gate(replace(approved(), mask_url="file:///tmp/claimed-mask")).allowed)
        self.assertFalse(gate(replace(approved(), reviewer_note="looks fine")).allowed)

    def test_human_review_does_not_automatically_certify_final_image(self):
        inputs = dict(real_tool_output=True, original_and_result_compared=True,
            fixed_content_preserved=True, coherent_photographic_look=True,
            expressive_improvement=True)
        self.assertTrue(edited_photo_acceptable(**inputs))
        for field in inputs:
            with self.subTest(field=field):
                changed = dict(inputs, **{field:False})
                self.assertFalse(edited_photo_acceptable(**changed))


if __name__ == "__main__":
    unittest.main()
