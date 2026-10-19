import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_structures.trie import Trie, TrieNode
from app.main import app

client = TestClient(app)


def test_trie_root_initialization():
    """Verify that a new Trie initializes with an empty root and zero size."""
    trie = Trie()
    assert len(trie) == 0
    assert trie.root is not None
    assert isinstance(trie.root, TrieNode)
    assert len(trie.root.children) == 0
    assert trie.root.is_end_of_word is False
    assert trie.root.payloads == []


def test_trie_insert_and_contains():
    """Verify O(L) insertion and exact term lookup."""
    trie = Trie()
    trie.insert("keyboard")
    trie.insert("mouse")

    assert len(trie) == 2
    assert trie.contains("keyboard") is True
    assert trie.contains("mouse") is True
    assert trie.contains("key") is False
    assert trie.contains("monitor") is False


def test_trie_prefix_traversal():
    """Verify prefix traversal returns all completions matching the given prefix."""
    trie = Trie()
    words = [
        "wireless mechanical keyboard",
        "wireless ergonomic mouse",
        "wireless noise-cancelling headphones",
        "wired gaming mouse",
        "bluetooth speaker"
    ]
    for w in words:
        trie.insert(w)

    suggestions = trie.search_prefix("wire", limit=10)
    assert len(suggestions) == 4
    assert "wireless mechanical keyboard" in suggestions
    assert "wireless ergonomic mouse" in suggestions
    assert "wireless noise-cancelling headphones" in suggestions
    assert "wired gaming mouse" in suggestions
    assert "bluetooth speaker" not in suggestions


def test_trie_prefix_not_found():
    """Verify that searching for a non-existent prefix returns an empty list without error."""
    trie = Trie()
    trie.insert("apple")
    trie.insert("application")

    assert trie.search_prefix("xyz") == []
    assert trie.search_prefix("banana") == []
    assert trie.starts_with("xyz") is False


def test_trie_case_insensitivity():
    """Verify that insertion and prefix search are strictly case-insensitive."""
    trie = Trie()
    trie.insert("Wireless Mouse")
    trie.insert("WIRELESS KEYBOARD")

    assert trie.contains("wireless mouse") is True
    assert trie.contains("WIRELESS MOUSE") is True
    assert trie.contains("Wireless Mouse") is True

    lower_results = trie.search_prefix("wire")
    upper_results = trie.search_prefix("WIRE")
    mixed_results = trie.search_prefix("WiRe")

    assert lower_results == upper_results == mixed_results
    assert len(lower_results) == 2


def test_trie_suggestion_limits():
    """Verify that search_prefix respects the requested limit."""
    trie = Trie()
    for i in range(10):
        trie.insert(f"product-{i:02d}")

    assert len(trie.search_prefix("product", limit=3)) == 3
    assert len(trie.search_prefix("product", limit=7)) == 7
    assert len(trie.search_prefix("product", limit=15)) == 10
    assert trie.search_prefix("product", limit=0) == []


def test_trie_ranking_by_frequency():
    """Verify that completions with higher accumulated frequency are ranked first."""
    trie = Trie()
    # Insert with different frequency weights
    trie.insert("keyboard", payload={"title": "keyboard", "frequency": 1})
    trie.insert("keycap set", payload={"title": "keycap set", "frequency": 5})
    trie.insert("keyboard mechanical", payload={"title": "keyboard mechanical", "frequency": 10})

    suggestions = trie.search_prefix("key", limit=5)
    # Highest frequency should appear first
    assert suggestions[0] == "keyboard mechanical"
    assert suggestions[1] == "keycap set"
    assert suggestions[2] == "keyboard"


def test_trie_empty_and_whitespace_prefix():
    """Verify that empty or whitespace-only prefix queries return empty list."""
    trie = Trie()
    trie.insert("hello")
    assert trie.search_prefix("") == []
    assert trie.search_prefix("   ") == []


def test_api_suggest_endpoint_success():
    """Integration test: GET /api/suggest returns 200 with suggestions matching API contract."""
    response = client.get("/api/suggest?prefix=wire&limit=5")
    assert response.status_code == 200
    data = response.json()

    assert data["prefix"] == "wire"
    assert isinstance(data["suggestions"], list)
    assert len(data["suggestions"]) > 0

    # Ensure suggestions match products in products.json starting with wire
    suggestions_lower = [s.lower() for s in data["suggestions"]]
    assert any("wireless" in s for s in suggestions_lower)


def test_api_suggest_endpoint_validation():
    """Integration test: GET /api/suggest returns 400 Bad Request on empty prefix."""
    response = client.get("/api/suggest?prefix=")
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "must not be empty" in data["detail"].lower()

