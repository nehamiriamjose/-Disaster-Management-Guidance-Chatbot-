"""
DisasterShield — Rule-Based Decision Tree Chatbot Engine
=========================================================
Implements pure Python decision-tree traversal based on pre-compiled,
expert-validated disaster management protocols (NDMA, GSI, CWC, NDRF).
No external AI or non-deterministic APIs are used.
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional


class RuleEngineError(Exception):
    """Custom exception raised for rule engine validation errors."""
    pass


class DisasterRuleEngine:
    """
    State-machine rule engine for traversing disaster guidance decision trees.
    """

    def __init__(self, data_dir: Optional[str] = None):
        if data_dir is None:
            data_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
        self.data_dir = data_dir
        self.disasters: Dict[str, Dict[str, Any]] = {}
        self.checklist: Dict[str, Any] = {}
        self.sources: Dict[str, Any] = {}
        self._load_all_data()

    def _load_all_data(self) -> None:
        """Load JSON datasets from data directory into memory."""
        disaster_keys = ["earthquake", "flood", "landslide"]
        for key in disaster_keys:
            filepath = os.path.join(self.data_dir, f"{key}.json")
            if not os.path.exists(filepath):
                raise FileNotFoundError(f"Required decision tree data file not found: {filepath}")
            with open(filepath, "r", encoding="utf-8") as f:
                self.disasters[key] = json.load(f)

        checklist_path = os.path.join(self.data_dir, "checklist.json")
        if os.path.exists(checklist_path):
            with open(checklist_path, "r", encoding="utf-8") as f:
                self.checklist = json.load(f)

        sources_path = os.path.join(self.data_dir, "sources.json")
        if os.path.exists(sources_path):
            with open(sources_path, "r", encoding="utf-8") as f:
                self.sources = json.load(f)

    def get_available_disasters(self) -> List[Dict[str, Any]]:
        """Return catalog of available disasters for homepage cards."""
        catalog = []
        for key, data in self.disasters.items():
            catalog.append({
                "id": data.get("id", key),
                "name": data.get("name"),
                "category": data.get("category"),
                "badge": data.get("badge"),
                "icon": data.get("icon"),
                "description": data.get("description"),
                "total_nodes": len(data.get("nodes", {}))
            })
        return catalog

    def get_disaster_meta(self, disaster_id: str) -> Dict[str, Any]:
        """Return metadata for a specific disaster."""
        if disaster_id not in self.disasters:
            raise RuleEngineError(f"Disaster '{disaster_id}' is not recognized.")
        data = self.disasters[disaster_id]
        return {
            "id": data.get("id"),
            "name": data.get("name"),
            "category": data.get("category"),
            "badge": data.get("badge"),
            "description": data.get("description"),
            "root_node": data.get("root_node")
        }

    def start_session(self, disaster_id: str) -> Dict[str, Any]:
        """
        Initialize a new conversation session for a disaster scenario.
        Returns the initial root node and empty session state.
        """
        disaster_id = disaster_id.lower().strip()
        if disaster_id not in self.disasters:
            raise RuleEngineError(
                f"Unknown disaster identifier: '{disaster_id}'. "
                f"Valid options are: {list(self.disasters.keys())}"
            )

        data = self.disasters[disaster_id]
        root_node_id = data.get("root_node")
        nodes = data.get("nodes", {})

        if root_node_id not in nodes:
            raise RuleEngineError(f"Root node '{root_node_id}' missing in {disaster_id} configuration.")

        root_node = nodes[root_node_id]

        initial_history_item = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "sender": "bot",
            "type": "question",
            "step": root_node.get("step", 1),
            "node_id": root_node_id,
            "text": root_node.get("prompt"),
            "context": root_node.get("context"),
            "urgency": root_node.get("urgency", "NORMAL"),
            "options": [
                {"id": opt["id"], "text": opt["text"], "description": opt.get("description", "")}
                for opt in root_node.get("options", [])
            ]
        }

        return {
            "disaster_id": disaster_id,
            "disaster_name": data.get("name"),
            "current_node_id": root_node_id,
            "step": root_node.get("step", 1),
            "is_complete": False,
            "node": root_node,
            "history": [initial_history_item]
        }

    def process_step(
        self,
        disaster_id: str,
        current_node_id: str,
        option_id: str,
        existing_history: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """
        Process user selection, navigate decision branch, and generate the next step or terminal guidance.
        """
        disaster_id = disaster_id.lower().strip()
        if disaster_id not in self.disasters:
            raise RuleEngineError(f"Disaster '{disaster_id}' does not exist.")

        data = self.disasters[disaster_id]
        nodes = data.get("nodes", {})

        if current_node_id not in nodes:
            raise RuleEngineError(f"Node '{current_node_id}' does not exist in '{disaster_id}'.")

        current_node = nodes[current_node_id]
        options = current_node.get("options", [])

        # Find matching option
        matched_option = None
        for opt in options:
            if opt.get("id") == option_id:
                matched_option = opt
                break

        if not matched_option:
            raise RuleEngineError(
                f"Option '{option_id}' is invalid for node '{current_node_id}'. "
                f"Available options: {[o.get('id') for o in options]}"
            )

        next_node_id = matched_option.get("next_node")
        if not next_node_id or next_node_id not in nodes:
            raise RuleEngineError(f"Target node '{next_node_id}' not found in '{disaster_id}'.")

        next_node = nodes[next_node_id]
        history = list(existing_history or [])
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Record user's choice
        history.append({
            "timestamp": now_str,
            "sender": "user",
            "type": "answer",
            "node_id": current_node_id,
            "selected_option_id": option_id,
            "text": matched_option.get("text"),
            "description": matched_option.get("description", "")
        })

        is_terminal = next_node.get("is_terminal", False) or ("guidance" in next_node)

        if is_terminal:
            guidance = next_node.get("guidance", {})
            history.append({
                "timestamp": now_str,
                "sender": "bot",
                "type": "guidance",
                "step": next_node.get("step", 4),
                "node_id": next_node_id,
                "status": guidance.get("status"),
                "severity": guidance.get("severity"),
                "summary": guidance.get("summary"),
                "immediate_actions": guidance.get("immediate_actions", []),
                "actions_to_avoid": guidance.get("actions_to_avoid", []),
                "preventive_measures": guidance.get("preventive_measures", []),
                "emergency_contacts": guidance.get("emergency_contacts", []),
                "official_reference": guidance.get("official_reference")
            })

            return {
                "disaster_id": disaster_id,
                "disaster_name": data.get("name"),
                "current_node_id": next_node_id,
                "step": next_node.get("step", 4),
                "is_complete": True,
                "guidance": guidance,
                "node": next_node,
                "history": history
            }
        else:
            # Interim question node
            bot_question = {
                "timestamp": now_str,
                "sender": "bot",
                "type": "question",
                "step": next_node.get("step", 2),
                "node_id": next_node_id,
                "text": next_node.get("prompt"),
                "context": next_node.get("context"),
                "urgency": next_node.get("urgency", "NORMAL"),
                "options": [
                    {"id": opt["id"], "text": opt["text"], "description": opt.get("description", "")}
                    for opt in next_node.get("options", [])
                ]
            }
            history.append(bot_question)

            return {
                "disaster_id": disaster_id,
                "disaster_name": data.get("name"),
                "current_node_id": next_node_id,
                "step": next_node.get("step", 2),
                "is_complete": False,
                "node": next_node,
                "history": history
            }

    def generate_transcript_text(self, history: List[Dict[str, Any]], disaster_name: str = "") -> str:
        """
        Format the conversation history into a clean human-readable transcript.
        """
        lines = []
        lines.append("=================================================================")
        lines.append(f"  DISASTERSHIELD — OFFICIAL GUIDANCE CHATBOT TRANSCRIPT")
        lines.append(f"  Scenario: {disaster_name or 'General Disaster Safety'}")
        lines.append(f"  Generated On: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append("=================================================================\n")

        for idx, entry in enumerate(history, 1):
            sender = "DISASTERSHIELD BOT" if entry.get("sender") == "bot" else "USER"
            timestamp = entry.get("timestamp", "")
            entry_type = entry.get("type", "")

            lines.append(f"[{timestamp}] {sender}:")

            if entry_type == "question":
                step = entry.get("step", "")
                urgency = entry.get("urgency", "")
                lines.append(f"  Step {step} Assessment ({urgency}):")
                lines.append(f"  Q: {entry.get('text')}")
                if entry.get("context"):
                    lines.append(f"  Note: {entry.get('context')}")
                lines.append("  Options presented:")
                for opt in entry.get("options", []):
                    lines.append(f"    * {opt.get('text')}")

            elif entry_type == "answer":
                lines.append(f"  A: {entry.get('text')}")

            elif entry_type == "guidance":
                lines.append(f"  >>> STATUS: {entry.get('status')} <<<")
                lines.append(f"  Summary: {entry.get('summary')}\n")
                lines.append("  IMMEDIATE LIFE-SAFETY ACTIONS:")
                for act in entry.get("immediate_actions", []):
                    lines.append(f"    [!] {act}")
                lines.append("\n  ACTIONS TO AVOID:")
                for av in entry.get("actions_to_avoid", []):
                    lines.append(f"    [X] {av}")
                lines.append("\n  PREVENTIVE & RECOVERY MEASURES:")
                for pm in entry.get("preventive_measures", []):
                    lines.append(f"    [-] {pm}")
                lines.append("\n  VERIFIED EMERGENCY CONTACTS:")
                for ec in entry.get("emergency_contacts", []):
                    lines.append(f"    * {ec.get('name')}: {ec.get('number')}")
                lines.append(f"\n  Official Reference: {entry.get('official_reference')}")

            lines.append("-" * 65)

        return "\n".join(lines)

    def get_flowchart_mermaid(self, disaster_id: str) -> str:
        """
        Generate a strict Mermaid flowchart markdown diagram representing the decision tree.
        """
        disaster_id = disaster_id.lower().strip()
        if disaster_id not in self.disasters:
            raise RuleEngineError(f"Disaster '{disaster_id}' not found.")

        data = self.disasters[disaster_id]
        nodes = data.get("nodes", {})
        root_node = data.get("root_node")

        lines = [
            "flowchart TD",
            f"  classDef startNode fill:#1e3a5f,stroke:#3b82f6,stroke-width:2px,color:#ffffff,font-weight:bold;",
            f"  classDef questionNode fill:#f0f9ff,stroke:#0284c7,stroke-width:2px,color:#0f172a;",
            f"  classDef criticalGuidance fill:#fef2f2,stroke:#dc2626,stroke-width:2px,color:#991b1b,font-weight:bold;",
            f"  classDef urgentGuidance fill:#fffbeb,stroke:#d97706,stroke-width:2px,color:#92400e,font-weight:bold;",
            f"  classDef normalGuidance fill:#f0fdf4,stroke:#16a34a,stroke-width:2px,color:#166534,font-weight:bold;",
            ""
        ]

        for node_id, node in nodes.items():
            if node.get("is_terminal"):
                guidance = node.get("guidance", {})
                status = guidance.get("status", "Guidance Outcome")
                sev = guidance.get("severity", "NORMAL")
                clean_title = status.replace('"', '').replace("'", "")
                lines.append(f'  {node_id}["{clean_title}"]')
                if sev == "CRITICAL":
                    lines.append(f"  class {node_id} criticalGuidance;")
                elif sev == "URGENT":
                    lines.append(f"  class {node_id} urgentGuidance;")
                else:
                    lines.append(f"  class {node_id} normalGuidance;")
            else:
                prompt = node.get("prompt", "")
                # Truncate prompt if long for clean diagram rendering
                short_prompt = prompt if len(prompt) <= 60 else prompt[:57] + "..."
                clean_prompt = short_prompt.replace('"', '').replace("'", "")
                step = node.get("step", 1)
                lines.append(f'  {node_id}["Step {step}: {clean_prompt}"]')
                if node_id == root_node:
                    lines.append(f"  class {node_id} startNode;")
                else:
                    lines.append(f"  class {node_id} questionNode;")

                for opt in node.get("options", []):
                    next_id = opt.get("next_node")
                    opt_text = opt.get("text", "")
                    short_opt = opt_text if len(opt_text) <= 35 else opt_text[:32] + "..."
                    clean_opt = short_opt.replace('"', '').replace("'", "")
                    if next_id:
                        lines.append(f'  {node_id} -->|"{clean_opt}"| {next_id}')

        return "\n".join(lines)

    def get_flowchart_graph(self, disaster_id: str) -> Dict[str, Any]:
        """
        Return structured nodes and edges for rendering in custom HTML/SVG canvas.
        """
        disaster_id = disaster_id.lower().strip()
        if disaster_id not in self.disasters:
            raise RuleEngineError(f"Disaster '{disaster_id}' not found.")

        data = self.disasters[disaster_id]
        nodes = data.get("nodes", {})
        graph_nodes = []
        graph_edges = []

        for node_id, node in nodes.items():
            is_term = node.get("is_terminal", False) or ("guidance" in node)
            node_info = {
                "id": node_id,
                "step": node.get("step", 1),
                "is_terminal": is_term,
                "label": node.get("guidance", {}).get("status") if is_term else node.get("prompt"),
                "urgency": node.get("urgency") or node.get("guidance", {}).get("severity", "NORMAL"),
                "is_root": node_id == data.get("root_node")
            }
            graph_nodes.append(node_info)

            if not is_term:
                for opt in node.get("options", []):
                    next_id = opt.get("next_node")
                    if next_id:
                        graph_edges.append({
                            "from": node_id,
                            "to": next_id,
                            "label": opt.get("text"),
                            "description": opt.get("description", "")
                        })

        return {
            "disaster_id": disaster_id,
            "disaster_name": data.get("name"),
            "root_node": data.get("root_node"),
            "nodes": graph_nodes,
            "edges": graph_edges
        }

    def get_all_paths(self, disaster_id: str) -> List[List[str]]:
        """
        Depth-first search to extract all possible decision paths from root to terminal nodes.
        Useful for exhaustive testing and coverage validation.
        """
        disaster_id = disaster_id.lower().strip()
        if disaster_id not in self.disasters:
            raise RuleEngineError(f"Disaster '{disaster_id}' not found.")

        data = self.disasters[disaster_id]
        nodes = data.get("nodes", {})
        root_node_id = data.get("root_node")

        paths: List[List[str]] = []

        def dfs(current_id: str, current_path: List[str]):
            if current_id not in nodes:
                return
            node = nodes[current_id]
            extended_path = current_path + [current_id]

            if node.get("is_terminal") or "guidance" in node:
                paths.append(extended_path)
                return

            options = node.get("options", [])
            for opt in options:
                next_id = opt.get("next_node")
                if next_id:
                    dfs(next_id, extended_path)

        dfs(root_node_id, [])
        return paths
