"""WAND (Weak AND) Dynamic Pruning Top-K Retrieval Algorithm.

Implements the Broder et al. (2003) WAND algorithm for fast top-k document retrieval
with dynamic threshold pruning.

Key Properties:
- Pre-computes exact term upper bounds:
    U_t = max_{D in postings(t)} BM25Score(t, D)
- Maintains a min-heap of size k storing current top-k candidate scores with threshold theta = heap[0].score.
- Skips non-competitive documents whose theoretical maximum score cannot exceed theta.
- Exact match guarantee: Returns the identical top-k documents and scores as exhaustive evaluation.
"""

import bisect
import heapq
from typing import Any, Dict, List, Optional, Tuple

try:
    from backend.app.ranking.bm25 import BM25Scorer
except ModuleNotFoundError:
    from app.ranking.bm25 import BM25Scorer


class PostingCursor:
    """Cursor managing traversal over a term's sorted posting list."""

    def __init__(self, term: str, postings: List[Tuple[str, int]], upper_bound: float):
        self.term: str = term
        self.postings: List[Tuple[str, int]] = postings
        self.upper_bound: float = upper_bound
        self.cursor: int = 0
        self.length: int = len(postings)

    @property
    def is_exhausted(self) -> bool:
        return self.cursor >= self.length

    def current_doc_id(self) -> Optional[str]:
        if self.is_exhausted:
            return None
        return self.postings[self.cursor][0]

    def current_tf(self) -> int:
        if self.is_exhausted:
            return 0
        return self.postings[self.cursor][1]

    def advance(self) -> None:
        self.cursor += 1

    def seek(self, target_doc_id: str) -> None:
        """Advance cursor to first document with doc_id >= target_doc_id using binary search."""
        if self.is_exhausted:
            return

        # Extract remaining doc_ids for binary search
        # Since postings are sorted by doc_id, use bisect_left
        idx = bisect.bisect_left(
            self.postings,
            target_doc_id,
            lo=self.cursor,
            hi=self.length,
            key=lambda x: x[0],
        )
        self.cursor = idx


class WANDTopK:
    """WAND Top-K query engine backed by BM25 scoring."""

    def __init__(self, bm25_scorer: BM25Scorer):
        self.scorer: BM25Scorer = bm25_scorer
        self.term_upper_bounds: Dict[str, float] = {}
        self._compute_term_upper_bounds()

    def _compute_term_upper_bounds(self) -> None:
        """Pre-compute the exact maximum BM25 contribution for each unique term."""
        for term, posting_list in self.scorer.postings.items():
            max_score = 0.0
            for doc_id, tf in posting_list:
                score = self.scorer.term_score(term, tf, doc_id)
                if score > max_score:
                    max_score = score
            self.term_upper_bounds[term] = max_score

    def get_term_upper_bound(self, term: str) -> float:
        """Return the pre-computed maximum BM25 score possible for a term."""
        return self.term_upper_bounds.get(term, 0.0)

    def search(
        self,
        query_tokens: List[str],
        k: int = 10
    ) -> List[Tuple[str, float]]:
        """Retrieve top-k documents sorted by BM25 relevance score descending."""
        results, _ = self.search_with_metrics(query_tokens, k=k)
        return results

    def search_with_metrics(
        self,
        query_tokens: List[str],
        k: int = 10
    ) -> Tuple[List[Tuple[str, float]], Dict[str, Any]]:
        """Retrieve top-k documents with execution metrics to verify pruning."""
        if k <= 0 or not query_tokens:
            return [], {"evaluated_docs": 0, "total_candidates": 0, "pruned_docs": 0, "threshold": 0.0}

        # Deduplicate query tokens and initialize cursors for existing terms
        unique_tokens = list(set(query_tokens))
        active_cursors: List[PostingCursor] = []
        all_candidate_docs: set = set()

        for token in unique_tokens:
            postings = self.scorer.postings.get(token, [])
            if postings:
                ub = self.term_upper_bounds.get(token, 0.0)
                active_cursors.append(PostingCursor(token, postings, ub))
                for doc_id, _ in postings:
                    all_candidate_docs.add(doc_id)

        if not active_cursors:
            return [], {"evaluated_docs": 0, "total_candidates": 0, "pruned_docs": 0, "threshold": 0.0}

        # Min-heap to maintain current top-k: elements are (score, doc_id)
        heap: List[Tuple[float, str]] = []
        threshold: float = 0.0
        evaluated_docs_count: int = 0

        while True:
            # Filter out exhausted cursors
            active_cursors = [c for c in active_cursors if not c.is_exhausted]
            if not active_cursors:
                break

            # 1. Sort active cursors by current_doc_id
            active_cursors.sort(key=lambda c: c.current_doc_id() or "")

            # 2. Accumulate upper bounds until sum exceeds threshold
            accumulated_score = 0.0
            pivot_idx: Optional[int] = None

            for i, cursor in enumerate(active_cursors):
                accumulated_score += cursor.upper_bound
                if accumulated_score > threshold:
                    pivot_idx = i
                    break

            # If accumulated upper bounds of all terms cannot beat threshold, terminate
            if pivot_idx is None:
                break

            pivot_cursor = active_cursors[pivot_idx]
            pivot_doc = pivot_cursor.current_doc_id()
            lead_doc = active_cursors[0].current_doc_id()

            if lead_doc == pivot_doc:
                # All cursors from 0..pivot_idx point to pivot_doc: full evaluation required
                full_score = self.scorer.score_document(pivot_doc, unique_tokens)
                evaluated_docs_count += 1

                if full_score > threshold:
                    if len(heap) < k:
                        heapq.heappush(heap, (full_score, pivot_doc))
                    else:
                        heapq.heappushpop(heap, (full_score, pivot_doc))

                    if len(heap) == k:
                        threshold = heap[0][0]

                # Advance all cursors currently at pivot_doc
                for c in active_cursors:
                    if c.current_doc_id() == pivot_doc:
                        c.advance()
            else:
                # Pick a cursor pointing to lead_doc < pivot_doc and advance to pivot_doc
                active_cursors[0].seek(pivot_doc)

        # Extract and sort top-k results descending by score
        top_k: List[Tuple[str, float]] = []
        while heap:
            score, doc_id = heapq.heappop(heap)
            top_k.append((doc_id, round(score, 4)))
        top_k.reverse()

        total_candidates = len(all_candidate_docs)
        metrics = {
            "evaluated_docs": evaluated_docs_count,
            "total_candidates": total_candidates,
            "pruned_docs": max(0, total_candidates - evaluated_docs_count),
            "threshold": round(threshold, 4),
        }

        return top_k, metrics
