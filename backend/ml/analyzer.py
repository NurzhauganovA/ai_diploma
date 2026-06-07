"""
Core ML analyzer for FakeGuard.
Uses lightweight models for sentiment + fake detection.
Heavy transformers are loaded lazily and cached.
"""
import re
import logging
from typing import Optional

logger = logging.getLogger(__name__)

# Lazy model cache
_sentiment_pipeline = None
_fake_pipeline = None


def _load_sentiment_model():
    global _sentiment_pipeline
    if _sentiment_pipeline is None:
        try:
            from transformers import pipeline
            _sentiment_pipeline = pipeline(
                "text-classification",
                model="blanchefort/rubert-base-cased-sentiment",
                device=-1,  # CPU
                truncation=True,
                max_length=512,
            )
            logger.info("Sentiment model loaded: rubert-base-cased-sentiment")
        except Exception as e:
            logger.warning(f"Could not load transformer sentiment model: {e}. Using keyword fallback.")
            _sentiment_pipeline = "keywords"
    return _sentiment_pipeline


def _load_fake_model():
    global _fake_pipeline
    if _fake_pipeline is None:
        try:
            from transformers import pipeline
            _fake_pipeline = pipeline(
                "text-classification",
                model="WpythonW/fake-news-detection-roberta",
                device=-1,
                truncation=True,
                max_length=512,
            )
            logger.info("Fake detection model loaded")
        except Exception as e:
            logger.warning(f"Could not load fake detection model: {e}. Using keyword-based fallback.")
            _fake_pipeline = "keywords"
    return _fake_pipeline


def analyze_sentiment(text: str) -> dict:
    """Returns sentiment label and score."""
    if not text or len(text.strip()) < 10:
        return {"sentiment": "neutral", "score": 0.5}

    model = _load_sentiment_model()
    if model == "keywords":
        return _sentiment_textblob(text)

    try:
        text_truncated = text[:512]
        result = model(text_truncated)[0]
        label = result["label"].lower()

        label_map = {
            "positive": "positive",
            "neutral": "neutral",
            "negative": "negative",
            "pos": "positive",
            "neg": "negative",
            "neu": "neutral",
            "label_0": "negative",
            "label_1": "neutral",
            "label_2": "positive",
        }
        sentiment = label_map.get(label, "neutral")
        score = result["score"]
        if sentiment == "negative":
            score = -score
        elif sentiment == "positive":
            score = score
        else:
            score = 0.0

        return {"sentiment": sentiment, "score": score}
    except Exception as e:
        logger.error(f"Sentiment analysis error: {e}")
        return _sentiment_textblob(text)


def _sentiment_textblob(text: str) -> dict:
    """Fallback: keyword-based sentiment for Russian text."""
    positive_words = [
        "хорошо", "отлично", "превосходно", "успех", "рост", "прибыль",
        "позитив", "достижение", "победа", "выгода", "развитие", "улучшение",
        "инновация", "лидер", "качество", "надёжность", "доверие", "партнёрство",
        "good", "great", "excellent", "success", "profit", "growth",
    ]
    negative_words = [
        "плохо", "убыток", "скандал", "мошенничество", "обман", "фейк", "ложь",
        "кризис", "банкротство", "штраф", "арест", "коррупция", "нарушение",
        "провал", "катастрофа", "угроза", "опасность", "проблема", "конфликт",
        "fake", "fraud", "scandal", "bankruptcy", "crisis", "failure",
    ]
    text_lower = text.lower()
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)

    if neg > pos:
        score = min(-0.3 - neg * 0.05, -0.9)
        return {"sentiment": "negative", "score": score}
    elif pos > neg:
        score = min(0.3 + pos * 0.05, 0.9)
        return {"sentiment": "positive", "score": score}
    return {"sentiment": "neutral", "score": 0.0}


def analyze_fake(text: str, source_credibility: float = 0.7) -> dict:
    """
    Returns fake_score (0=real, 1=fake) and explanation keywords.
    """
    if not text or len(text.strip()) < 10:
        return {"fake_score": 0.3, "explanation": []}

    # Keyword-based signals
    fake_signals = _get_fake_signals(text)

    model = _load_fake_model()
    if model != "keywords":
        try:
            text_truncated = (text[:500]).strip()
            result = model(text_truncated)[0]
            label = result["label"].lower()
            confidence = result["score"]

            is_fake = "fake" in label or label in ["label_1", "false", "0"]
            base_score = confidence if is_fake else (1 - confidence)
        except Exception as e:
            logger.error(f"Fake detection error: {e}")
            base_score = _keyword_fake_score(text, fake_signals)
    else:
        base_score = _keyword_fake_score(text, fake_signals)

    # Adjust by source credibility
    credibility_penalty = (1 - source_credibility) * 0.3
    final_score = min(1.0, base_score + credibility_penalty)

    return {
        "fake_score": round(final_score, 3),
        "explanation": fake_signals[:5],
    }


def _get_fake_signals(text: str) -> list:
    """Detect fake news signal words."""
    signals = {
        "срочно": 0.2,
        "exclusive": 0.1,
        "шок": 0.25,
        "сенсация": 0.2,
        "скрывают": 0.3,
        "правда которую": 0.35,
        "никто не знает": 0.3,
        "официально скрывают": 0.4,
        "по слухам": 0.2,
        "источники утверждают": 0.15,
        "якобы": 0.15,
        "говорят что": 0.1,
        "будто бы": 0.15,
        "стало известно": 0.1,
        "breaking": 0.1,
        "shocking": 0.2,
        "secret": 0.15,
        "they don't want": 0.3,
    }
    text_lower = text.lower()
    found = [kw for kw in signals if kw in text_lower]
    return found


def _keyword_fake_score(text: str, signals: list) -> float:
    """Simple heuristic fake score."""
    base = 0.2
    signal_boost = len(signals) * 0.1
    # Check for exclamation marks (clickbait)
    exclamation_count = text.count("!")
    caps_ratio = sum(1 for c in text if c.isupper()) / max(len(text), 1)
    caps_boost = min(caps_ratio * 0.5, 0.2)
    return min(1.0, base + signal_boost + caps_boost + min(exclamation_count * 0.05, 0.2))


def analyze_toxicity(text: str) -> float:
    """
    Returns toxicity score 0-1.
    Uses keyword heuristics (can be replaced with Perspective API).
    """
    toxic_patterns = [
        r"\bидиот\b", r"\bдебил\b", r"\bкретин\b", r"\bмошенник\b",
        r"\bворов\b", r"\bпреступник\b", r"\bублюдок\b", r"\bнегодяй\b",
        r"\bidiot\b", r"\bstupid\b", r"\bscammer\b", r"\bfraud\b",
        r"\bterrorist\b",
    ]
    text_lower = text.lower()
    matches = sum(1 for p in toxic_patterns if re.search(p, text_lower))
    return min(1.0, matches * 0.2)


def extract_entities(text: str, keywords: list = None) -> list:
    """
    Simple entity extraction using keyword matching.
    Returns list of found entities.
    """
    entities = []
    if keywords:
        text_lower = text.lower()
        for kw in keywords:
            if kw.lower() in text_lower:
                entities.append({"text": kw, "label": "ORG"})

    # Find capitalized multi-word sequences (potential org/person names)
    pattern = r"\b([А-ЯA-Z][а-яa-z]{2,}\s+[А-ЯA-Z][а-яa-z]{2,})\b"
    found = re.findall(pattern, text)
    for name in found[:5]:
        if not any(e["text"] == name for e in entities):
            entities.append({"text": name, "label": "PERSON"})

    return entities


def get_topic(title: str, content: str) -> str:
    """Classify article topic based on keywords."""
    text = (title + " " + content[:500]).lower()

    topic_map = {
        "финансы": ["акции", "биржа", "инвестиции", "прибыль", "убыток", "финансы", "деньги", "банк", "кредит"],
        "скандал": ["скандал", "обвинение", "иск", "суд", "расследование", "коррупция", "мошенничество"],
        "продукт": ["продукт", "сервис", "услуга", "релиз", "запуск", "обновление", "версия", "feature"],
        "персонал": ["сотрудник", "увольнение", "найм", "руководитель", "директор", "ceo", "команда"],
        "партнёрство": ["партнёр", "сотрудничество", "договор", "сделка", "слияние", "поглощение"],
        "технологии": ["ai", "ии", "технология", "разработка", "инновация", "патент", "алгоритм"],
        "ESG": ["экология", "устойчивый", "esg", "климат", "окружающая среда", "зелёный"],
        "общее": [],
    }

    scores = {topic: 0 for topic in topic_map}
    for topic, kws in topic_map.items():
        for kw in kws:
            if kw in text:
                scores[topic] += 1

    best = max(scores, key=lambda t: scores[t])
    return best if scores[best] > 0 else "общее"


def calculate_urgency(fake_score: float, sentiment_score: float, toxicity: float, source_credibility: float) -> str:
    """Calculate urgency level from ML scores."""
    threat = (
        (fake_score or 0) * 0.5 +
        abs(sentiment_score or 0) * 0.2 +
        (toxicity or 0) * 0.2 +
        (1 - source_credibility) * 0.1
    )

    if threat >= 0.7:
        return "critical"
    elif threat >= 0.5:
        return "high"
    elif threat >= 0.3:
        return "medium"
    return "low"


def extract_keywords(text: str, top_n: int = 10) -> list:
    """Extract top keywords by TF-IDF-like frequency."""
    stop_words = {
        "и", "в", "на", "с", "что", "это", "как", "по", "от", "к", "из",
        "не", "но", "а", "или", "то", "же", "уже", "еще", "ещё", "для",
        "о", "об", "за", "при", "без", "до", "под", "над", "между",
        "the", "a", "an", "in", "of", "to", "and", "or", "is", "are",
    }
    words = re.findall(r"\b[а-яёa-z]{4,}\b", text.lower())
    freq = {}
    for w in words:
        if w not in stop_words:
            freq[w] = freq.get(w, 0) + 1
    sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
    return [w for w, _ in sorted_words[:top_n]]


def full_analyze(text: str, title: str = "", source_credibility: float = 0.7, company_keywords: list = None) -> dict:
    """
    Full analysis pipeline.
    Returns all ML metrics for an article.
    """
    full_text = (title + " " + text).strip()

    sentiment_result = analyze_sentiment(full_text)
    fake_result = analyze_fake(full_text, source_credibility)
    toxicity = analyze_toxicity(full_text)
    topic = get_topic(title, text)
    entities = extract_entities(full_text, company_keywords)
    keywords = extract_keywords(full_text)
    urgency = calculate_urgency(
        fake_result["fake_score"],
        sentiment_result["score"],
        toxicity,
        source_credibility,
    )

    # Build simple SHAP-like explanation
    shap_data = {
        "top_signals": fake_result.get("explanation", []),
        "sentiment_drivers": [],
        "fake_score_components": {
            "keyword_signals": round(len(fake_result.get("explanation", [])) * 0.1, 2),
            "source_credibility_penalty": round((1 - source_credibility) * 0.3, 2),
        },
    }

    return {
        "fake_score": fake_result["fake_score"],
        "sentiment": sentiment_result["sentiment"],
        "sentiment_score": sentiment_result["score"],
        "toxicity_score": round(toxicity, 3),
        "urgency": urgency,
        "topic": topic,
        "entities": entities,
        "keywords": keywords,
        "shap_data": shap_data,
    }
