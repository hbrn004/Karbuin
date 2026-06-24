"""SymptomParser — rule-based free-text → symptom IDs.

NO LLM. Pure alias matching + substring detection.
Deterministic, auditable, no hallucination.
"""
from __future__ import annotations


class SymptomParser:
    def __init__(self, kb):
        self.kb = kb
        self._build_index()

    def _build_index(self):
        # list of (phrase_lower, symptom_id, base_confidence)
        self.alias_index: list[tuple[str, str, float]] = []
        for g in self.kb.gejala:
            sid = g["id"]
            # canonical name → 0.7 base conf
            self.alias_index.append((g["name"].lower(), sid, 0.7))
            # aliases → 0.85 base conf (more colloquial → higher conf when matched)
            for alias in g.get("aliases", []):
                self.alias_index.append((alias.lower(), sid, 0.85))

    def parse(self, text: str) -> list[tuple[str, float]]:
        """Parse user free text → list of (symptom_id, confidence).

        Strategy: substring matching, longest match wins per symptom.
        No tokenization tricks — simple and auditable.
        """
        if not text:
            return []
        text_lower = text.lower()
        matches: dict[str, float] = {}
        for phrase, sid, base_conf in self.alias_index:
            if phrase and phrase in text_lower:
                # longest phrase wins
                existing = matches.get(sid, 0)
                if base_conf > existing:
                    matches[sid] = base_conf
        return list(matches.items())

    def parse_with_details(self, text: str) -> list[dict]:
        """Same as parse() but returns matched phrase for auditability."""
        if not text:
            return []
        text_lower = text.lower()
        results: dict[str, dict] = {}
        for phrase, sid, base_conf in self.alias_index:
            if phrase and phrase in text_lower:
                if sid not in results or base_conf > results[sid]["confidence"]:
                    results[sid] = {
                        "symptom_id": sid,
                        "matched_phrase": phrase,
                        "confidence": base_conf,
                    }
        return list(results.values())