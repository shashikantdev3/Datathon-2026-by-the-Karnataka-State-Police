"""Lightweight English/Kannada UI strings + sample questions (bilingual support)."""

STRINGS = {
    "en": {
        "app_title": "CrimeSense — Conversational Crime Intelligence",
        "ask": "Ask about FIRs, accused, victims, hotspots, gangs, money trails…",
        "send": "Ask",
        "evidence": "Evidence / Reasoning (Explainable AI)",
        "sql": "SQL executed",
        "export_pdf": "Export conversation to PDF",
        "samples": "Try a sample question",
        "lang": "Language",
    },
    "kn": {
        "app_title": "ಕ್ರೈಮ್‌ಸೆನ್ಸ್ — ಸಂಭಾಷಣಾ ಅಪರಾಧ ಗುಪ್ತಚರ",
        "ask": "ಎಫ್‌ಐಆರ್, ಆರೋಪಿಗಳು, ಸಂತ್ರಸ್ತರು, ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳ ಬಗ್ಗೆ ಕೇಳಿ…",
        "send": "ಕೇಳಿ",
        "evidence": "ಸಾಕ್ಷ್ಯ / ತಾರ್ಕಿಕತೆ (ವಿವರಿಸಬಹುದಾದ AI)",
        "sql": "ನಡೆಸಿದ SQL",
        "export_pdf": "ಸಂಭಾಷಣೆಯನ್ನು PDF ಗೆ ರಫ್ತು ಮಾಡಿ",
        "samples": "ಮಾದರಿ ಪ್ರಶ್ನೆ ಪ್ರಯತ್ನಿಸಿ",
        "lang": "ಭಾಷೆ",
    },
}

# Map common Kannada crime words to the English keywords the engine understands,
# so a Kannada query still resolves (demonstrates regional-language support).
KN_TO_EN = {
    "ಕಳ್ಳತನ": "theft", "ದರೋಡೆ": "robbery", "ಕೊಲೆ": "murder", "ವಂಚನೆ": "cheating",
    "ಸೈಬರ್": "cyber", "ಬೆಂಗಳೂರು": "bengaluru", "ಮೈಸೂರು": "mysuru", "ಗ್ಯಾಂಗ್": "gang",
    "ಪ್ರವೃತ್ತಿ": "trend", "ಹಾಟ್‌ಸ್ಪಾಟ್": "hotspot",
}


def normalize_query(q: str) -> str:
    for kn, en in KN_TO_EN.items():
        if kn in q:
            q = q + " " + en
    return q
