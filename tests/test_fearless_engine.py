"""Unit test suite for C9 Fearless Nexus core Fearless Draft & Scouting logic."""

from __future__ import annotations

import unittest

from backend.fearless_engine import (
    TOURNAMENT_DRAFT_SEQUENCE,
    compute_fearless_locked,
    compute_pinch_score,
    estimate_live_win_probability,
    evaluate_comp_balance,
    validate_draft_action,
)
from backend.grid_stream import classify_rift_zone


class TestFearlessDraftEngine(unittest.TestCase):
    def test_tournament_20_step_sequence_structure(self) -> None:
        self.assertEqual(len(TOURNAMENT_DRAFT_SEQUENCE), 20)
        bans = [s for s in TOURNAMENT_DRAFT_SEQUENCE if s.action == "ban"]
        picks = [s for s in TOURNAMENT_DRAFT_SEQUENCE if s.action == "pick"]
        self.assertEqual(len(bans), 10)
        self.assertEqual(len(picks), 10)
        # First pick must be B1 at step 7; last pick must be R5 counter-pick at step 20
        self.assertEqual(TOURNAMENT_DRAFT_SEQUENCE[6].slot, "B1")
        self.assertEqual(TOURNAMENT_DRAFT_SEQUENCE[6].side, "blue")
        self.assertEqual(TOURNAMENT_DRAFT_SEQUENCE[19].slot, "R5")
        self.assertEqual(TOURNAMENT_DRAFT_SEQUENCE[19].side, "red")

    def test_fearless_cumulative_locks_game1_to_game5(self) -> None:
        g1 = ["Rumble", "Skarner", "Azir", "Kalista", "Rell", "K'Sante", "Vi", "Ahri", "Varus", "Rakan"]
        g2 = ["Jax", "Sejuani", "Orianna", "Ashe", "Braum", "Gnar", "Xin Zhao", "Taliyah", "Ezreal", "Leona"]
        g3 = ["Ornn", "Maokai", "Yone", "Kai'Sa", "Nautilus", "Renekton", "Wukong", "Sylas", "Jhin", "Alistar"]
        g4 = ["Ambessa", "Nocturne", "Viktor", "Xayah", "Bard", "Aatrox", "Viego", "Galio", "Miss Fortune", "Thresh"]

        self.assertEqual(len(compute_fearless_locked([])), 0)
        self.assertEqual(len(compute_fearless_locked([g1])), 10)
        self.assertEqual(len(compute_fearless_locked([g1, g2])), 20)
        self.assertEqual(len(compute_fearless_locked([g1, g2, g3])), 30)
        locked_g5 = compute_fearless_locked([g1, g2, g3, g4])
        self.assertEqual(len(locked_g5), 40)

        ok_locked, msg_locked = validate_draft_action("Skarner", locked_g5, [], [])
        self.assertFalse(ok_locked)
        self.assertIn("Fearless-locked", msg_locked)

        ok_legal, _ = validate_draft_action("Cassiopeia", locked_g5, ["Ziggs"], ["Jayce"])
        self.assertTrue(ok_legal)

    def test_pinch_score_monotonicity_under_fearless_and_bans(self) -> None:
        jungle_pool = [
            {"champion": "Sejuani", "games": 14, "wins": 10},
            {"champion": "Skarner", "games": 10, "wins": 7},
            {"champion": "Vi", "games": 6, "wins": 4},
            {"champion": "Ivern", "games": 1, "wins": 0},
        ]
        p0 = compute_pinch_score(jungle_pool, locked_champions=[], banned_champions=[])
        p1 = compute_pinch_score(jungle_pool, locked_champions=["Sejuani", "Skarner"], banned_champions=[])
        p2 = compute_pinch_score(jungle_pool, locked_champions=["Sejuani", "Skarner"], banned_champions=["Vi"])

        self.assertEqual(p0["pinch_index"], 0.0)
        self.assertGreater(p1["pinch_index"], p0["pinch_index"])
        self.assertGreater(p2["pinch_index"], p1["pinch_index"])
        self.assertLess(p2["expected_wr_delta"], 0.0)
        self.assertEqual(p2["remaining_comfort_count"], 0)

    def test_win_probability_bounds_and_comp_synergy(self) -> None:
        balanced = evaluate_comp_balance(["Ornn", "Vi", "Orianna", "Kai'Sa", "Rell"])
        mono_squishy = evaluate_comp_balance(["Jayce", "Lee Sin", "Tristana", "Caitlyn", "Pyke"])
        self.assertGreater(balanced["composite"], mono_squishy["composite"])

        res = estimate_live_win_probability(
            c9_side="blue",
            c9_picks=["Ornn", "Vi", "Orianna", "Kai'Sa", "Rell"],
            opp_picks=["Jayce", "Lee Sin", "Tristana", "Caitlyn", "Pyke"],
            champ_metrics={"Orianna": {"c9_wr": 0.68}, "Vi": {"c9_wr": 0.64}},
            pinch_bonus=0.06,
        )
        self.assertGreaterEqual(res["c9_win_probability"], 0.05)
        self.assertLessEqual(res["c9_win_probability"], 0.95)
        self.assertGreater(res["c9_win_probability"], 0.55)
        self.assertAlmostEqual(res["c9_win_probability"] + res["opp_win_probability"], 1.0, places=3)

    def test_rift_coordinate_zone_classifier(self) -> None:
        self.assertEqual(classify_rift_zone(4900.0, 10200.0), "Baron / Void Grub Pit")
        self.assertEqual(classify_rift_zone(9800.0, 4400.0), "Dragon Pit & Bot River")
        self.assertEqual(classify_rift_zone(7400.0, 7300.0), "Mid Lane & Raptor Crossing")


if __name__ == "__main__":
    unittest.main()
