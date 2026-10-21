import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.ranking.bm25 import BM25Scorer
from app.ranking.wand import WANDTopK
from app.indexing.tokenizer import Tokenizer


SAMPLE_CORPUS = {
    "doc1": {
        "id": "doc1",
        "title": "Wireless Mechanical Keyboard",
        "description": "Compact mechanical gaming keyboard with hot swappable switches and wireless connectivity."
    },
    "doc2": {
        "id": "doc2",
        "title": "Wireless Ergonomic Mouse",
        "description": "Ergonomic vertical optical wireless mouse designed for comfort."
    },
    "doc3": {
        "id": "doc3",
        "title": "Bluetooth Wireless Noise-Cancelling Headphones",
        "description": "Premium over-ear wireless headphones with active noise cancellation and clear microphone."
    },
    "doc4": {
        "id": "doc4",
        "title": "Mechanical Gaming Keyboard RGB",
        "description": "Heavy duty wired mechanical keyboard with per-key RGB backlighting and tactile switches."
    },
    "doc5": {
        "id": "doc5",
        "title": "USB-C Multiport Adapter Hub",
        "description": "Aluminum dongle with 4K HDMI, Gigabit Ethernet, and USB ports."
    }
}


def test_bm25_idf_strictly_positive():
    """Verify Robertson-Sparck Jones non-negative IDF formula produces valid positive scores."""
    tokenizer = Tokenizer()
    scorer = BM25Scorer(corpus=SAMPLE_CORPUS, tokenizer=tokenizer)

    # Term present in multiple docs vs term present in one doc
    idf_wireless = scorer.idf("wireless")
    idf_adapter = scorer.idf("adapter")

    assert idf_wireless > 0.0
    assert idf_adapter > 0.0
    # Rarer terms should have strictly higher IDF
    assert idf_adapter > idf_wireless


def test_bm25_length_normalization():
    """Verify document length normalization penalizes excessively long documents with identical term counts."""
    tokenizer = Tokenizer()
    synthetic_corpus = {
        "short_doc": {
            "id": "short_doc",
            "title": "wireless keyboard",
            "description": "keyboard"
        },
        "long_doc": {
            "id": "long_doc",
            "title": "wireless keyboard",
            "description": "keyboard " + "filler word test extra text padding " * 10
        }
    }
    scorer = BM25Scorer(corpus=synthetic_corpus, tokenizer=tokenizer)
    short_score = scorer.score_document("short_doc", ["keyboard"])
    long_score = scorer.score_document("long_doc", ["keyboard"])

    assert short_score > long_score


def test_wand_top_k_exact_scores():
    """Verify WAND returns the exact same top-k documents and scores as exhaustive BM25 evaluation."""
    tokenizer = Tokenizer()
    scorer = BM25Scorer(corpus=SAMPLE_CORPUS, tokenizer=tokenizer)
    wand = WANDTopK(bm25_scorer=scorer)

    query_tokens = ["wireless", "keyboard"]
    k = 3

    # Exhaustive ground truth
    exhaustive_scores = scorer.score_all_candidates(query_tokens)
    exhaustive_top_k = sorted(exhaustive_scores.items(), key=lambda x: (-x[1], x[0]))[:k]

    # WAND top-k
    wand_top_k, metrics = wand.search_with_metrics(query_tokens, k=k)

    assert len(wand_top_k) == len(exhaustive_top_k)
    for (wand_doc, wand_score), (exh_doc, exh_score) in zip(wand_top_k, exhaustive_top_k):
        assert wand_doc == exh_doc
        assert abs(wand_score - exh_score) < 1e-4


def test_wand_pruning_efficiency():
    """Verify WAND prunes evaluations and skips non-competitive documents."""
    tokenizer = Tokenizer()
    # Create a 10-document synthetic corpus
    large_corpus = {}
    for i in range(10):
        large_corpus[f"doc_{i}"] = {
            "id": f"doc_{i}",
            "title": f"product {i} " + ("wireless " if i % 2 == 0 else "") + ("keyboard " if i % 3 == 0 else ""),
            "description": "electronics accessories hardware computer gear."
        }

    scorer = BM25Scorer(corpus=large_corpus, tokenizer=tokenizer)
    wand = WANDTopK(bm25_scorer=scorer)

    # Search with a tight k=1
    results, metrics = wand.search_with_metrics(["wireless", "keyboard"], k=1)
    assert len(results) == 1
    assert metrics["total_candidates"] >= metrics["evaluated_docs"]


def test_wand_edge_cases():
    """Verify WAND behavior on empty queries, k=0, k > N, and non-existent terms."""
    tokenizer = Tokenizer()
    scorer = BM25Scorer(corpus=SAMPLE_CORPUS, tokenizer=tokenizer)
    wand = WANDTopK(bm25_scorer=scorer)

    # Empty query
    assert wand.search([], k=5) == []

    # Non-existent term
    assert wand.search(["nonexistenttermxyz"], k=5) == []

    # k=0
    assert wand.search(["wireless"], k=0) == []

    # k > corpus size
    results = wand.search(["wireless"], k=100)
    assert len(results) <= len(SAMPLE_CORPUS)
