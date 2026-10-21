"""Search and query processing module.

Components:
- Fuzzy matching via Levenshtein-distance dynamic programming.
- QueryProcessor combining Bloom Filter fast-rejection with Levenshtein typo correction.
"""

try:
    from backend.app.search.fuzzy import (
        levenshtein_distance,
        levenshtein_distance_1d,
        find_closest_match,
        find_closest_matches,
    )
    from backend.app.search.query_processor import QueryProcessor
except ModuleNotFoundError:
    from app.search.fuzzy import (
        levenshtein_distance,
        levenshtein_distance_1d,
        find_closest_match,
        find_closest_matches,
    )
    from app.search.query_processor import QueryProcessor

__all__ = [
    "levenshtein_distance",
    "levenshtein_distance_1d",
    "find_closest_match",
    "find_closest_matches",
    "QueryProcessor",
]

