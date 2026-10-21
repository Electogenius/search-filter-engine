"""Unit tests for Bloom Filter probabilistic data structure.

Verifies:
- Optimal m (bit size) and k (hash function count) calculations.
- Membership verification (contains and 'in' operator).
- Strict 0% false negative guarantee.
- Empirical false positive rate aligns with theoretical target p = 0.01.
- Edge cases and lifecycle methods (clear, len, empty filter).
"""

import math
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_structures.bloom_filter import BloomFilter


def test_bloom_filter_optimal_parameters():
    """Verify optimal bit array size m and hash function count k calculation."""
    n = 1000
    p = 0.01

    expected_m = math.ceil(-(n * math.log(p)) / (math.log(2) ** 2))
    expected_k = round((expected_m / n) * math.log(2))

    bf = BloomFilter(expected_elements=n, false_positive_rate=p)

    assert bf.size == expected_m
    assert bf.hash_count == expected_k
    assert bf.size == 9586
    assert bf.hash_count == 7


def test_bloom_filter_custom_parameters():
    """Ensure explicit size and hash_count override automatic calculation."""
    bf = BloomFilter(size=512, hash_count=4)
    assert bf.size == 512
    assert bf.hash_count == 4
    assert len(bf.bit_array) == 64  # 512 bits / 8 = 64 bytes


def test_bloom_filter_membership_verification():
    """Verify basic item insertion and membership query."""
    bf = BloomFilter(expected_elements=100, false_positive_rate=0.01)

    words = ["wireless", "keyboard", "bluetooth", "mechanical", "ergonomic"]
    for word in words:
        bf.add(word)

    # All inserted words must be reported as present
    for word in words:
        assert bf.contains(word) is True
        assert word in bf  # __contains__ hook

    # Absent words should test negative
    assert bf.contains("nonexistent_random_token_xyz_123") is False
    assert "another_absent_term" not in bf


def test_bloom_filter_zero_false_negatives():
    """Verify fundamental invariant: 0% False Negatives.

    If an item was added, contains(item) MUST NEVER return False.
    """
    n = 500
    bf = BloomFilter(expected_elements=n, false_positive_rate=0.01)

    dataset = [f"indexed_token_{i}" for i in range(n)]
    for token in dataset:
        bf.add(token)

    false_negatives = 0
    for token in dataset:
        if not bf.contains(token):
            false_negatives += 1

    assert false_negatives == 0, f"Expected 0 false negatives, got {false_negatives}"
    assert len(bf) == n


def test_bloom_filter_false_positive_rate():
    """Empirically measure false positive rate across 10,000 non-member queries.

    Target false positive rate is p = 0.01.
    Empirical rate should be close to 0.01 and well under 0.03.
    """
    n = 1000
    target_p = 0.01
    bf = BloomFilter(expected_elements=n, false_positive_rate=target_p)

    # Insert n members
    for i in range(n):
        bf.add(f"member_word_{i}")

    # Query 10,000 distinct non-members
    test_queries = 10000
    false_positives = 0
    for i in range(test_queries):
        query = f"non_member_probe_{i}"
        if bf.contains(query):
            false_positives += 1

    empirical_p = false_positives / test_queries
    # Verify empirical false positive rate is consistent with design target
    assert empirical_p < 0.03, (
        f"Empirical false positive rate {empirical_p:.4f} exceeds threshold for target {target_p}"
    )


def test_bloom_filter_empty_state_and_clear():
    """Verify empty filter behaviour and clear() method."""
    bf = BloomFilter(expected_elements=50)

    # Empty filter should have count 0 and return False for queries
    assert len(bf) == 0
    assert bf.contains("anything") is False

    bf.add("test_token")
    assert len(bf) == 1
    assert bf.contains("test_token") is True

    # Clear should zero all bits
    bf.clear()
    assert len(bf) == 0
    assert bf.contains("test_token") is False
    assert all(b == 0 for b in bf.bit_array)


def test_bloom_filter_edge_cases():
    """Verify handling of empty string, None, and Unicode tokens."""
    bf = BloomFilter(expected_elements=50)

    # None handling
    assert bf.contains(None) is False
    bf.add(None)
    assert len(bf) == 0  # None is skipped

    # Empty string handling
    bf.add("")
    assert bf.contains("") is True

    # Unicode strings
    unicode_tokens = ["café", "naïve", "résumé", "日本語", "⚡"]
    for token in unicode_tokens:
        bf.add(token)
        assert bf.contains(token) is True

