"""In-memory product catalogue and search coordinator.

Loads product data from JSON files at startup, indexes text into an AVL-Tree based
inverted index, and applies multi-criteria filters and sorting.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from backend.app.indexing.inverted_index import AVLInvertedIndex
    from backend.app.data_structures.trie import Trie
    from backend.app.data_structures.bloom_filter import BloomFilter
    from backend.app.search.query_processor import QueryProcessor
    from backend.app.ranking.bm25 import BM25Scorer
    from backend.app.ranking.wand import WANDTopK
    from backend.app.recommendations.cooccurrence import CooccurrenceRecommender
except ModuleNotFoundError:
    from app.indexing.inverted_index import AVLInvertedIndex
    from app.data_structures.trie import Trie
    from app.data_structures.bloom_filter import BloomFilter
    from app.search.query_processor import QueryProcessor
    from app.ranking.bm25 import BM25Scorer
    from app.ranking.wand import WANDTopK
    from app.recommendations.cooccurrence import CooccurrenceRecommender


class ProductCatalog:
    """In-memory catalogue storing product records, the AVL inverted index, Bloom Filter, and prefix Trie."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path: Path = data_path or self._resolve_data_path()
        self.products_by_id: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: AVLInvertedIndex = AVLInvertedIndex()
        self.trie: Trie = Trie()
        self.bloom_filter: Optional[BloomFilter] = None
        self.query_processor: Optional[QueryProcessor] = None
        self.bm25_scorer: Optional[BM25Scorer] = None
        self.wand: Optional[WANDTopK] = None
        self.recommender: Optional[CooccurrenceRecommender] = None
        self._load_and_index()

    @staticmethod
    def _resolve_data_path() -> Path:
        """Locate data/products.json relative to repository root."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_file = base_dir / "data" / "products.json"
        if not data_file.exists():
            # Fallback relative to current working directory
            data_file = Path("data/products.json")
        return data_file

    @staticmethod
    def _resolve_baskets_path() -> Path:
        """Locate data/baskets.json relative to repository root."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_file = base_dir / "data" / "baskets.json"
        if not data_file.exists():
            data_file = Path("data/baskets.json")
        return data_file

    def _load_and_index(self) -> None:
        """Read products.json and construct the in-memory AVL inverted index and Trie."""
        if not self.data_path.exists():
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            items: List[Dict[str, Any]] = json.load(f)

        for item in items:
            product_id = item["id"]
            self.products_by_id[product_id] = item
            title = item.get("title", "").strip()
            desc = item.get("description", "").strip()

            self.inverted_index.index_product(
                doc_id=product_id,
                title=title,
                description=desc
            )

            # Feed product title into Trie with higher priority
            if title:
                self.trie.insert(title.lower(), payload={"title": title.lower(), "frequency": 10})

        # Feed all unique vocabulary tokens from inverted index into Trie
        vocab = self.inverted_index.get_vocabulary()
        for term in vocab:
            self.trie.insert(term.lower(), payload={"title": term.lower(), "frequency": 1})

        # Calculate optimal m = -n*lnp/(ln 2)^2 and k = (m/n) ln 2 for target p=0.01
        expected_n = max(len(vocab), 100)
        self.bloom_filter = BloomFilter(
            expected_elements=expected_n,
            false_positive_rate=0.01
        )

        # Populate Bloom Filter with all indexed dictionary tokens at startup
        vocab_freqs: Dict[str, int] = {}
        for term in vocab:
            normalized_term = term.lower()
            self.bloom_filter.add(normalized_term)
            postings = self.inverted_index.lookup_term(normalized_term)
            vocab_freqs[normalized_term] = sum(postings.values()) if postings else 1

        # Initialize QueryProcessor with Bloom Filter fast rejection and Levenshtein DP
        self.query_processor = QueryProcessor(
            bloom_filter=self.bloom_filter,
            vocabulary=vocab_freqs,
            tokenizer=self.inverted_index.tokenizer,
            max_edit_distance=2
        )

        # Initialize Okapi BM25 Scorer and WAND Top-K Pruning Engine
        self.bm25_scorer = BM25Scorer(
            corpus=self.products_by_id,
            tokenizer=self.inverted_index.tokenizer,
            k1=1.5,
            b=0.75,
            title_weight=3,
            desc_weight=1
        )
        self.wand = WANDTopK(bm25_scorer=self.bm25_scorer)

        # Initialize Market Basket Co-Occurrence Recommender
        baskets_path = self._resolve_baskets_path()
        self.recommender = CooccurrenceRecommender(
            baskets_path=baskets_path,
            products=self.products_by_id
        )

    def suggest(self, prefix: str, limit: int = 5) -> List[str]:
        """Provide real-time prefix completion suggestions using the Trie in O(L) time."""
        return self.trie.search_prefix(prefix=prefix, limit=limit)

    def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Look up product details by unique product ID in O(1) time."""
        return self.products_by_id.get(product_id)

    def get_recommendations(
        self,
        product_id: str,
        limit: int = 4
    ) -> Optional[List[Dict[str, Any]]]:
        """Fetch market basket co-occurrence recommendations for a product."""
        if product_id not in self.products_by_id:
            return None
        if not self.recommender:
            return []
        return self.recommender.get_recommendations(product_id, limit=limit)

    def wand_search(self, query: str, k: int = 10) -> List[Any]:
        """Run pure WAND top-k candidate pruning for a query."""
        if not self.wand:
            return []
        tokens = self.inverted_index.tokenizer.tokenize(query)
        return self.wand.search(tokens, k=k)

    def search(
        self,
        q: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        available: Optional[bool] = None,
        sort_by: str = "relevance",
        limit: int = 10,
        offset: int = 0,
        auto_correct: bool = True,
    ) -> Dict[str, Any]:
        """Perform search with query matching against AVL inverted index and apply filters."""
        raw_query = (q or "").strip()
        corrected_query: Optional[str] = None
        search_query_str = raw_query

        # Search Pipeline: Bloom filter fast rejection + Levenshtein spelling correction
        if raw_query and auto_correct and self.query_processor:
            proc_res = self.query_processor.process_query(raw_query)
            if proc_res.get("corrected"):
                corrected_query = proc_res.get("corrected_query")
                search_query_str = proc_res.get("effective_query", raw_query)

        matched_scores: Dict[str, float] = {}

        if search_query_str:
            # Compute Okapi BM25 relevance scores across matching candidates
            tokens = self.inverted_index.tokenizer.tokenize(search_query_str)
            if self.bm25_scorer:
                matched_scores = self.bm25_scorer.score_all_candidates(tokens)
            else:
                matched_scores = self.inverted_index.search_query(search_query_str)
            candidate_ids = list(matched_scores.keys())
        else:
            # No text query specified: all products are candidates
            candidate_ids = list(self.products_by_id.keys())

        filtered_results: List[Dict[str, Any]] = []

        for pid in candidate_ids:
            prod = self.products_by_id.get(pid)
            if not prod:
                continue

            # 1. Category Filter
            if category:
                if prod.get("category", "").lower() != category.strip().lower():
                    continue

            # 2. Price Filters
            price = prod.get("price", 0.0)
            if min_price is not None and price < min_price:
                continue
            if max_price is not None and price > max_price:
                continue

            # 3. Rating Filter
            rating = prod.get("rating", 0.0)
            if min_rating is not None and rating < min_rating:
                continue

            # 4. Availability Filter
            if available is not None:
                if prod.get("available", False) != available:
                    continue

            # Attach match score if text query was evaluated
            item_copy = dict(prod)
            if search_query_str and pid in matched_scores:
                item_copy["score"] = matched_scores[pid]

            filtered_results.append(item_copy)

        # Apply Sorting
        if sort_by == "price_asc":
            filtered_results.sort(key=lambda x: (x.get("price", 0.0), -x.get("rating", 0.0)))
        elif sort_by == "price_desc":
            filtered_results.sort(key=lambda x: (-x.get("price", 0.0), -x.get("rating", 0.0)))
        elif sort_by == "rating_desc":
            filtered_results.sort(key=lambda x: (-x.get("rating", 0.0), x.get("price", 0.0)))
        else:
            # Default "relevance" sort: if text score present, sort by score descending, else rating
            if search_query_str:
                filtered_results.sort(key=lambda x: (-x.get("score", 0.0), -x.get("rating", 0.0)))
            else:
                filtered_results.sort(key=lambda x: (-x.get("rating", 0.0), x.get("price", 0.0)))

        total_matches = len(filtered_results)
        paginated_results = filtered_results[offset: offset + limit]

        response: Dict[str, Any] = {
            "query": raw_query,
            "total": total_matches,
            "limit": limit,
            "offset": offset,
            "results": paginated_results
        }
        if corrected_query:
            response["corrected_query"] = corrected_query

        return response


# Global singleton instance
_catalog_instance: Optional[ProductCatalog] = None


def get_catalog() -> ProductCatalog:
    """Retrieve or initialize the global in-memory product catalogue singleton."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = ProductCatalog()
    return _catalog_instance

