"""Market Basket Co-Occurrence Recommender.

Constructs an in-memory symmetric co-occurrence graph/matrix from transaction baskets
in O(B * L^2) build time, providing real-time product recommendations based on
purchase co-occurrence frequency.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class CooccurrenceRecommender:
    """In-memory recommendation engine backed by a symmetric item co-occurrence matrix."""

    def __init__(
        self,
        baskets_path: Optional[Path] = None,
        baskets_data: Optional[List[Dict[str, Any]]] = None,
        products: Optional[Dict[str, Dict[str, Any]]] = None,
    ):
        self.products: Dict[str, Dict[str, Any]] = products or {}
        self.matrix: Dict[str, Dict[str, int]] = {}
        self.total_baskets: int = 0

        if baskets_data is not None:
            self._build_matrix(baskets_data)
        elif baskets_path is not None and baskets_path.exists():
            with open(baskets_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._build_matrix(data)
        else:
            default_path = self._resolve_default_baskets_path()
            if default_path.exists():
                with open(default_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._build_matrix(data)

    @staticmethod
    def _resolve_default_baskets_path() -> Path:
        """Resolve path to data/baskets.json relative to repository root."""
        base_dir = Path(__file__).resolve().parent.parent.parent.parent
        data_file = base_dir / "data" / "baskets.json"
        if not data_file.exists():
            data_file = Path("data/baskets.json")
        return data_file

    def _build_matrix(self, baskets: List[Dict[str, Any]]) -> None:
        """Construct the symmetric co-occurrence matrix in O(B * L^2) time."""
        self.total_baskets = len(baskets)
        for basket in baskets:
            items = basket.get("items", [])
            # Deduplicate items within the same basket
            unique_items = sorted(set(items))
            n = len(unique_items)
            for i in range(n):
                item_a = unique_items[i]
                if item_a not in self.matrix:
                    self.matrix[item_a] = {}

                for j in range(i + 1, n):
                    item_b = unique_items[j]
                    if item_b not in self.matrix:
                        self.matrix[item_b] = {}

                    # Increment symmetric co-occurrence count
                    self.matrix[item_a][item_b] = self.matrix[item_a].get(item_b, 0) + 1
                    self.matrix[item_b][item_a] = self.matrix[item_b].get(item_a, 0) + 1

    def get_cooccurrence_count(self, item_a: str, item_b: str) -> int:
        """Return raw co-occurrence frequency between two products."""
        return self.matrix.get(item_a, {}).get(item_b, 0)

    def get_all_cooccurrences(self, product_id: str) -> Dict[str, int]:
        """Return all co-occurring products and their counts for a given product."""
        return dict(self.matrix.get(product_id, {}))

    def get_recommendations(
        self,
        product_id: str,
        limit: int = 4
    ) -> List[Dict[str, Any]]:
        """Retrieve top-N recommendations for a product ordered by co-occurrence frequency.

        Returns:
            List of product dicts matching the api-contract schema, enriched with co_occurrence_count.
        """
        co_counts = self.matrix.get(product_id, {})
        if not co_counts:
            return []

        # Sort candidate products by co-occurrence count descending
        # Secondary tie-breakers: product rating descending, price ascending
        def sort_key(candidate_id: str) -> Tuple[int, float, float]:
            count = co_counts[candidate_id]
            prod = self.products.get(candidate_id, {})
            rating = float(prod.get("rating", 0.0))
            price = float(prod.get("price", 0.0))
            return (count, rating, -price)

        sorted_candidates = sorted(co_counts.keys(), key=sort_key, reverse=True)

        recommendations: List[Dict[str, Any]] = []
        for cand_id in sorted_candidates[:limit]:
            prod = self.products.get(cand_id)
            count = co_counts[cand_id]
            if prod:
                rec_item = {
                    "id": prod["id"],
                    "title": prod.get("title", ""),
                    "category": prod.get("category", ""),
                    "price": prod.get("price", 0.0),
                    "rating": prod.get("rating", 0.0),
                    "available": prod.get("available", False),
                    "co_occurrence_count": count,
                }
            else:
                rec_item = {
                    "id": cand_id,
                    "title": cand_id,
                    "category": "General",
                    "price": 0.0,
                    "rating": 0.0,
                    "available": True,
                    "co_occurrence_count": count,
                }
            recommendations.append(rec_item)

        return recommendations
