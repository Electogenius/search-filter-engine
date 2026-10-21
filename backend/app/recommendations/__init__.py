"""Recommendations module.

Implementations:
- CooccurrenceRecommender: In-memory market basket co-occurrence recommender.
"""

try:
    from backend.app.recommendations.cooccurrence import CooccurrenceRecommender
except ModuleNotFoundError:
    from app.recommendations.cooccurrence import CooccurrenceRecommender

__all__ = ["CooccurrenceRecommender"]

