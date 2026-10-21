"""Okapi BM25 Ranking Algorithm.

Implements the standard Okapi BM25 probabilistic retrieval function with:
- Robertson-Spärck Jones non-negative IDF:
    IDF(q_i) = ln(1 + (N - n(q_i) + 0.5) / (n(q_i) + 0.5))
- Document length normalization with parameters k1 = 1.5, b = 0.75:
    Score(D, Q) = sum_{i=1..n} [ IDF(q_i) * (f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * (|D| / avgdl))) ]
"""

import math
from typing import Any, Dict, List, Optional, Set, Tuple

try:
    from backend.app.indexing.tokenizer import Tokenizer
except ModuleNotFoundError:
    from app.indexing.tokenizer import Tokenizer


class BM25Scorer:
    """Computes Okapi BM25 relevance scores for documents in the catalogue."""

    def __init__(
        self,
        corpus: Dict[str, Dict[str, Any]],
        tokenizer: Optional[Tokenizer] = None,
        k1: float = 1.5,
        b: float = 0.75,
        title_weight: int = 3,
        desc_weight: int = 1,
    ):
        self.k1: float = k1
        self.b: float = b
        self.tokenizer: Tokenizer = tokenizer or Tokenizer()
        self.title_weight: int = title_weight
        self.desc_weight: int = desc_weight

        self.N: int = len(corpus)
        self.doc_lengths: Dict[str, int] = {}
        self.postings: Dict[str, List[Tuple[str, int]]] = {}
        self.doc_term_freqs: Dict[str, Dict[str, int]] = {}
        self.doc_frequencies: Dict[str, int] = {}
        self.idf_cache: Dict[str, float] = {}

        self._index_corpus(corpus)
        self.avgdl: float = (
            sum(self.doc_lengths.values()) / self.N if self.N > 0 else 1.0
        )

    def _index_corpus(self, corpus: Dict[str, Dict[str, Any]]) -> None:
        """Extract term frequencies and document lengths across all documents."""
        raw_postings: Dict[str, Dict[str, int]] = {}

        for doc_id, doc in corpus.items():
            title = doc.get("title", "")
            desc = doc.get("description", "")

            title_tf = self.tokenizer.get_term_frequencies(title)
            desc_tf = self.tokenizer.get_term_frequencies(desc)

            combined_tf: Dict[str, int] = {}
            for term, count in title_tf.items():
                combined_tf[term] = combined_tf.get(term, 0) + (count * self.title_weight)
            for term, count in desc_tf.items():
                combined_tf[term] = combined_tf.get(term, 0) + (count * self.desc_weight)

            self.doc_term_freqs[doc_id] = combined_tf
            self.doc_lengths[doc_id] = sum(combined_tf.values())

            for term, freq in combined_tf.items():
                if term not in raw_postings:
                    raw_postings[term] = {}
                raw_postings[term][doc_id] = freq

        # Sort posting lists by doc_id for efficient WAND cursor traversal
        for term, doc_map in raw_postings.items():
            self.postings[term] = sorted(doc_map.items(), key=lambda x: x[0])
            self.doc_frequencies[term] = len(doc_map)

    def idf(self, term: str) -> float:
        """Compute the Robertson-Spärck Jones non-negative IDF for a term."""
        if term in self.idf_cache:
            return self.idf_cache[term]

        n_q = self.doc_frequencies.get(term, 0)
        if n_q == 0 or self.N == 0:
            val = 0.0
        else:
            # Strictly non-negative RSJ formula: ln(1 + (N - n_q + 0.5) / (n_q + 0.5))
            numerator = self.N - n_q + 0.5
            denominator = n_q + 0.5
            val = math.log(1.0 + (numerator / denominator))

        self.idf_cache[term] = val
        return val

    def term_score(self, term: str, tf: int, doc_id: str) -> float:
        """Calculate the BM25 contribution of a single term to a document."""
        if tf <= 0:
            return 0.0

        term_idf = self.idf(term)
        doc_len = self.doc_lengths.get(doc_id, self.avgdl)
        len_norm = 1.0 - self.b + (self.b * (doc_len / self.avgdl)) if self.avgdl > 0 else 1.0
        tf_component = (tf * (self.k1 + 1.0)) / (tf + (self.k1 * len_norm))
        return term_idf * tf_component

    def score_document(self, doc_id: str, query_tokens: List[str]) -> float:
        """Calculate the full BM25 score for a document against a query."""
        doc_tf = self.doc_term_freqs.get(doc_id)
        if not doc_tf:
            return 0.0

        total_score = 0.0
        for token in query_tokens:
            tf = doc_tf.get(token, 0)
            if tf > 0:
                total_score += self.term_score(token, tf, doc_id)
        return total_score

    def score_all_candidates(self, query_tokens: List[str]) -> Dict[str, float]:
        """Exhaustively compute BM25 scores for all matching documents (ground truth baseline)."""
        candidates: Set[str] = set()
        for token in query_tokens:
            for doc_id, _ in self.postings.get(token, []):
                candidates.add(doc_id)

        scores: Dict[str, float] = {}
        for doc_id in candidates:
            score = self.score_document(doc_id, query_tokens)
            if score > 0:
                scores[doc_id] = round(score, 4)
        return scores
