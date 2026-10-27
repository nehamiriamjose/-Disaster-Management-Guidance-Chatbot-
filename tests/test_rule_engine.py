"""
Unit Test Suite for DisasterShield Rule Engine
==============================================
Validates tree integrity, decision branches, error handling,
terminal guidance completeness, and transcript formatting.
"""

import unittest
from chatbot_engine import DisasterRuleEngine, RuleEngineError


class TestDisasterRuleEngine(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.engine = DisasterRuleEngine()

    def test_datasets_loaded(self):
        """Ensure all required disasters are loaded."""
        disasters = self.engine.get_available_disasters()
        self.assertEqual(len(disasters), 3)
        ids = [d["id"] for d in disasters]
        self.assertIn("earthquake", ids)
        self.assertIn("flood", ids)
        self.assertIn("landslide", ids)

    def test_sources_and_checklist_loaded(self):
        """Ensure checklist and sources are non-empty."""
        self.assertGreater(len(self.engine.checklist.get("categories", [])), 0)
        self.assertGreater(len(self.engine.sources.get("sources", [])), 0)
        self.assertGreater(len(self.engine.sources.get("hotlines", [])), 0)

    def test_all_decision_tree_paths_valid(self):
        """
        Exhaustively test that every branch in every disaster tree leads
        to a terminal guidance node without broken references.
        """
        for disaster_id in ["earthquake", "flood", "landslide"]:
            paths = self.engine.get_all_paths(disaster_id)
            # Must satisfy the assignment requirement of at least 3-4 decision branches
            self.assertGreaterEqual(len(paths), 4, f"Insufficient branches in {disaster_id}")

            nodes = self.engine.disasters[disaster_id]["nodes"]

            for path in paths:
                # Path length must be at least 3 nodes (meaning at least 3-4 decision steps)
                self.assertGreaterEqual(len(path), 3, f"Path too short in {disaster_id}: {path}")

                terminal_node_id = path[-1]
                terminal_node = nodes[terminal_node_id]

                # Terminal node must have structured guidance
                self.assertTrue(
                    terminal_node.get("is_terminal") or "guidance" in terminal_node,
                    f"Final node {terminal_node_id} is not terminal in {disaster_id}"
                )
                guidance = terminal_node.get("guidance", {})
                self.assertIn("status", guidance)
                self.assertIn("severity", guidance)
                self.assertIn("summary", guidance)
                self.assertGreaterEqual(len(guidance.get("immediate_actions", [])), 2)
                self.assertGreaterEqual(len(guidance.get("actions_to_avoid", [])), 1)
                self.assertGreaterEqual(len(guidance.get("emergency_contacts", [])), 1)
                self.assertTrue(bool(guidance.get("official_reference")))

    def test_earthquake_branching_outcomes(self):
        """
        Verify that distinct user choices lead to different appropriate safety guidance.
        Branch A: Indoors actively shaking with table -> Drop, Cover, Hold
        Branch B: Indoors post-shake with gas smell -> Utility emergency
        Branch C: Outdoors in open park -> Safe open field stay
        """
        # Branch A: Active shaking indoor
        session_a = self.engine.start_session("earthquake")
        res_a1 = self.engine.process_step("earthquake", session_a["current_node_id"], "opt_indoors", session_a["history"])
        res_a2 = self.engine.process_step("earthquake", res_a1["current_node_id"], "opt_shaking_now", res_a1["history"])
        res_a3 = self.engine.process_step("earthquake", res_a2["current_node_id"], "opt_sturdy_table", res_a2["history"])

        self.assertTrue(res_a3["is_complete"])
        self.assertIn("DROP, COVER, AND HOLD ON", res_a3["guidance"]["status"])

        # Branch B: Gas smell
        session_b = self.engine.start_session("earthquake")
        res_b1 = self.engine.process_step("earthquake", session_b["current_node_id"], "opt_indoors", session_b["history"])
        res_b2 = self.engine.process_step("earthquake", res_b1["current_node_id"], "opt_shaking_stopped", res_b1["history"])
        res_b3 = self.engine.process_step("earthquake", res_b2["current_node_id"], "opt_gas_spark", res_b2["history"])

        self.assertTrue(res_b3["is_complete"])
        self.assertIn("UTILITY HAZARD", res_b3["guidance"]["status"])

        # Branch C: Outdoor open field
        session_c = self.engine.start_session("earthquake")
        res_c1 = self.engine.process_step("earthquake", session_c["current_node_id"], "opt_outdoors", session_c["history"])
        res_c2 = self.engine.process_step("earthquake", res_c1["current_node_id"], "opt_open_park", res_c1["history"])

        self.assertTrue(res_c2["is_complete"])
        self.assertIn("SAFE OPEN-GROUND", res_c2["guidance"]["status"])

        # Validate that outcomes are indeed different
        self.assertNotEqual(res_a3["guidance"]["status"], res_b3["guidance"]["status"])
        self.assertNotEqual(res_a3["guidance"]["status"], res_c2["guidance"]["status"])

    def test_flood_turn_around_dont_drown_branch(self):
        """
        Verify Flood vehicle path strictly enforces 'Turn Around, Don't Drown'.
        """
        session = self.engine.start_session("flood")
        res1 = self.engine.process_step("flood", session["current_node_id"], "opt_in_vehicle", session["history"])
        res2 = self.engine.process_step("flood", res1["current_node_id"], "opt_approaching_flooded_road", res1["history"])

        self.assertTrue(res2["is_complete"])
        self.assertIn("TURN AROUND, DON'T DROWN", res2["guidance"]["status"])
        avoid_actions = " ".join(res2["guidance"]["actions_to_avoid"])
        self.assertIn("DO NOT attempt to drive through waterlogged roads", avoid_actions)

    def test_landslide_lateral_sprint_branch(self):
        """
        Verify Landslide active path directs lateral escape sprint away from gully.
        """
        session = self.engine.start_session("landslide")
        res1 = self.engine.process_step("landslide", session["current_node_id"], "opt_active_slide", session["history"])
        res2 = self.engine.process_step("landslide", res1["current_node_id"], "opt_active_outdoors_path", res1["history"])
        res3 = self.engine.process_step("landslide", res2["current_node_id"], "opt_can_sprint_lateral", res2["history"])

        self.assertTrue(res3["is_complete"])
        self.assertIn("LATERAL SPRINT", res3["guidance"]["status"])
        avoid_actions = " ".join(res3["guidance"]["actions_to_avoid"])
        self.assertIn("NEVER run downhill in the direction of the slide", avoid_actions)

    def test_error_handling_invalid_inputs(self):
        """Verify proper exceptions on invalid inputs."""
        with self.assertRaises(RuleEngineError):
            self.engine.start_session("tornado")

        with self.assertRaises(RuleEngineError):
            self.engine.process_step("earthquake", "eq_start", "non_existent_option")

        with self.assertRaises(RuleEngineError):
            self.engine.process_step("earthquake", "invalid_node_id", "opt_indoors")

    def test_transcript_formatting(self):
        """Test transcript generation produces expected formatted text."""
        session = self.engine.start_session("earthquake")
        res1 = self.engine.process_step("earthquake", session["current_node_id"], "opt_outdoors", session["history"])
        res2 = self.engine.process_step("earthquake", res1["current_node_id"], "opt_open_park", res1["history"])

        transcript = self.engine.generate_transcript_text(res2["history"], "Earthquake")
        self.assertIn("DISASTERSHIELD — OFFICIAL GUIDANCE CHATBOT TRANSCRIPT", transcript)
        self.assertIn("USER:", transcript)
        self.assertIn("DISASTERSHIELD BOT:", transcript)
        self.assertIn("IMMEDIATE LIFE-SAFETY ACTIONS:", transcript)

    def test_mermaid_generation(self):
        """Verify Mermaid graph generation syntax."""
        mermaid_code = self.engine.get_flowchart_mermaid("earthquake")
        self.assertTrue(mermaid_code.startswith("flowchart TD"))
        self.assertIn("classDef", mermaid_code)
        self.assertIn("eq_start", mermaid_code)


if __name__ == "__main__":
    unittest.main()
