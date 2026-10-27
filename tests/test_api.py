"""
Integration Test Suite for DisasterShield Flask Endpoints
==========================================================
Validates REST API responses, error handling, JSON structures,
and session workflows.
"""

import unittest
import json
from app import app


class TestDisasterShieldAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        app.config["TESTING"] = True
        cls.client = app.test_client()

    def test_health_endpoint(self):
        """Test health endpoint."""
        res = self.client.get("/health")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "healthy")

    def test_index_page(self):
        """Test main homepage renders HTML."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        html = res.data.decode("utf-8")
        self.assertIn("DisasterShield", html)
        self.assertIn("Select Disaster Scenario", html)

    def test_get_disasters(self):
        """Test disasters catalog endpoint."""
        res = self.client.get("/api/disasters")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(len(data.get("data", [])), 3)

    def test_start_chat_success(self):
        """Test starting a valid chat session."""
        res = self.client.post("/api/chat/start", json={"disaster_id": "flood"})
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        session = data.get("session", {})
        self.assertEqual(session.get("disaster_id"), "flood")
        self.assertEqual(session.get("current_node_id"), "flood_start")
        self.assertFalse(session.get("is_complete"))

    def test_start_chat_invalid_disaster(self):
        """Test starting chat with unknown disaster ID."""
        res = self.client.post("/api/chat/start", json={"disaster_id": "hurricane"})
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data.get("status"), "error")

    def test_start_chat_missing_payload(self):
        """Test missing payload."""
        res = self.client.post("/api/chat/start", json={})
        self.assertEqual(res.status_code, 400)

    def test_chat_step_progression(self):
        """Test advancing a decision tree step via API."""
        start_res = self.client.post("/api/chat/start", json={"disaster_id": "earthquake"})
        session = start_res.get_json()["session"]

        step_res = self.client.post("/api/chat/step", json={
            "disaster_id": "earthquake",
            "current_node_id": session["current_node_id"],
            "option_id": "opt_indoors",
            "history": session["history"]
        })

        self.assertEqual(step_res.status_code, 200)
        data = step_res.get_json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["step_result"]["current_node_id"], "eq_indoor_status")

    def test_transcript_generation(self):
        """Test transcript generation endpoint."""
        sample_history = [
            {
                "timestamp": "2026-10-22 10:00:00",
                "sender": "bot",
                "type": "question",
                "step": 1,
                "text": "Where are you located?",
                "options": [{"text": "Indoors"}]
            },
            {
                "timestamp": "2026-10-22 10:00:15",
                "sender": "user",
                "type": "answer",
                "text": "Indoors"
            }
        ]

        res = self.client.post("/api/chat/transcript", json={
            "history": sample_history,
            "disaster_name": "Earthquake"
        })

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("DISASTERSHIELD — OFFICIAL GUIDANCE CHATBOT TRANSCRIPT", data.get("transcript"))

    def test_checklist_endpoint(self):
        """Test checklist endpoint."""
        res = self.client.get("/api/checklist")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("categories", data.get("data", {}))

    def test_sources_endpoint(self):
        """Test sources endpoint."""
        res = self.client.get("/api/sources")
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data.get("status"), "success")
        self.assertIn("sources", data.get("data", {}))
        self.assertIn("hotlines", data.get("data", {}))

    def test_flowchart_endpoint(self):
        """Test flowchart endpoint for earthquake, flood, landslide."""
        for dis in ["earthquake", "flood", "landslide"]:
            res = self.client.get(f"/api/flowchart/{dis}")
            self.assertEqual(res.status_code, 200)
            data = res.get_json()
            self.assertEqual(data.get("status"), "success")
            self.assertIn("graph", data)
            self.assertIn("mermaid", data)


if __name__ == "__main__":
    unittest.main()
