import os
import re

MOCK_LLM = int(os.getenv("MOCK_LLM", "1"))


def _mock_extract_signals(snippet: str) -> dict:
    text = snippet.lower()

    risk_flags = []

    # Risk signals
    if re.search(r"\blitigation\b", text):
        risk_flags.append("litigation")

    if re.search(r"\bregulatory\b", text):
        risk_flags.append("regulatory")

    if re.search(
        r"customer concentration|concentration of customers|dependence on key customers",
        text,
    ):
        risk_flags.append("customer_concentration")

    # Hedging phrases
    hedging_detected = bool(
        re.search(
            r"\bassuming\b|\bcautiously\b|\bvisibility\b",
            text,
        )
    )

    # Sentiment
    if re.search(r"\bconfident\b|\bapproved\b", text):
        sentiment = "confident"
    elif hedging_detected:
        sentiment = "cautious"
    else:
        sentiment = "neutral"

    return {
        "risk_flags": risk_flags,
        "hedging_detected": hedging_detected,
        "sentiment": sentiment,
    }


def _validate_result(result: dict) -> bool:
    if not isinstance(result, dict):
        return False

    required_keys = {
        "risk_flags",
        "hedging_detected",
        "sentiment",
    }

    if set(result.keys()) != required_keys:
        return False

    if not isinstance(result["risk_flags"], list):
        return False

    if not isinstance(result["hedging_detected"], bool):
        return False

    if result["sentiment"] not in {
        "confident",
        "cautious",
        "neutral",
    }:
        return False

    return True


def extract_signals(snippet: str) -> dict:
    """
    Returns:
    {
        "risk_flags": [...],
        "hedging_detected": bool,
        "sentiment": "confident"|"cautious"|"neutral"
    }
    """

    if MOCK_LLM == 1:
        return _mock_extract_signals(snippet)

    # Optional LLM extension
    for _ in range(2):  # initial attempt + one retry
        try:
            result = call_llm_for_json(snippet)

            if _validate_result(result):
                return result
        except Exception:
            pass

    # Fallback to deterministic graded baseline
    return _mock_extract_signals(snippet)

DISCLOSURE_SNIPPETS = [
    snippet1,
    snippet2,
    snippet3,
    snippet4,
    snippet5,
    snippet6,
]

for i, snippet in enumerate(DISCLOSURE_SNIPPETS, start=1):
    result = extract_signals(snippet)

    print(f"\nSnippet {i}")
    print(result)
