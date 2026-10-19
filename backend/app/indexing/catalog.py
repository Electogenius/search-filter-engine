"""In-memory product catalogue and search coordinator.

Loads product data from JSON files at startup, indexes text into an AVL-Tree based
inverted index, and applies multi-criteria filters and sorting.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from backend.app.indexing.inverted_index import AVLInvertedIndex
except ModuleNotFoundError:
    from app.indexing.inverted_index import AVLInvertedIndex


class ProductCatalog:
    """In-memory catalogue storing product records and the AVL inverted index."""

    def __init__(self, data_path: Optional[Path] = None):
        self.data_path: Path = data_path or self._resolve_data_path()
        self.products_by_id: Dict[str, Dict[str, Any]] = {}
        self.inverted_index: AVLInvertedIndex = AVLInvertedIndex()
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

    def _load_and_index(self) -> None:
        """Read products.json and construct the in-memory AVL inverted index."""
        if not self.data_path.exists():
            return

        with open(self.data_path, "r", encoding="utf-8") as f:
            items: List[Dict[str, Any]] = json.load(f)

        for item in items:
            product_id = item["id"]
            self.products_by_id[product_id] = item
            self.inverted_index.index_product(
                doc_id=product_id,
                title=item.get("title", ""),
                description=item.get("description", "")
            )

    def get_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Look up product details by unique product ID in O(1) time."""
        return self.products_by_id.get(product_id)

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
    ) -> Dict[str, Any]:
        """Perform search with query matching against AVL inverted index and apply filters."""
        query_str = (q or "").strip()
        matched_scores: Dict[str, float] = {}

        if query_str:
            # Query terms lookup via AVL inverted index
            matched_scores = self.inverted_index.search_query(query_str)
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
            if query_str and pid in matched_scores:
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
            if query_str:
                filtered_results.sort(key=lambda x: (-x.get("score", 0.0), -x.get("rating", 0.0)))
            else:
                filtered_results.sort(key=lambda x: (-x.get("rating", 0.0), x.get("price", 0.0)))

        total_matches = len(filtered_results)
        paginated_results = filtered_results[offset: offset + limit]

        return {
            "query": query_str,
            "total": total_matches,
            "limit": limit,
            "offset": offset,
            "results": paginated_results
        }


# Global singleton instance
_catalog_instance: Optional[ProductCatalog] = None


def get_catalog() -> ProductCatalog:
    """Retrieve or initialize the global in-memory product catalogue singleton."""
    global _catalog_instance
    if _catalog_instance is None:
        _catalog_instance = ProductCatalog()
    return _catalog_instance

