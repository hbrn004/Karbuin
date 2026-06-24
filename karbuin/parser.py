"""SymptomParser — rule-based free-text → symptom IDs.

NO LLM. Pure alias matching + substring detection.
Deterministic, auditable, no hallucination.

v1.2 ADDITIVE: added parse_v12() which extends parse() with:
  - Synonym group resolution (synonyms.py)
  - Fuzzy matching for typo tolerance
  - Context awareness for ambiguous phrases

The original parse() / parse_with_details() are UNCHANGED.
"""
from __future__ import annotations
from pathlib import Path

# v1.2: optional import (synonyms module is v1.2 additive)
try:
    from .synonyms import SynonymResolver, FuzzyMatcher, tag_context
    _SYNONYMS_AVAILABLE = True
except ImportError:
    _SYNONYMS_AVAILABLE = False


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

    # ──────────────────────────────────────────────────────────────
    # v1.2 ADDITIVE: enhanced parser with synonyms + fuzzy + context
    # ──────────────────────────────────────────────────────────────

    def init_v12(self, seed_dir: Path | None = None) -> None:
        """Initialize v1.2 enhancements (call once after construction).

        Idempotent: safe to call multiple times.
        Loads SynonymResolver + builds FuzzyMatcher from all alias phrases.
        """
        if not _SYNONYMS_AVAILABLE:
            return
        # Default seed_dir is project's data/seed (callers can override)
        if seed_dir is None:
            # Try to find the seed dir relative to this module
            seed_dir = Path(__file__).parent.parent / "data" / "seed"
        if not getattr(self, "_v12_initialized", False):
            self.synonym_resolver = SynonymResolver(seed_dir)
            # Build phrase -> symptom_id map from gejala
            phrase_to_id: dict[str, str] = {}
            for g in self.kb.gejala:
                sid = g["id"]
                phrase_to_id[g["name"].lower()] = sid
                for a in g.get("aliases", []):
                    phrase_to_id[a.lower()] = sid
            # Also add synonym phrases
            for phrase, (cid, _gname, _conf) in self.synonym_resolver.phrase_index.items():
                phrase_to_id[phrase] = cid
            self.fuzzy_matcher = FuzzyMatcher(phrase_to_id, max_dist=2)
            self._v12_initialized = True

    def parse_v12(self, text: str) -> dict:
        """v1.2 enhanced parse: returns dict with matches + metadata.

        Returns:
        {
            "matches": [(symptom_id, confidence, source, phrase), ...],
            "context_tags": {word: context},
            "synonym_groups_hit": [group_name, ...],
            "fuzzy_matches": [(phrase, distance), ...],
            "version": "1.2"
        }

        Existing parse() still works. This is the additive v1.2 version.
        v1.2.2: matched_phrase now included in each match tuple.
        """
        if not _SYNONYMS_AVAILABLE:
            return {"matches": [], "version": "1.0_fallback"}

        if not getattr(self, "_v12_initialized", False):
            self.init_v12()

        text_lower = (text or "").lower()

        # 1. Alias-based matching (with phrase tracking)
        merged: dict[str, tuple[float, str, str]] = {}  # (conf, source, phrase)
        for phrase, sid, base_conf in self.alias_index:
            if phrase and phrase in text_lower:
                if sid not in merged or merged[sid][0] < base_conf:
                    merged[sid] = (base_conf, "alias", phrase)

        # 2. Synonym group resolution (with phrase tracking)
        syn_groups_hit: list[str] = []
        for phrase, (cid, gname, conf) in self.synonym_resolver.phrase_index.items():
            if phrase in text_lower:
                if cid not in merged or merged[cid][0] < conf:
                    merged[cid] = (conf, f"synonym:{gname}", phrase)
                if gname not in syn_groups_hit:
                    syn_groups_hit.append(gname)

        # 3. Context tags
        context_tags = tag_context(text)

        # 4. Fuzzy matches (typo tolerance) — only add if not already matched
        fuzzy = self.fuzzy_matcher.match(text)
        for sid, phrase, dist in fuzzy:
            if sid not in merged:
                conf = 0.6 - (dist * 0.1)
                merged[sid] = (conf, f"fuzzy:{phrase}:d{dist}", phrase)

        return {
            "matches": [(sid, c, src, p) for sid, (c, src, p) in merged.items()],
            "context_tags": context_tags,
            "synonym_groups_hit": syn_groups_hit,
            "fuzzy_matches": [(p, d) for _, p, d in fuzzy],
            "version": "1.2",
        }