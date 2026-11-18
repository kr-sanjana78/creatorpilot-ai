'''backend/services/gemini.py

Service module that provides audience analysis using Gemini (google‑genai).
It follows the contract defined in ``backend.schemas.audience`` and falls back to a
simple heuristic when the Gemini API key is missing or the remote call fails.
'''

import json
import logging
import re
from collections import Counter
from typing import List, Dict, Any

from backend.schemas.audience import AnalysisInsights
from backend.config import settings

# ---------------------------------------------------------------------------
# Logging configuration (project should configure handlers elsewhere)
# ---------------------------------------------------------------------------
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic fallback implementation
# ---------------------------------------------------------------------------

POSITIVE_WORDS = {
    "good",
    "great",
    "awesome",
    "fantastic",
    "excellent",
    "love",
    "like",
    "amazing",
    "perfect",
    "nice",
}

NEGATIVE_WORDS = {
    "bad",
    "terrible",
    "hate",
    "poor",
    "awful",
    "disappoint",
    "worst",
    "boring",
    "slow",
    "confusing",
}


def _heuristic_analyze(comments: List[str]) -> Dict[str, Any]:
    """Return a minimal analysis when Gemini cannot be used.

    The function computes very simple sentiment percentages, picks the most
    frequent non‑stop words as *top themes*, and returns placeholder FAQs and
    content ideas. The output matches the ``AnalysisInsights`` schema.
    """
    total = max(len(comments), 1)
    pos, neg, neu = 0, 0, 0
    for c in comments:
        lowered = c.lower()
        has_pos = any(w in lowered for w in POSITIVE_WORDS)
        has_neg = any(w in lowered for w in NEGATIVE_WORDS)
        if has_pos and not has_neg:
            pos += 1
        elif has_neg and not has_pos:
            neg += 1
        else:
            neu += 1
    positive_pct = round(pos / total * 100, 2)
    negative_pct = round(neg / total * 100, 2)
    neutral_pct = round(neu / total * 100, 2)
    if positive_pct > negative_pct and positive_pct > neutral_pct:
        overall = "positive"
    elif negative_pct > positive_pct and negative_pct > neutral_pct:
        overall = "negative"
    else:
        overall = "neutral"
    # extract words longer than 3 characters
    words = [w for comment in comments for w in comment.lower().split() if len(w) > 3]
    top_themes = [w for w, _ in Counter(words).most_common(5)]
    faqs = [
        "What are the main concerns of the audience?",
        "Which features do viewers request most often?",
    ]
    ideas = [
        "Create a tutorial addressing the most‑asked question.",
        "Produce a follow‑up video that highlights the positive feedback.",
    ]
    return {
        "sentiment_summary": {
            "positive_pct": positive_pct,
            "neutral_pct": neutral_pct,
            "negative_pct": negative_pct,
            "overall_sentiment": overall,
        },
        "top_themes": top_themes,
        "frequently_asked_questions": faqs,
        "content_ideas": ideas,
    }

# ---------------------------------------------------------------------------
# Gemini integration (google‑genai SDK)
# ---------------------------------------------------------------------------

from google import genai  # type: ignore


def _is_placeholder_key(key: str) -> bool:
    """Detect the default placeholder used in the *.env* file.

    The project ships with a placeholder value; when that is present we skip the
    remote call entirely.
    """
    placeholder_variants = {"", "your_gemini_api_key_here", "YOUR_GEMINI_API_KEY", None}
    return (key or "").strip() in placeholder_variants


async def analyze_comments(comments: List[str]) -> Dict[str, Any]:
    """Analyse a list of audience comments.

    The function first tries to call Gemini. On any failure (missing key, API
    error, malformed response) it falls back to the heuristic implementation.
    The returned dictionary conforms to the ``AnalysisInsights`` schema and
    always includes an ``analyzed_by`` field indicating the source.
    """
    if not comments:
        raise ValueError("At least one comment must be provided for analysis.")

    # Shortcut when the API key is a placeholder.
    if _is_placeholder_key(getattr(settings, "GEMINI_API_KEY", "")):
        fallback = _heuristic_analyze(comments)
        fallback["analyzed_by"] = "heuristic_fallback"
        insights = AnalysisInsights.model_validate(fallback)
        return insights.model_dump()

    try:
        # Initialise Gemini client using the modern SDK.
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        prompt = (
            "You are an audience‑analysis assistant. Analyse the following list of comments "
            "and output a JSON object that matches the ``AnalysisInsights`` schema defined in "
            "the project. Include sentiment percentages, overall sentiment, up to five key "
            "themes, up to five frequently asked questions, and up to five content ideas. "
            "Do NOT add any extra fields.\nComments: "
            f"{json.dumps(comments)}"
        )
        # The SDK supports specifying the response MIME type to request JSON.
        try:
            from google.genai.types import GenerateContentConfig  # type: ignore
            config = GenerateContentConfig(response_mime_type="application/json")
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=config,
            )
        except Exception as e:
            # If the config class is unavailable, fall back to a plain call.
            logger.debug("GenerateContentConfig not available or failed: %s", e)
            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
            )
        raw = response.text
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Attempt to extract a fenced JSON block if Gemini wrapped it in markdown.
            match = re.search(r"```json\n(?P<json>.*?\n)```", raw, re.DOTALL)
            if match:
                data = json.loads(match.group("json"))
            else:
                logger.warning("Gemini returned non‑JSON response: %s", raw)
                raise
        # Validate the shape against the Pydantic model.
        insights = AnalysisInsights.model_validate(data)
        result = insights.model_dump()
        result["analyzed_by"] = "gemini"
        return result
    except Exception as exc:  # pragma: no cover – exercised via fallback in tests
        logger.error("Gemini analysis failed: %s", exc, exc_info=True)
        fallback = _heuristic_analyze(comments)
        fallback["analyzed_by"] = "heuristic_fallback"
        insights = AnalysisInsights.model_validate(fallback)
        return insights.model_dump()

# End of file
