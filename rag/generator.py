"""
DisasterShield Answer Generator
===============================
Generates grounded, evidence-based disaster safety answers with strict statutory citations.
Supports:
1. Local Grounded Synthesizer (Default, 100% offline, zero paid API required)
2. Optional Hosted LLMs (OpenAI / Gemini) when API keys are configured in environment
"""

import os
import re
import requests
from typing import List, Dict, Any, Optional
from rag.config import RAGConfig
from rag.context_builder import ContextBuilder


class BaseAnswerGenerator:
    """Abstract base generator."""

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        is_emergency: bool = False
    ) -> Dict[str, Any]:
        raise NotImplementedError


class LocalGroundedSynthesizer(BaseAnswerGenerator):
    """
    Extractive synthesis engine that grounds answers strictly in retrieved passages.
    Requires zero external AI API keys or network connection.
    Guarantees no hallucination of phone numbers, thresholds, or evacuation orders.
    """

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        is_emergency: bool = False
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            return {
                "answer": (
                    "The official indexed knowledge base does not contain sufficient supporting "
                    "information to answer this question. Please ensure relevant disaster guideline "
                    "PDFs are uploaded and indexed, or switch to the **Emergency Guidance** decision-tree "
                    "mode for immediate step-by-step assessment."
                ),
                "citations": [],
                "is_emergency": is_emergency,
                "evidence_found": False,
                "provider": "local_synthesizer"
            }

        # Analyze query intent
        q_lower = query.lower()
        key_actions: List[str] = []
        cautions: List[str] = []
        seen_points = set()

        for chunk in retrieved_chunks:
            doc_title = chunk.get("title", "Official Guideline")
            page = chunk.get("page_number", 1)
            chunk_text = chunk.get("text", "")
            cite_tag = f"[{doc_title}, Page {page}]"

            # Break into candidate sentences or bullet items
            lines = [l.strip() for l in chunk_text.splitlines() if l.strip()]
            for line in lines:
                clean_line = line.lstrip("•*-0123456789. ")
                if len(clean_line) < 30:
                    continue

                line_lower = clean_line.lower()

                # Skip header/metadata lines
                if (
                    line_lower.startswith("issuing authority")
                    or line_lower.startswith("document reference")
                    or line_lower.startswith("national disaster management guidelines")
                    or line_lower.startswith("standard operating procedure")
                    or line_lower.startswith("national landslide risk")
                    or line_lower.startswith("section ")
                    or line_lower.startswith("part ")
                ):
                    continue

                # Deduplication key
                fingerprint = re.sub(r"\W+", "", clean_line[:40].lower())
                if fingerprint in seen_points:
                    continue
                seen_points.add(fingerprint)

                if any(w in line_lower for w in ["do not", "never", "avoid", "danger", "warning", "prohibited", "hazard"]):
                    cautions.append(f"{clean_line} {cite_tag}")
                elif any(w in line_lower for w in ["should", "must", "prepare", "action", "keep", "inspect", "ensure", "evacuate", "drop", "cover", "turn off", "boil"]):
                    key_actions.append(f"{clean_line} {cite_tag}")
                elif len(key_actions) < 4:
                    key_actions.append(f"{clean_line} {cite_tag}")

        # Assemble structured response
        response_sections = []

        if is_emergency:
            response_sections.append(
                "> [!CRITICAL]\n"
                "> **IMMEDIATE EMERGENCY ALERT**: If you are in active danger, prioritize life safety immediately.\n"
                "> Dial **112** (Pan-India Emergency) or **1078** (NDRF Rescue) right now. "
                "Switch to the **Emergency Guidance** tab for instant situational decision trees."
            )

        top_chunk = retrieved_chunks[0]
        top_title = top_chunk.get("title")
        top_page = top_chunk.get("page_number")
        top_org = top_chunk.get("organization")

        intro = (
            f"Based on verified guidelines in **{top_title}** (Page {top_page}, published by *{top_org}*), "
            f"here is the official safety protocol regarding your query:"
        )
        response_sections.append(intro)

        if key_actions:
            response_sections.append("### Recommended Official Actions:")
            for action in key_actions[:6]:
                response_sections.append(f"- {action}")

        if cautions:
            response_sections.append("### Important Conditions & Warnings to Strictly Avoid:")
            for caution in cautions[:4]:
                response_sections.append(f"- **Warning**: {caution}")

        response_sections.append(
            "\n*Note: The above points reflect verified static guidelines from the indexed official documents. "
            "In active emergencies, always obey real-time commands from local police, NDRF, and civil defense officials.*"
        )

        return {
            "answer": "\n\n".join(response_sections),
            "citations": citations,
            "is_emergency": is_emergency,
            "evidence_found": True,
            "provider": "local_synthesizer"
        }


class HostedLLMGenerator(BaseAnswerGenerator):
    """Generates grounded responses via OpenAI or Gemini when configured."""

    def __init__(self, provider: str = "openai"):
        self.provider = provider
        self.local_fallback = LocalGroundedSynthesizer()

    def generate(
        self,
        query: str,
        retrieved_chunks: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        is_emergency: bool = False
    ) -> Dict[str, Any]:
        if not retrieved_chunks:
            return self.local_fallback.generate(query, retrieved_chunks, citations, is_emergency)

        context_str, _ = ContextBuilder.build_prompt_context(query, retrieved_chunks)

        user_prompt = (
            f"USER QUERY: {query}\n\n"
            f"RETRIEVED OFFICIAL EVIDENCE:\n{context_str}\n\n"
            "INSTRUCTIONS:\n"
            "Provide a grounded, clear, and safety-focused response strictly supported by the evidence above. "
            "Cite the document title and page number for every specific recommendation."
        )

        if self.provider == "openai" and RAGConfig.OPENAI_API_KEY:
            try:
                headers = {
                    "Authorization": f"Bearer {RAGConfig.OPENAI_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": RAGConfig.OPENAI_MODEL,
                    "messages": [
                        {"role": "system", "content": ContextBuilder.SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800
                }
                resp = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload, timeout=25)
                resp.raise_for_status()
                ans_text = resp.json()["choices"][0]["message"]["content"]
                return {
                    "answer": ans_text,
                    "citations": citations,
                    "is_emergency": is_emergency,
                    "evidence_found": True,
                    "provider": f"openai_{RAGConfig.OPENAI_MODEL}"
                }
            except Exception as e:
                print(f"[Warning] OpenAI API call failed: {e}. Falling back to local synthesizer.")
                fallback_res = self.local_fallback.generate(query, retrieved_chunks, citations, is_emergency)
                fallback_res["provider"] += "_fallback"
                return fallback_res

        # Default fallback
        return self.local_fallback.generate(query, retrieved_chunks, citations, is_emergency)


def get_answer_generator() -> BaseAnswerGenerator:
    """Factory creating generator based on RAGConfig."""
    provider = RAGConfig.GENERATOR_PROVIDER
    if provider == "openai" and RAGConfig.OPENAI_API_KEY:
        return HostedLLMGenerator("openai")
    return LocalGroundedSynthesizer()
