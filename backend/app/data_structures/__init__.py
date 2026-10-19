"""In-memory data structures module.

Implementations:
- AVLTree: Self-balancing binary search tree storing terms and posting lists.
- Trie (upcoming milestone): Prefix tree for autocomplete.
- BloomFilter (upcoming milestone): Probabilistic membership filter.
"""

try:
    from backend.app.data_structures.avl_tree import AVLTree, AVLNode
except ModuleNotFoundError:
    from app.data_structures.avl_tree import AVLTree, AVLNode

__all__ = ["AVLTree", "AVLNode"]
