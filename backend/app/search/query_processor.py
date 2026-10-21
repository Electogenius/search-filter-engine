"""Query processing and typo correction pipeline.

Combines probabilistic Bloom Filter membership testing (O(k) fast-rejection with 0% false negatives)
with Levenshtein Dynamic Programming fuzzy matching to detect and correct misspelled search tokens.
"""

import re
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union

try:
    from backend.app.data_structures.bloom_filter import BloomFilter
    from backend.app.search.fuzzy import find_closest_match
    from backend.app.indexing.tokenizer import Tokenizer
except ModuleNotFoundError:
    from app.data_structures.bloom_filter import BloomFilter
    from app.search.fuzzy import find_closest_match
    from app.indexing.tokenizer import Tokenizer

# Regex matching alphanumeric words/tokens in search strings
TOKEN_SPLIT_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class QueryProcessor:
    """Pre-processes search queries, detecting and correcting typos via Bloom Filter and Levenshtein DP.

    Attributes:
        bloom_filter (BloomFilter): Fast probabilistic filter populated with all vocabulary terms.
        vocabulary (Union[Iterable[str], Dict[str, int]]): Indexed dictionary words or word frequencies.
        tokenizer (Tokenizer): Tokenizer for normalization and stop word filtering.
        max_edit_distance (int): Maximum edit distance threshold k <= 2 for fuzzy matching.
    """

    def __init__(
        self,
        bloom_filter: BloomFilter,
        vocabulary: Union[Iterable[str], Dict[str, int]],
        tokenizer: Optional[Tokenizer] = None,
        max_edit_distance: int = 2
    ):
        self.bloom_filter: BloomFilter = bloom_filter
        self.vocabulary: Union[Iterable[str], Dict[str, int]] = vocabulary
        self.tokenizer: Tokenizer = tokenizer or Tokenizer()
        self.max_edit_distance: int = max_edit_distance

    def set_vocabulary(self, vocabulary: Union[Iterable[str], Dict[str, int]]) -> None:
        """Update the candidate vocabulary."""
        self.vocabulary = vocabulary

    def correct_token(self, token: str) -> Tuple[str, bool]:
        """Check a single token against Bloom filter and run fuzzy matching if absent.

        Returns:
            Tuple of (replacement_token, was_corrected).
        """
        if not token:
            return token, False

        token_norm = token.strip().lower()

        # Stop words are common non-indexed words (e.g. "for", "with", "and");
        # they should not be flagged as spelling errors.
        if token_norm in self.tokenizer.stop_words:
            return token_norm, False

        # Fast rejection step via Bloom filter:
        # If contains(token) is True: token is probably in vocabulary, accept as-is.
        # If contains(token) is False: 0% false negatives guarantee token is ABSENT.
        if self.bloom_filter.contains(token_norm):
            return token_norm, False

        # Token is guaranteed not in the vocabulary: run Levenshtein dynamic programming
        match = find_closest_match(
            token_norm,
            self.vocabulary,
            max_distance=self.max_edit_distance
        )

        if match and match.lower() != token_norm:
            return match.lower(), True

        # No suitable vocabulary candidate within threshold k <= 2
        return token_norm, False

    def process_query(self, query: str) -> Dict[str, Any]:
        """Process a search query string, verifying tokens and correcting typos.

        Pipeline:
        1. Extract tokens from raw query string.
        2. For each token, check Bloom Filter:
           - If contains(token) is False (guaranteed not in vocabulary):
             Run Levenshtein matching to find closest vocabulary term within k <= 2.
           - If contains(token) is True:
             Token is accepted without expensive DP lookup.
        3. If any token was corrected, build 'corrected_query'.

        Args:
            query: The raw query string typed by user (e.g., "wireles keybrd").

        Returns:
            Dict containing:
                original_query: The untouched input string.
                corrected_query: The corrected string if typos were fixed, else None.
                effective_query: The query to execute against inverted index.
                corrected: Boolean flag indicating if any typo was corrected.
                corrections: Mapping from original token to corrected token.
        """
        if not query or not query.strip():
            return {
                "original_query": query,
                "corrected_query": None,
                "effective_query": query,
                "corrected": False,
                "corrections": {}
            }

        raw_query = query.strip()
        tokens = TOKEN_SPLIT_PATTERN.findall(raw_query)

        if not tokens:
            return {
                "original_query": query,
                "corrected_query": None,
                "effective_query": query,
                "corrected": False,
                "corrections": {}
            }

        corrected_tokens: List[str] = []
        corrections: Dict[str, str] = {}
        has_typo = False

        for tok in tokens:
            corrected_tok, was_fixed = self.correct_token(tok)
            corrected_tokens.append(corrected_tok)

            if was_fixed:
                corrections[tok] = corrected_tok
                has_typo = True

        if has_typo:
            corrected_query_str = " ".join(corrected_tokens)
            return {
                "original_query": raw_query,
                "corrected_query": corrected_query_str,
                "effective_query": corrected_query_str,
                "corrected": True,
                "corrections": corrections
            }

        return {
            "original_query": raw_query,
            "corrected_query": None,
            "effective_query": raw_query,
            "corrected": False,
            "corrections": {}
        }

