"""Fuzzy string matching using Levenshtein / Damerau-Levenshtein Dynamic Programming.

Implements:
1. Bottom-up 2D DP table computing edit distance with substitution, insertion,
   deletion, and adjacent character transposition.
2. Space-optimized 1D / two-row DP table computing edit distance in O(min(m, n)) space.
3. Vocabulary candidate lookup finding closest matching terms within edit threshold k <= 2.
"""

from typing import Dict, Iterable, List, Optional, Tuple, Union


def levenshtein_distance(
    s1: str,
    s2: str,
    max_distance: Optional[int] = None,
    allow_transpositions: bool = True
) -> int:
    """Compute edit distance between s1 and s2 using a bottom-up 2D DP table.

    Operations supported:
    - Substitution: replace s1[i] with s2[j] (cost 1 if characters differ, 0 if identical)
    - Insertion: insert s2[j] into s1 (cost 1)
    - Deletion: delete s1[i] from s1 (cost 1)
    - Transposition: swap adjacent characters s1[i-1] and s1[i-2] (cost 1 if allow_transpositions is True)

    Args:
        s1: First string (e.g., query token).
        s2: Second string (e.g., vocabulary candidate).
        max_distance: Optional upper bound threshold for early termination.
        allow_transpositions: Whether adjacent character swaps count as 1 edit.

    Returns:
        Integer edit distance between s1 and s2.
    """
    if s1 == s2:
        return 0

    m, n = len(s1), len(s2)

    # Length-difference pruning: if the difference in lengths exceeds max_distance,
    # the minimum number of insertions/deletions alone exceeds the threshold.
    if max_distance is not None and abs(m - n) > max_distance:
        return max_distance + 1

    if m == 0:
        return n
    if n == 0:
        return m

    # Construct (m + 1) x (n + 1) DP table
    # dp[i][j] represents the minimum edit distance between prefix s1[:i] and prefix s2[:j]
    dp = [[0] * (n + 1) for _ in range(m + 1)]

    # Base cases: transforming to / from the empty string
    for i in range(m + 1):
        dp[i][0] = i
    for j in range(n + 1):
        dp[0][j] = j

    # Bottom-up iterative table filling
    for i in range(1, m + 1):
        row_min = dp[i][0]
        char1 = s1[i - 1]

        for j in range(1, n + 1):
            char2 = s2[j - 1]
            cost = 0 if char1 == char2 else 1

            # Standard Levenshtein recurrence
            dp[i][j] = min(
                dp[i - 1][j] + 1,        # Deletion from s1
                dp[i][j - 1] + 1,        # Insertion into s1
                dp[i - 1][j - 1] + cost  # Substitution
            )

            # Transposition recurrence (Damerau-Levenshtein condition)
            if (
                allow_transpositions
                and i > 1
                and j > 1
                and char1 == s2[j - 2]
                and s1[i - 2] == char2
            ):
                dp[i][j] = min(dp[i][j], dp[i - 2][j - 2] + 1)

            if dp[i][j] < row_min:
                row_min = dp[i][j]

        # Early termination: if every cell in the current row exceeds max_distance,
        # subsequent rows cannot produce a distance <= max_distance.
        if max_distance is not None and row_min > max_distance:
            return max_distance + 1

    return dp[m][n]


def levenshtein_distance_1d(s1: str, s2: str) -> int:
    """Compute standard Levenshtein distance using a space-optimized 1D / two-row DP table.

    Requires only O(min(m, n)) auxiliary space instead of O(m * n).
    """
    if s1 == s2:
        return 0

    # Ensure s2 is the shorter string to minimize space
    if len(s1) < len(s2):
        s1, s2 = s2, s1

    m, n = len(s1), len(s2)
    if n == 0:
        return m

    # previous_row stores distances for previous character of s1
    previous_row = list(range(n + 1))
    current_row = [0] * (n + 1)

    for i in range(1, m + 1):
        current_row[0] = i
        char1 = s1[i - 1]

        for j in range(1, n + 1):
            char2 = s2[j - 1]
            cost = 0 if char1 == char2 else 1

            current_row[j] = min(
                previous_row[j] + 1,        # Deletion
                current_row[j - 1] + 1,     # Insertion
                previous_row[j - 1] + cost  # Substitution
            )

        previous_row, current_row = current_row, previous_row

    return previous_row[n]


def find_closest_match(
    token: str,
    vocabulary: Union[Iterable[str], Dict[str, int]],
    max_distance: int = 2,
    allow_transpositions: bool = True
) -> Optional[str]:
    """Find the single closest matching term in vocabulary within max_distance threshold.

    Candidate filtering:
    - Prunes candidates whose length difference |len(token) - len(candidate)| > max_distance.
    - Uses early termination in DP table once current distance exceeds the best seen so far.
    - Tie-breaking:
      1. Lower edit distance
      2. If vocabulary is a Dict[term, frequency], higher frequency
      3. Longer common prefix length
      4. Lexicographical order

    Args:
        token: Query token to correct (e.g., "wireles", "keybrd").
        vocabulary: Iterable of valid terms or Dict mapping term -> frequency.
        max_distance: Maximum allowable edit distance (typically 2).
        allow_transpositions: Whether adjacent swaps count as 1 edit.

    Returns:
        The best matching vocabulary word, or None if no word is within max_distance.
    """
    if not token or not vocabulary:
        return None

    normalized_token = token.strip().lower()
    token_len = len(normalized_token)

    is_dict = isinstance(vocabulary, dict)
    candidates = vocabulary.keys() if is_dict else vocabulary

    best_match: Optional[str] = None
    best_distance = max_distance + 1
    best_freq = -1
    best_prefix_len = -1

    for candidate in candidates:
        if not candidate:
            continue

        cand_norm = candidate.strip().lower()

        # Quick length difference filter: O(1)
        if abs(token_len - len(cand_norm)) > max_distance:
            continue

        # Exact match check: O(1)
        if cand_norm == normalized_token:
            return candidate

        # Compute edit distance bounded by current best_distance
        dist = levenshtein_distance(
            normalized_token,
            cand_norm,
            max_distance=best_distance,
            allow_transpositions=allow_transpositions
        )

        if dist > max_distance:
            continue

        cand_freq = vocabulary.get(candidate, 0) if is_dict else 0
        cand_prefix = _common_prefix_length(normalized_token, cand_norm)

        # Better distance found
        if dist < best_distance:
            best_distance = dist
            best_match = candidate
            best_freq = cand_freq
            best_prefix_len = cand_prefix
        # Tie breaker: same edit distance
        elif dist == best_distance:
            if is_dict and cand_freq > best_freq:
                best_match = candidate
                best_freq = cand_freq
                best_prefix_len = cand_prefix
            elif (not is_dict or cand_freq == best_freq) and cand_prefix > best_prefix_len:
                best_match = candidate
                best_prefix_len = cand_prefix
            elif (
                (not is_dict or cand_freq == best_freq)
                and cand_prefix == best_prefix_len
                and (best_match is None or candidate < best_match)
            ):
                best_match = candidate

    return best_match if best_distance <= max_distance else None


def find_closest_matches(
    token: str,
    vocabulary: Union[Iterable[str], Dict[str, int]],
    max_distance: int = 2,
    limit: int = 5,
    allow_transpositions: bool = True
) -> List[Tuple[str, int]]:
    """Find top candidate matches within max_distance, sorted by distance and relevance."""
    if not token or not vocabulary:
        return []

    normalized_token = token.strip().lower()
    token_len = len(normalized_token)

    is_dict = isinstance(vocabulary, dict)
    candidates = vocabulary.keys() if is_dict else vocabulary

    matches: List[Tuple[int, int, str]] = []

    for candidate in candidates:
        if not candidate:
            continue

        cand_norm = candidate.strip().lower()
        if abs(token_len - len(cand_norm)) > max_distance:
            continue

        dist = levenshtein_distance(
            normalized_token,
            cand_norm,
            max_distance=max_distance,
            allow_transpositions=allow_transpositions
        )

        if dist <= max_distance:
            freq = vocabulary.get(candidate, 0) if is_dict else 0
            matches.append((dist, -freq, candidate))

    matches.sort()
    return [(cand, dist) for dist, _, cand in matches[:limit]]


def _common_prefix_length(s1: str, s2: str) -> int:
    """Compute number of leading characters s1 and s2 share."""
    limit = min(len(s1), len(s2))
    length = 0
    for i in range(limit):
        if s1[i] == s2[i]:
            length += 1
        else:
            break
    return length

