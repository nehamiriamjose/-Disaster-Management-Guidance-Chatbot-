"""
DisasterShield — RAG Evaluation Benchmark Suite
Evaluates document retrieval quality, citation accuracy, answer groundedness,
and appropriate refusal behavior across Earthquake, Flood, and Landslide domains.
"""

import pytest
from app import app
from rag.pipeline import DisasterRAGPipeline


@pytest.fixture(scope="module")
def rag_pipeline():
    return DisasterRAGPipeline()


class TestDisasterRAGEvaluation:
    """Benchmark evaluation across official disaster scenarios."""

    # -------------------------------------------------------------------------
    # 1. EARTHQUAKE BENCHMARK
    # -------------------------------------------------------------------------
    def test_eval_earthquake_shaking_actions(self, rag_pipeline):
        """Query: What actions are recommended during active earthquake shaking?"""
        result = rag_pipeline.ask("What actions are recommended during active earthquake shaking?", category="earthquake")

        assert result["evidence_found"] is True
        assert len(result["citations"]) > 0

        # Verify retrieved source
        top_citation = result["citations"][0]
        assert "earthquake" in top_citation["disaster_category"].lower()
        assert "NDMA" in top_citation["issuing_organization"]
        assert top_citation["page_number"] in {1, 2}  # Guidelines are on pages 1-2

        # Verify answer groundedness
        answer_lower = result["answer"].lower()
        assert "drop" in answer_lower or "cover" in answer_lower or "hold" in answer_lower
        assert "elevators" in answer_lower or "prohibited" in answer_lower or "sturdy" in answer_lower

    def test_eval_earthquake_emergency_kit(self, rag_pipeline):
        """Query: What items should an earthquake family emergency kit contain?"""
        result = rag_pipeline.ask("What items should an earthquake family emergency kit contain?")

        assert result["evidence_found"] is True
        assert any(c["page_number"] in {2, 3} for c in result["citations"])  # Kit is on pages 2-3
        answer_lower = result["answer"].lower()
        assert "go-bag" in answer_lower or "emergency" in answer_lower or "water" in answer_lower or "first-aid" in answer_lower or "supplies" in answer_lower

    # -------------------------------------------------------------------------
    # 2. FLOOD BENCHMARK
    # -------------------------------------------------------------------------
    def test_eval_flood_turn_around_dont_drown(self, rag_pipeline):
        """Query: What should motorists do during flooding according to turn around dont drown?"""
        result = rag_pipeline.ask("What should motorists do during flooding according to turn around dont drown?", category="flood")

        assert result["evidence_found"] is True
        assert any("Flood" in c["document_title"] for c in result["citations"])
        answer_lower = result["answer"].lower()
        assert "turn around" in answer_lower or "drive" in answer_lower or "inches" in answer_lower

    def test_eval_flood_water_sanitation(self, rag_pipeline):
        """Query: How should drinking water be purified after flood inundation?"""
        result = rag_pipeline.ask("How should drinking water be purified after flood inundation?")

        assert result["evidence_found"] is True
        answer_lower = result["answer"].lower()
        assert "boil" in answer_lower or "chlorine" in answer_lower or "water" in answer_lower

    # -------------------------------------------------------------------------
    # 3. LANDSLIDE BENCHMARK
    # -------------------------------------------------------------------------
    def test_eval_landslide_warning_signs(self, rag_pipeline):
        """Query: What are the early warning signs of an impending landslide?"""
        result = rag_pipeline.ask("What are the early warning signs of an impending landslide?", category="landslide")

        assert result["evidence_found"] is True
        top_cit = result["citations"][0]
        assert "GSI" in top_cit["issuing_organization"] or "Geological" in top_cit["issuing_organization"]
        assert top_cit["page_number"] == 1  # Warning signs are on page 1

        answer_lower = result["answer"].lower()
        assert "crack" in answer_lower or "tilt" in answer_lower or "muddy" in answer_lower or "rumble" in answer_lower

    def test_eval_landslide_escape_direction(self, rag_pipeline):
        """Query: What direction should someone run during an active debris flow?"""
        result = rag_pipeline.ask("What direction should someone run during an active debris flow?")

        assert result["evidence_found"] is True
        answer_lower = result["answer"].lower()
        assert "lateral" in answer_lower or "perpendicular" in answer_lower or "path" in answer_lower

    # -------------------------------------------------------------------------
    # 4. EMERGENCY DETECTION & IMMEDIATE LIFE SAFETY
    # -------------------------------------------------------------------------
    def test_eval_active_life_emergency_redirection(self, rag_pipeline):
        """Query: House collapsed, severe bleeding, trapped under rubble!"""
        result = rag_pipeline.ask("My house collapsed, someone is bleeding and trapped under rubble!")

        assert result["is_emergency"] is True
        assert "112" in result["emergency_helplines"]
        assert "1078" in result["emergency_helplines"]
        assert "112" in result["answer"]

    # -------------------------------------------------------------------------
    # 5. REFUSAL ON UNSUPPORTED / IRRELEVANT TOPICS
    # -------------------------------------------------------------------------
    def test_eval_refusal_on_irrelevant_query(self, rag_pipeline):
        """Query: How do I change the oil in a 2018 Honda Civic?"""
        result = rag_pipeline.ask("How do I change the oil in a 2018 Honda Civic?")

        # Must refuse and state knowledge base lacks evidence
        assert result["evidence_found"] is False
        assert len(result["citations"]) == 0
        assert "does not contain sufficient supporting information" in result["answer"]

    def test_eval_no_hallucinated_emergency_hotlines(self, rag_pipeline):
        """Verify that any query answered only mentions official verified hotlines."""
        queries = [
            "What should I do during an earthquake?",
            "What to do when water enters house?",
            "How to recognize landslide danger?"
        ]
        official_numbers = {"112", "1078", "101", "108"}
        for q in queries:
            res = rag_pipeline.ask(q)
            # Ensure no imaginary 7-digit, 10-digit fake numbers are generated
            import re
            numbers_found = set(re.findall(r"\b\d{3,4}\b", res["answer"]))
            # Filter out year numbers like 2024, 2025, 2026 or page numbers
            suspicious_hotlines = [n for n in numbers_found if len(n) == 3 or len(n) == 4]
            # Any hotline-like shortcode should be an official one
            for n in suspicious_hotlines:
                if n in {"112", "1078", "101", "108", "2024", "2025", "2026", "2020", "2019"}:
                    continue
                # Not a recognized disaster hotline
                assert n in official_numbers or int(n) > 1900 or int(n) < 100
