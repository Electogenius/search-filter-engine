"""Text tokenization and normalization module.

Splits input text into normalized alphanumeric tokens, removes common English stop words,
and computes per-document term frequencies.
"""

import re
from typing import Dict, List, Set

# Standard English stop words to filter out non-informative noise
DEFAULT_STOP_WORDS: Set[str] = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "did",
    "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him",
    "himself", "his", "how", "i", "if", "in", "into", "is", "it", "its", "itself",
    "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out",
    "over", "own", "same", "she", "should", "so", "some", "such", "than", "that",
    "the", "their", "theirs", "them", "themselves", "then", "there", "these",
    "they", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "we", "were", "what", "when", "where", "which", "while", "who",
    "whom", "why", "with", "would", "you", "your", "yours", "yourself", "yourselves"
}

# Regex to extract alphanumeric word tokens
TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")


class Tokenizer:
    """Configurable text tokenizer and normalizer."""

    def __init__(self, stop_words: Set[str] = DEFAULT_STOP_WORDS, min_length: int = 2):
        self.stop_words: Set[str] = stop_words
        self.min_length: int = min_length

    def tokenize(self, text: str) -> List[str]:
        """Convert text into normalized, filtered tokens."""
        if not text:
            return []

        raw_tokens = TOKEN_PATTERN.findall(text.lower())
        tokens = [
            token for token in raw_tokens
            if len(token) >= self.min_length and token not in self.stop_words
        ]
        return tokens

    def get_term_frequencies(self, text: str) -> Dict[str, int]:
        """Tokenize text and count term occurrences (tf)."""
        frequencies: Dict[str, int] = {}
        for token in self.tokenize(text):
            frequencies[token] = frequencies.get(token, 0) + 1
        return frequencies

