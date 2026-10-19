"""Custom Trie (Prefix Tree) data structure for autocomplete suggestions.

Supports O(L) insertion and O(L) prefix traversal (where L is the length of the string),
followed by a Depth-First Search (DFS) over the subtree to collect and rank candidate completions.
"""

from typing import List, Optional


class TrieNode:
    """A single node in the Trie (Prefix Tree).

    Attributes:
        children (dict): Mapping from character (str) to child TrieNode.
        is_end_of_word (bool): True if a complete word/title terminates at this node.
        payloads (list): Stores product titles or term metadata terminating here.
        frequency (int): Priority weight / popularity count used to rank completions.
    """

    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.payloads = []
        self.frequency = 0


class Trie:
    """In-memory Trie (Prefix Tree) for fast autocomplete and prefix matching."""

    def __init__(self):
        # The root node represents the empty string ""
        self.root = TrieNode()
        self._size = 0

    def __len__(self) -> int:
        """Return total number of unique words/phrases stored in the Trie."""
        return self._size

    def insert(self, word: str, payload: Optional[object] = None) -> None:
        """Insert a word or product title into the Trie in O(L) time.

        Args:
            word: The string to insert (case-insensitive).
            payload: Optional metadata (e.g. dict with title and frequency, or string).
        """
        if not word or not isinstance(word, str):
            return

        normalized = word.strip().lower()
        if not normalized:
            return

        # Determine priority weight (higher for complete product titles)
        freq = 1
        if isinstance(payload, dict):
            freq = int(payload.get("frequency", 1))

        # Walk character-by-character from the root, creating nodes as needed
        current = self.root
        for char in normalized:
            if char not in current.children:
                current.children[char] = TrieNode()
            current = current.children[char]

        # Mark completion at the final character node
        if not current.is_end_of_word:
            current.is_end_of_word = True
            self._size += 1

        current.frequency += freq
        current.payloads.append(payload if payload is not None else normalized)

    def _find_node(self, prefix: str) -> Optional[TrieNode]:
        """Traverse to the node representing the prefix in O(L) time."""
        current = self.root
        for char in prefix:
            if char not in current.children:
                return None
            current = current.children[char]
        return current

    def contains(self, word: str) -> bool:
        """Check if an exact word exists in the Trie in O(L) time."""
        if not word:
            return False
        node = self._find_node(word.strip().lower())
        return node is not None and node.is_end_of_word

    def starts_with(self, prefix: str) -> bool:
        """Check if any word in the Trie begins with the given prefix in O(L) time."""
        if not prefix:
            return False
        return self._find_node(prefix.strip().lower()) is not None

    def search_prefix(self, prefix: str, limit: int = 5) -> List[str]:
        """Find top autocomplete completions for a prefix in O(L + K) time.

        Args:
            prefix: The substring typed by the user.
            limit: Maximum number of suggestions to return.

        Returns:
            List of unique suggestion strings, ranked by frequency descending.
        """
        if not prefix or limit <= 0:
            return []

        clean_prefix = prefix.strip().lower()
        if not clean_prefix:
            return []

        # 1. Step O(L): Locate the prefix node in the tree
        prefix_node = self._find_node(clean_prefix)
        if not prefix_node:
            return []

        # 2. Step O(K): Depth-First Search (DFS) over the subtree to collect completions
        candidates = []
        seen = set()
        stack = [(prefix_node, clean_prefix)]

        while stack:
            node, path = stack.pop()

            if node.is_end_of_word:
                # Extract display text from payload or reconstructed path
                text = path
                for p in node.payloads:
                    if isinstance(p, dict):
                        text = str(p.get("title") or p.get("text") or path).lower()
                    elif isinstance(p, str):
                        text = p.lower()

                if text not in seen:
                    seen.add(text)
                    candidates.append((text, node.frequency, len(text)))

            # Push children to stack (reverse sorted for deterministic alphabetical order)
            for char in sorted(node.children.keys(), reverse=True):
                stack.append((node.children[char], path + char))

        # 3. Rank: frequency descending (popular items first), then shorter length
        candidates.sort(key=lambda item: (-item[1], item[2], item[0]))

        return [item[0] for item in candidates[:limit]]

    def get_all_words(self) -> List[str]:
        """Return all unique words stored in the Trie."""
        words = []
        stack = [(self.root, "")]
        while stack:
            node, path = stack.pop()
            if node.is_end_of_word:
                words.append(path)
            for char in sorted(node.children.keys(), reverse=True):
                stack.append((node.children[char], path + char))
        return words
