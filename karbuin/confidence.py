"""Confidence tier classification.

Per Phase 1 decisions:
  < 0.60      → "Data tidak cukup"
  0.60 - 0.74 → "Kemungkinan sedang"
  0.75 - 0.89 → "Kemungkinan tinggi"
  ≥ 0.90      → "Sangat tinggi"
"""

TIERS = [
    (0.90, "Sangat tinggi"),
    (0.75, "Kemungkinan tinggi"),
    (0.60, "Kemungkinan sedang"),
    (0.00, "Data tidak cukup"),
]


def classify_tier(confidence: float) -> str:
    for threshold, label in TIERS:
        if confidence >= threshold:
            return label
    return "Data tidak cukup"


def is_actionable(confidence: float) -> bool:
    """Whether diagnosis is safe to show to user."""
    return confidence >= 0.60