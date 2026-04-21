import time
from dataclasses import dataclass, field
from typing import Optional, List, Dict


# Calificación por factores

@dataclass
class ScoringWeights:
    sentiment:  float = 0.30
    topic:      float = 0.30
    recency:    float = 0.20
    unread:     float = 0.10
    confidence: float = 0.10

    def validate(self):
        total = self.sentiment + self.topic + self.recency + self.unread + self.confidence
        if not (0.99 < total < 1.01):
            raise ValueError(f"Los pesos deben sumar 1.0, se ha obtenido {total:.4f}")


# Puntuación basada en el LLM

SENTIMENT_SCORES = {
    "negative": 1.0,
    "neutral":  0.4,
    "positive": 0.1,
}

TOPIC_SCORES = {
    "complaint":       1.00,
    "bug_report":      0.95,
    "billing":         0.80,
    "follow_up":       0.65,
    "sales_inquiry":   0.55,
    "feature_request": 0.35,
    "partnership":     0.30,
    "other":           0.20,
}

RECENCY_DECAY_HOURS = 168  # 7 días

# Puntuación basada en el tiempo del email

def _recency_score(timestamp_ms: int) -> float:
    now_ms  = time.time() * 1000
    age_h   = (now_ms - timestamp_ms) / 3_600_000
    score   = max(0.0, 1.0 - age_h / RECENCY_DECAY_HOURS)
    return round(score, 4)


# Función principal de puntuaciones

def score_email(email: dict, weights: Optional[ScoringWeights] = None) -> dict:
    if weights is None:
        weights = ScoringWeights()
    weights.validate()

    analysis   = email.get("analysis", {})
    sentiment  = analysis.get("sentiment", "neutral")
    topic      = analysis.get("topic", "other")
    confidence = float(analysis.get("confidence", 0.5))
    timestamp  = email.get("timestamp", 0)
    labels     = email.get("labels", [])

    s_sentiment  = SENTIMENT_SCORES.get(sentiment, 0.4)
    s_topic      = TOPIC_SCORES.get(topic, 0.2)
    s_recency    = _recency_score(timestamp)
    s_unread     = 1.0 if "UNREAD" in labels else 0.0
    s_confidence = confidence

    raw_score = (
        weights.sentiment  * s_sentiment  +
        weights.topic      * s_topic      +
        weights.recency    * s_recency    +
        weights.unread     * s_unread     +
        weights.confidence * s_confidence
    )

    urgency = round(min(max(raw_score * 100, 0), 100), 2)

    result = dict(email)
    result["urgency_score"] = urgency
    result["score_breakdown"] = {
        "sentiment_score":  round(s_sentiment  * weights.sentiment  * 100, 2),
        "topic_score":      round(s_topic      * weights.topic      * 100, 2),
        "recency_score":    round(s_recency    * weights.recency    * 100, 2),
        "unread_score":     round(s_unread     * weights.unread     * 100, 2),
        "confidence_score": round(s_confidence * weights.confidence * 100, 2),
    }
    return result


def score_emails(emails: List[dict], weights: Optional[ScoringWeights] = None) -> List[dict]:
    scored = [score_email(e, weights) for e in emails]
    scored.sort(key=lambda e: e["urgency_score"], reverse=True)
    return scored
