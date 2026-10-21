"""Unit tests for Levenshtein Dynamic Programming & Fuzzy Matching.

Verifies:
- Substitution edit operations.
- Insertion edit operations.
- Deletion edit operations.
- Transposition edit operations (Damerau-Levenshtein adjacent swaps).
- Max edit distance thresholding (k <= 2) and early pruning.
- Vocabulary lookup and tie-breaking.
- Space-optimized 1D DP table equivalence.
"""

import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.search.fuzzy import (
    levenshtein_distance,
    levenshtein_distance_1d,
    find_closest_match,
    find_closest_matches,
)


def test_levenshtein_substitution():
    """Verify substitution edit operations."""
    assert levenshtein_distance("cat", "bat") == 1
    assert levenshtein_distance("cat", "dog") == 3
    assert levenshtein_distance("kitten", "sitten") == 1
    assert levenshtein_distance("phone", "prone") == 1
    assert levenshtein_distance("same", "same") == 0


def test_levenshtein_insertion():
    """Verify character insertion edit operations."""
    assert levenshtein_distance("cat", "cats") == 1
    assert levenshtein_distance("wireles", "wireless") == 1
    assert levenshtein_distance("key", "keyboard") == 5
    assert levenshtein_distance("", "abc") == 3
    assert levenshtein_distance("headphone", "headphones") == 1


def test_levenshtein_deletion():
    """Verify character deletion edit operations."""
    assert levenshtein_distance("cats", "cat") == 1
    assert levenshtein_distance("keyboard", "keybrd") == 2
    assert levenshtein_distance("apple", "appl") == 1
    assert levenshtein_distance("monitor", "") == 7


def test_levenshtein_transposition():
    """Verify adjacent character transposition (Damerau-Levenshtein) edit operations."""
    # Adjacent swap "teh" -> "the" is distance 1 with transposition allowed
    assert levenshtein_distance("teh", "the", allow_transpositions=True) == 1
    # Without transposition, swap requires 2 substitutions or 1 delete + 1 insert
    assert levenshtein_distance("teh", "the", allow_transpositions=False) == 2

    # Two character transposition "ca" -> "ac"
    assert levenshtein_distance("ca", "ac", allow_transpositions=True) == 1
    assert levenshtein_distance("ca", "ac", allow_transpositions=False) == 2

    # Adjacent swap within longer word: "wirelses" -> "wireless"
    assert levenshtein_distance("wirelses", "wireless", allow_transpositions=True) == 1


def test_levenshtein_max_distance_threshold():
    """Verify threshold pruning and early termination with max_distance."""
    # Length difference > max_distance triggers O(1) length-pruning
    dist = levenshtein_distance("cat", "helicopter", max_distance=2)
    assert dist > 2

    # Entirely disjoint strings terminated early via DP row pruning
    dist = levenshtein_distance("abcdef", "uvwxyz", max_distance=2)
    assert dist > 2

    # Within threshold k <= 2
    assert levenshtein_distance("wireles", "wireless", max_distance=2) == 1
    assert levenshtein_distance("keybrd", "keyboard", max_distance=2) == 2


def test_find_closest_match_vocabulary():
    """Verify vocabulary candidate lookup within max edit distance threshold k <= 2."""
    vocab = [
        "wireless",
        "keyboard",
        "mechanical",
        "monitor",
        "mouse",
        "ergonomic",
        "headphones"
    ]

    # Insertion error
    assert find_closest_match("wireles", vocab, max_distance=2) == "wireless"

    # Multiple deletions / omissions (distance 2)
    assert find_closest_match("keybrd", vocab, max_distance=2) == "keyboard"

    # Substitution error
    assert find_closest_match("mousa", vocab, max_distance=2) == "mouse"

    # Transposition error
    assert find_closest_match("moues", vocab, max_distance=2) == "mouse"

    # Beyond max distance threshold (e.g. k > 2) should return None
    assert find_closest_match("totallydifferentstring", vocab, max_distance=2) is None
    assert find_closest_match("xyz999", vocab, max_distance=2) is None


def test_find_closest_match_with_frequency_tiebreaker():
    """Verify that when candidates are equidistant, higher frequency is chosen."""
    # "car" is distance 1 from both "cat" and "cap"
    vocab_freqs = {
        "cat": 5,
        "cap": 50,  # "cap" has higher frequency
    }

    match = find_closest_match("car", vocab_freqs, max_distance=1)
    assert match == "cap"


def test_space_optimized_1d_dp():
    """Verify that 1D DP table matches standard 2D Levenshtein distance."""
    test_pairs = [
        ("kitten", "sitting"),
        ("rosettacode", "raisethysword"),
        ("wireless", "wireles"),
        ("keyboard", "keybrd"),
        ("apple", "orange"),
        ("", "test"),
        ("test", ""),
        ("identical", "identical"),
    ]

    for s1, s2 in test_pairs:
        dist_2d = levenshtein_distance(s1, s2, allow_transpositions=False)
        dist_1d = levenshtein_distance_1d(s1, s2)
        assert dist_1d == dist_2d, f"Mismatch for '{s1}' vs '{s2}': 2D={dist_2d}, 1D={dist_1d}"


def test_query_processor_pipeline():
    """Verify QueryProcessor integration with Bloom Filter and Levenshtein DP."""
    from app.data_structures.bloom_filter import BloomFilter
    from app.search.query_processor import QueryProcessor

    vocab = ["wireless", "keyboard", "mouse", "monitor"]
    bf = BloomFilter(expected_elements=10, false_positive_rate=0.01)
    for term in vocab:
        bf.add(term)

    qp = QueryProcessor(bloom_filter=bf, vocabulary=vocab, max_edit_distance=2)

    # Typo in both tokens: "wireles keybrd" -> "wireless keyboard"
    res = qp.process_query("wireles keybrd")
    assert res["corrected"] is True
    assert res["corrected_query"] == "wireless keyboard"
    assert res["effective_query"] == "wireless keyboard"

    # Exact match: no correction
    res_exact = qp.process_query("wireless keyboard")
    assert res_exact["corrected"] is False
    assert res_exact["corrected_query"] is None
    assert res_exact["effective_query"] == "wireless keyboard"

    # Stop words preserved
    res_stop = qp.process_query("mouse with wireles")
    assert res_stop["corrected"] is True
    assert res_stop["corrected_query"] == "mouse with wireless"

