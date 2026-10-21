"""In-memory data structures module.

Implementations:
- AVLTree: Self-balancing binary search tree storing terms and posting lists.
- Trie: Prefix tree for autocomplete.
- BloomFilter: Probabilistic set membership filter with 0% false negatives.
"""

try:
    from backend.app.data_structures.avl_tree import AVLTree, AVLNode
    from backend.app.data_structures.trie import Trie, TrieNode
    from backend.app.data_structures.bloom_filter import BloomFilter
except ModuleNotFoundError:
    from app.data_structures.avl_tree import AVLTree, AVLNode
    from app.data_structures.trie import Trie, TrieNode
    from app.data_structures.bloom_filter import BloomFilter

__all__ = ["AVLTree", "AVLNode", "Trie", "TrieNode", "BloomFilter"]
