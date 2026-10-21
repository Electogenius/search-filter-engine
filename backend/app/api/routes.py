from typing import Optional
from fastapi import APIRouter, HTTPException, Query, status

router = APIRouter()


@router.get("/health", summary="Health Check")
def health_check() -> dict:
    """Verify backend service liveness and readiness."""
    return {
        "status": "ok",
        "service": "search-filter-engine",
        "version": "0.1.0"
    }


# ============================================================================
# PLACEHOLDER ROUTE DEFINITIONS
# The endpoints below define the routing structure as per docs/api-contract.md.
# Implementation will be completed in subsequent milestones by the project team.
# No mock search or recommendation data is returned.
# ============================================================================


try:
    from backend.app.indexing.catalog import get_catalog
except ModuleNotFoundError:
    from app.indexing.catalog import get_catalog


@router.get("/search", summary="Search and Filter Products")
def search_products(
    q: Optional[str] = Query(None, description="Search query string"),
    category: Optional[str] = Query(None, description="Category filter"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    available: Optional[bool] = Query(None, description="In-stock filter"),
    sort_by: str = Query("relevance", description="Sort order: relevance, price_asc, price_desc, rating_desc"),
    limit: int = Query(10, ge=1, le=50, description="Max results to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    auto_correct: bool = Query(True, description="Enable typo correction via Bloom Filter and Levenshtein DP"),
) -> dict:
    """Search and filter products across the in-memory catalogue.

    Backed by:
    - AVL-Tree based Inverted Index for text token retrieval
    - Bloom Filter fast-rejection with 0% false negatives
    - Levenshtein DP for typo detection and correction
    - Multi-criteria filtering (category, price range, rating, availability)
    """
    if min_price is not None and max_price is not None and min_price > max_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameter: min_price cannot be greater than max_price."
        )

    catalog = get_catalog()
    return catalog.search(
        q=q,
        category=category,
        min_price=min_price,
        max_price=max_price,
        min_rating=min_rating,
        available=available,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
        auto_correct=auto_correct,
    )


@router.get("/products/{id}", summary="Get Product Details")
def get_product(id: str) -> dict:
    """Fetch complete product details by unique product ID in O(1) time."""
    catalog = get_catalog()
    product = catalog.get_by_id(id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{id}' not found."
        )
    return product


@router.get("/suggest", summary="Prefix Autocomplete Suggestions")
def autocomplete_suggestions(
    prefix: Optional[str] = Query(None, description="Prefix string to search suggestions for"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions to return"),
) -> dict:
    """Provide real-time prefix completion suggestions backed by Trie (Prefix Tree)."""
    if prefix is None or not prefix.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query parameter 'prefix' must not be empty."
        )

    catalog = get_catalog()
    suggestions = catalog.suggest(prefix=prefix.strip(), limit=limit)
    return {
        "prefix": prefix,
        "suggestions": suggestions
    }


@router.get("/products/{id}/related", summary="Related Product Recommendations")
def get_related_products(
    id: str,
    limit: int = Query(4, ge=1, le=10, description="Max related products to return"),
) -> dict:
    """Recommend products based on market basket co-occurrence statistics.

    Backed by:
    - In-memory symmetric co-occurrence matrix constructed from baskets.json
    """
    catalog = get_catalog()
    recommendations = catalog.get_recommendations(product_id=id, limit=limit)
    if recommendations is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id '{id}' not found."
        )
    return {
        "product_id": id,
        "recommendations": recommendations
    }

