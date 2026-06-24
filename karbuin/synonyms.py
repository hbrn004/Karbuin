"""synonyms.py — Synonym group resolution (additive v1.2).

Provides:
- SynonymResolver: maps synonym phrases to canonical symptom_ids
- FuzzyMatcher: typo-tolerant matching (edit distance 1-2)
- ContextTagger: disambiguates context-dependent phrases (e.g., "panas" = engine vs weather)

This is ADDITIVE — does NOT modify the existing SymptomParser.
Server can choose to call SymptomParser.parse() OR .parse_v12() for the new features.
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Iterable


# ── Edit distance (Levenshtein) — bounded for performance ──────
def levenshtein(s1: str, s2: str, max_dist: int = 3) -> int:
    """Bounded Levenshtein — returns max_dist+1 if distance exceeds max_dist."""
    if abs(len(s1) - len(s2)) > max_dist:
        return max_dist + 1
    if not s1:
        return len(s2)
    if not s2:
        return len(s1)
    prev = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1, 1):
        curr = [i] + [0] * len(s2)
        for j, c2 in enumerate(s2, 1):
            cost = 0 if c1 == c2 else 1
            curr[j] = min(curr[j-1] + 1, prev[j] + 1, prev[j-1] + cost)
            if min(prev[j], curr[j-1], prev[j-1]) > max_dist:
                return max_dist + 1
        prev = curr
    return prev[-1]


# ── Synonym group resolver ──────────────────────────────────────
class SynonymResolver:
    """Maps synonym phrases to canonical symptom_id.

    Loads from data/seed/synonym_groups.json.
    Each group has: name, canonical_id, phrases[].
    """

    def __init__(self, seed_dir: Path | None = None):
        self.groups: list[dict] = []
        # phrase_lower -> (canonical_id, group_name, base_conf)
        self.phrase_index: dict[str, tuple[str, str, float]] = {}
        if seed_dir:
            self.load(seed_dir)

    def load(self, seed_dir: Path) -> None:
        path = Path(seed_dir) / "synonym_groups.json"
        if not path.exists():
            return
        with open(path) as f:
            data = json.load(f)
        for group in data.get("groups", []):
            self.groups.append(group)
            cid = group["canonical_id"]
            gname = group["name"]
            for phrase in group.get("phrases", []):
                p = phrase.lower().strip()
                if p and p not in self.phrase_index:
                    self.phrase_index[p] = (cid, gname, 0.9)

    def resolve(self, text: str) -> list[tuple[str, float, str]]:
        """Find synonym matches in text. Returns [(canonical_id, confidence, group_name)]."""
        if not text:
            return []
        text_lower = text.lower()
        seen: dict[str, tuple[float, str]] = {}
        for phrase, (cid, gname, conf) in self.phrase_index.items():
            if phrase in text_lower:
                if cid not in seen or seen[cid][0] < conf:
                    seen[cid] = (conf, gname)
        return [(cid, c, g) for cid, (c, g) in seen.items()]


# ── Fuzzy matcher (typo tolerance) ──────────────────────────────
class FuzzyMatcher:
    """Matches a single token against known phrases with typo tolerance.

    Threshold: edit distance <= 2 for phrases >= 5 chars; <= 1 for shorter.
    Maps matched phrase → symptom_id via callback.
    """

    def __init__(self, phrase_to_id: dict[str, str], max_dist: int = 2):
        # phrase_lower -> symptom_id
        self.phrase_to_id: dict[str, str] = dict(phrase_to_id)
        self.phrases: list[str] = list(phrase_to_id.keys())
        self.max_dist = max_dist

    def match(self, text: str) -> list[tuple[str, str, int]]:
        """Find fuzzy matches. Returns [(symptom_id, matched_phrase, edit_distance)]."""
        if not text:
            return []
        text_lower = text.lower()
        words = text_lower.split()
        out: list[tuple[str, str, int]] = []
        seen: set[tuple[str, int]] = set()
        for word in words:
            for phrase in self.phrases:
                threshold = 2 if len(phrase) >= 5 else 1
                d = levenshtein(word, phrase, max_dist=threshold)
                if 0 < d <= threshold:
                    sid = self.phrase_to_id[phrase]
                    key = (sid, d)
                    if key not in seen:
                        seen.add(key)
                        out.append((sid, phrase, d))
        return out


# ── Context tagger ──────────────────────────────────────────────
# Heuristics for ambiguous phrases
CONTEXT_RULES = {
    "panas": {
        "engine": ["mesin", "engine", "motor", "knalpot", "kepala silinder", "overheat"],
        "weather": ["cuaca", "hari", "udara", "matahari", "tengah hari", "siang"]
    },
    "dingin": {
        "engine": ["mesin", "engine", "starter", "pagi", "subuh", "mesin dingin"],
        "weather": ["cuaca", "hari", "udara", "pagi", "pagi hari"]
    },
    "berat": {
        "engine": ["engkol", "starter", "kick", "kickstarter", "diengkol", "tarik gas", "tarik"],
        "general": []  # default
    },
    "mati": {
        "engine": ["mesin", "engine", "motor", "lampu merah", "langsam", "rem", "lampu", "starter"],
        "electrical": ["lampu", "aki", "kelistrikan", "listrik"]
    }
}


def tag_context(text: str) -> dict[str, str]:
    """Tag ambiguous words in text with their likely context.

    Returns {word: context_tag} for each ambiguous word found.
    """
    if not text:
        return {}
    text_lower = text.lower()
    out: dict[str, str] = {}
    for word, rules in CONTEXT_RULES.items():
        if word in text_lower:
            # Check if any engine context word is also in text
            for ctx_word in rules.get("engine", []):
                if ctx_word in text_lower:
                    out[word] = "engine"
                    break
            else:
                for ctx_word in rules.get("weather", []):
                    if ctx_word in text_lower:
                        out[word] = "weather" if "weather" in rules else "general"
                        break
                else:
                    out[word] = "engine"  # default for engine domain
    return out
