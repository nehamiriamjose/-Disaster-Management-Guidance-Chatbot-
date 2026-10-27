"""
DisasterShield — Transcript Generation Tool
Runs realistic user simulation through all 3 disaster trees and
generates official academic transcripts from actual execution.
"""

from chatbot_engine import DisasterRuleEngine
import os

engine = DisasterRuleEngine()

runs = [
    {
        "title": "Earthquake Scenario: Indoor Active Tremors with Trapped Signaling",
        "disaster_id": "earthquake",
        "steps": [
            ("eq_start", "opt_indoors"),
            ("eq_indoor_status", "opt_trapped"),
            ("eq_indoor_trapped_protocol", "opt_trapped_airway_open")
        ]
    },
    {
        "title": "Earthquake Scenario: Outdoor Downed Powerlines Hazard",
        "disaster_id": "earthquake",
        "steps": [
            ("eq_start", "opt_outdoors"),
            ("eq_outdoor_status", "opt_dense_urban"),
            ("eq_outdoor_urban_hazards", "opt_downed_wires")
        ]
    },
    {
        "title": "Flood Scenario: Motorist Approaching Submerged Road ('Turn Around, Don't Drown')",
        "disaster_id": "flood",
        "steps": [
            ("flood_start", "opt_in_vehicle"),
            ("flood_vehicle_severity", "opt_approaching_flooded_road")
        ]
    },
    {
        "title": "Flood Scenario: Residential Inundation with Submerged Electrical Breaker",
        "disaster_id": "flood",
        "steps": [
            ("flood_start", "opt_home_building"),
            ("flood_indoor_severity", "opt_water_entering_ground"),
            ("flood_indoor_utility_check", "opt_breaker_wet_submerged")
        ]
    },
    {
        "title": "Landslide Scenario: Active Debris Flow with Lateral Sprint Escape",
        "disaster_id": "landslide",
        "steps": [
            ("ls_start", "opt_active_slide"),
            ("ls_active_slide_location", "opt_active_outdoors_path"),
            ("ls_active_outdoor_escape_feasibility", "opt_can_sprint_lateral")
        ]
    },
    {
        "title": "Landslide Scenario: Slope Tension Cracking & Preemptive Hillside Evacuation",
        "disaster_id": "landslide",
        "steps": [
            ("ls_start", "opt_early_warning"),
            ("ls_early_warning_location", "opt_hillside_building"),
            ("ls_early_warning_signs_building", "opt_cracking_and_seepage")
        ]
    }
]

output_lines = [
    "# DisasterShield — Official Academic Conversation Transcripts",
    "Generated from Actual Test Runs on DisasterShield Rule-Based Engine",
    f"Timestamp: 2026-10-22",
    "",
    "> [!NOTE]",
    "> These transcripts document actual simulated sessions through the DisasterShield rule-based state machine.",
    "> Every step shows the question prompt, user selection, and resulting statutory NDMA/GSI guidance.",
    ""
]

for run in runs:
    disaster_id = run["disaster_id"]
    session = engine.start_session(disaster_id)
    history = session["history"]
    curr_node = session["current_node_id"]

    for node_id, opt_id in run["steps"]:
        res = engine.process_step(disaster_id, node_id, opt_id, history)
        history = res["history"]
        curr_node = res["current_node_id"]

    formatted_text = engine.generate_transcript_text(history, session["disaster_name"])
    output_lines.append(f"## {run['title']}")
    output_lines.append("```text")
    output_lines.append(formatted_text)
    output_lines.append("```")
    output_lines.append("")

os.makedirs("docs", exist_ok=True)
with open("docs/sample_transcript.md", "w", encoding="utf-8") as f:
    f.write("\n".join(output_lines))

print("[+] Successfully generated docs/sample_transcript.md with 6 diverse scenario test runs!")
