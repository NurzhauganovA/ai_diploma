"""
Gemini AI analyzer for FakeGuard.

Использует Google Gemini 1.5 Flash — самая дешёвая быстрая модель.
Один запрос = полный анализ статьи (fake + sentiment + токсичность + тема + ключевые слова).

Экономия токенов:
  - Текст обрезается до 600 символов
  - Ответ ограничен 400 токенами
  - Температура 0.1 (детерминированный результат)
  - Результат кэшируется в shap_data["gemini"]
"""
import re
import json
import logging
from typing import Optional

logger = logging.getLogger(__name__)

_gemini_model = None


def _get_model():
    global _gemini_model
    if _gemini_model is not None:
        return _gemini_model
    try:
        import google.generativeai as genai
        from django.conf import settings

        api_key = getattr(settings, "GEMINI_API_KEY", "")
        if not api_key:
            return None

        genai.configure(api_key=api_key)
        _gemini_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash",
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 450,
                "response_mime_type": "application/json",
            },
        )
        logger.info("Gemini 1.5 Flash model initialized")
        return _gemini_model
    except Exception as e:
        logger.warning(f"Gemini init failed: {e}")
        return None


ANALYSIS_PROMPT = """Analyze this news article and return a JSON object.

Title: {title}
Text: {text}
Source credibility (0-1): {credibility}

Return ONLY this JSON structure (no markdown, no explanation):
{{
  "fake_score": <float 0.0-1.0, probability of misinformation>,
  "sentiment": <"positive" | "neutral" | "negative">,
  "sentiment_score": <float -1.0 to 1.0>,
  "toxicity_score": <float 0.0-1.0>,
  "urgency": <"low" | "medium" | "high" | "critical">,
  "topic": <string, category in Russian: технологии/финансы/политика/общество/спорт/наука/бизнес/другое>,
  "keywords": [<3-5 key terms in article language>],
  "summary": <string, 1-2 sentences in Russian summarizing the article>,
  "explanation": <string, brief reason for fake_score in Russian, max 50 words>
}}"""


def analyze_with_gemini(
    title: str,
    content: str,
    source_credibility: float = 0.7,
) -> Optional[dict]:
    """
    Analyze article using Gemini 1.5 Flash.
    Returns structured dict or None if Gemini not available/failed.
    """
    model = _get_model()
    if model is None:
        return None

    try:
        # Truncate to save tokens: title 200 chars + text 600 chars
        title_short = (title or "")[:200]
        text_short = (content or title or "")[:600]

        prompt = ANALYSIS_PROMPT.format(
            title=title_short,
            text=text_short,
            credibility=round(source_credibility, 2),
        )

        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Extract JSON if wrapped in markdown code blocks
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if json_match:
            raw = json_match.group()

        data = json.loads(raw)

        # Validate and clamp numeric values
        result = {
            "fake_score": _clamp(data.get("fake_score", 0.3)),
            "sentiment": data.get("sentiment", "neutral"),
            "sentiment_score": _clamp(data.get("sentiment_score", 0.0), -1, 1),
            "toxicity_score": _clamp(data.get("toxicity_score", 0.1)),
            "urgency": data.get("urgency", "low"),
            "topic": str(data.get("topic", ""))[:100],
            "keywords": data.get("keywords", [])[:10],
            "summary": str(data.get("summary", ""))[:500],
            "explanation": str(data.get("explanation", ""))[:300],
            "ai_analyzed": True,
        }

        # Normalize sentiment
        if result["sentiment"] not in ("positive", "neutral", "negative"):
            result["sentiment"] = "neutral"

        # Normalize urgency
        if result["urgency"] not in ("low", "medium", "high", "critical"):
            result["urgency"] = "low"

        logger.info(f"Gemini analyzed: fake={result['fake_score']:.2f} sentiment={result['sentiment']}")
        return result

    except Exception as e:
        logger.error(f"Gemini analysis failed: {e}")
        # Reset model cache on error so it can retry
        global _gemini_model
        _gemini_model = None
        return None


def is_gemini_available() -> bool:
    """Check if Gemini API key is configured."""
    try:
        from django.conf import settings
        return bool(getattr(settings, "GEMINI_API_KEY", ""))
    except Exception:
        return False


def _clamp(value, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        return max(lo, min(hi, float(value)))
    except (TypeError, ValueError):
        return lo
