"""AVL-Tree based Inverted Index.

Maps vocabulary terms to document posting lists using an underlying AVL Tree.
Supports multi-field indexing (e.g. title and description with customizable weights)
and term lookup in O(log V) time.
"""

from typing import Dict, List, Optional, Set

try:
    from backend.app.data_structures.avl_tree import AVLTree
    from backend.app.indexing.tokenizer import Tokenizer
except ModuleNotFoundError:
    from app.data_structures.avl_tree import AVLTree
    from app.indexing.tokenizer import Tokenizer


class AVLInvertedIndex:
    """Inverted index data structure backed by a self-balancing AVL Tree."""

    def __init__(self, tokenizer: Optional[Tokenizer] = None):
        self.tree: AVLTree = AVLTree()
        self.tokenizer: Tokenizer = tokenizer or Tokenizer()
        self.doc_count: int = 0
        self.indexed_doc_ids: Set[str] = set()

    def __len__(self) -> int:
        """Return number of unique vocabulary terms indexed."""
        return len(self.tree)

    def index_product(
        self,
        doc_id: str,
        title: str,
        description: str,
        title_weight: int = 3,
        desc_weight: int = 1
    ) -> None:
        """Index a product title and description into the AVL tree.

        Title tokens are assigned higher weight to prioritize title matches
        over description body text.
        """
        title_freqs = self.tokenizer.get_term_frequencies(title)
        desc_freqs = self.tokenizer.get_term_frequencies(description)

        # Merge term frequencies with weights
        combined_freqs: Dict[str, int] = {}
        for term, count in title_freqs.items():
            combined_freqs[term] = combined_freqs.get(term, 0) + (count * title_weight)
        for term, count in desc_freqs.items():
            combined_freqs[term] = combined_freqs.get(term, 0) + (count * desc_weight)

        for term, count in combined_freqs.items():
            self.tree.insert(term=term, doc_id=doc_id, count=count)

        if doc_id not in self.indexed_doc_ids:
            self.indexed_doc_ids.add(doc_id)
            self.doc_count += 1

    def lookup_term(self, term: str) -> Optional[Dict[str, int]]:
        """Find postings for a single normalized term using the AVL tree in O(log V)."""
        normalized_term = term.strip().lower()
        return self.tree.search(normalized_term)

    def search_query(self, query: str) -> Dict[str, float]:
        """Search the inverted index for all tokens in the query string.

        Computes relevance scores combining term frequency and a bonus for documents
        matching multiple query terms (coordinate matching).

        Returns:
            Dict mapping doc_id to computed match score.
        """
        tokens = self.tokenizer.tokenize(query)
        if not tokens:
            return {}

        doc_scores: Dict[str, float] = {}
        term_matches_per_doc: Dict[str, int] = {}

        for token in tokens:
            postings = self.lookup_term(token)
            if not postings:
                continue

            for doc_id, tf in postings.items():
                doc_scores[doc_id] = doc_scores.get(doc_id, 0.0) + float(tf)
                term_matches_per_doc[doc_id] = term_matches_per_doc.get(doc_id, 0) + 1

        # Coordinate matching bonus: reward documents that match more of the query terms
        total_tokens = len(tokens)
        for doc_id, matched_count in term_matches_per_doc.items():
            coordination_factor = matched_count / total_tokens
            doc_scores[doc_id] = round(doc_scores[doc_id] * (1.0 + coordination_factor), 3)

        return doc_scores

    def get_vocabulary(self) -> List[str]:
        """Return all unique indexed terms in lexicographical order."""
        return self.tree.get_vocabulary()

