"""In-memory data structures module.

Implementations:
- AVLTree: Self-balancing binary search tree storing terms and posting lists.
- Trie: Prefix tree for autocomplete.
- BloomFilter (upcoming milestone): Probabilistic membership filter.
"""

try:
    from backend.app.data_structures.avl_tree import AVLTree, AVLNode
    from backend.app.data_structures.trie import Trie, TrieNode
except ModuleNotFoundError:
    from app.data_structures.avl_tree import AVLTree, AVLNode
    from app.data_structures.trie import Trie, TrieNode

__all__ = ["AVLTree", "AVLNode", "Trie", "TrieNode"]
