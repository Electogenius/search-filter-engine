"""Bloom Filter data structure for probabilistic set membership testing.

Provides O(k) insertion and O(k) membership query time complexity with zero false negatives
and a tunable false positive probability p (default p = 0.01).
Utilizes double hashing (Kirsch-Mitzenmacher optimization) over an array-backed bit vector.
"""

import hashlib
import math
from typing import List, Optional


class BloomFilter:
    """Space-efficient probabilistic data structure for set membership testing.

    Attributes:
        expected_elements (int): Anticipated number of items (n) to be stored.
        false_positive_rate (float): Target false positive probability (p).
        size (int): Total number of bits (m) in the underlying bit array.
        hash_count (int): Number of independent hash evaluations (k).
        bit_array (bytearray): Byte array storing packed bits.
        count (int): Number of items added to the filter.
    """

    def __init__(
        self,
        expected_elements: int = 1000,
        false_positive_rate: float = 0.01,
        size: Optional[int] = None,
        hash_count: Optional[int] = None
    ):
        """Initialize the Bloom Filter with optimal or explicit size and hash counts.

        Optimal sizing formulas:
            m = - (n * ln(p)) / (ln 2)^2
            k = (m / n) * ln 2
        """
        self.expected_elements: int = max(1, int(expected_elements))
        self.false_positive_rate: float = (
            false_positive_rate if 0 < false_positive_rate < 1 else 0.01
        )

        if size is not None:
            self.size: int = max(1, int(size))
        else:
            self.size = self.calculate_optimal_size(
                self.expected_elements,
                self.false_positive_rate
            )

        if hash_count is not None:
            self.hash_count: int = max(1, int(hash_count))
        else:
            self.hash_count = self.calculate_optimal_hash_count(
                self.size,
                self.expected_elements
            )

        # Allocate bytearray: ceil(m / 8) bytes to store m bits
        self.byte_count: int = (self.size + 7) // 8
        self.bit_array: bytearray = bytearray(self.byte_count)
        self.count: int = 0

    @staticmethod
    def calculate_optimal_size(n: int, p: float) -> int:
        """Calculate optimal bit array size m = ceil(-n * ln(p) / (ln 2)^2)."""
        if n <= 0:
            n = 1
        if not (0 < p < 1):
            p = 0.01
        m = -(n * math.log(p)) / (math.log(2) ** 2)
        return max(1, math.ceil(m))

    @staticmethod
    def calculate_optimal_hash_count(m: int, n: int) -> int:
        """Calculate optimal hash function count k = round((m / n) * ln 2)."""
        if n <= 0:
            n = 1
        k = (m / n) * math.log(2)
        return max(1, round(k))

    def _get_hash_indices(self, token: str) -> List[int]:
        """Generate k bit indices using Kirsch-Mitzenmacher double hashing:

            h_i(x) = (h_1(x) + i * h_2(x)) mod m

        Where h_1 and h_2 are two 64-bit integer digests derived from SHA-256.
        """
        raw_bytes = str(token).encode("utf-8")
        digest = hashlib.sha256(raw_bytes).digest()

        # Extract two 64-bit unsigned integers from 32-byte SHA-256 digest
        h1 = int.from_bytes(digest[:8], byteorder="big")
        h2 = int.from_bytes(digest[8:16], byteorder="big")

        # Ensure non-zero step size that is relatively coprime to size
        if h2 == 0 or h2 % self.size == 0:
            h2 = 1

        indices: List[int] = []
        for i in range(self.hash_count):
            idx = (h1 + (i * h2)) % self.size
            indices.append(idx)

        return indices

    def add(self, token: str) -> None:
        """Insert a token into the Bloom Filter by setting k bit positions.

        Time Complexity: O(k) where k is the number of hash functions.
        """
        if token is None:
            return

        indices = self._get_hash_indices(token)
        for idx in indices:
            byte_idx = idx // 8
            bit_offset = idx % 8
            self.bit_array[byte_idx] |= (1 << bit_offset)

        self.count += 1

    def contains(self, token: str) -> bool:
        """Test for token set membership.

        Guarantees:
        - If False is returned: Token is DEFINITELY NOT in the set (0% False Negatives).
        - If True is returned: Token is PROBABLY in the set (subject to false positive rate p).

        Time Complexity: O(k).
        """
        if token is None:
            return False

        indices = self._get_hash_indices(token)
        for idx in indices:
            byte_idx = idx // 8
            bit_offset = idx % 8
            if not (self.bit_array[byte_idx] & (1 << bit_offset)):
                return False

        return True

    def __contains__(self, token: str) -> bool:
        """Enable Python 'in' operator syntax: token in bloom_filter."""
        return self.contains(token)

    def __len__(self) -> int:
        """Return the total number of items inserted so far."""
        return self.count

    def clear(self) -> None:
        """Reset all bits in the bit array to zero."""
        for i in range(self.byte_count):
            self.bit_array[i] = 0
        self.count = 0

    def current_false_positive_rate(self) -> float:
        """Compute the theoretical false positive rate for current element count:

            p_current = (1 - e^(-k * n / m))^k
        """
        if self.count == 0:
            return 0.0
        exponent = -(self.hash_count * self.count) / self.size
        return (1.0 - math.exp(exponent)) ** self.hash_count

    def __repr__(self) -> str:
        return (
            f"BloomFilter(n={self.expected_elements}, p={self.false_positive_rate}, "
            f"m={self.size} bits, k={self.hash_count}, count={self.count})"
        )

