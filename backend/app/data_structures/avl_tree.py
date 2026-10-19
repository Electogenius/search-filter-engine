"""AVL-Tree based dictionary and posting-list index.

An AVL (Adelson-Velsky and Landis) Tree is a strictly self-balancing binary search
tree. For every node, the heights of its left and right subtrees differ by at
most 1 (balance factor in {-1, 0, 1}).

Time Complexities:
- Search: O(log n) where n is the total number of unique vocabulary terms.
- Insertion: O(log n) guaranteed worst-case due to at most 2 tree rotations.
- In-order traversal: O(n) yielding lexicographically sorted vocabulary.
"""

from typing import Dict, List, Optional, Tuple


class AVLNode:
    """A node in the AVL Inverted Index Tree.

    Attributes:
        term: Vocabulary term (BST search key).
        postings: Mapping from document/product ID to term frequency in that document.
        height: Height of the subtree rooted at this node (leaves have height 1).
        left: Left child node (lexicographically smaller terms).
        right: Right child node (lexicographically larger terms).
    """

    def __init__(self, term: str, doc_id: Optional[str] = None, count: int = 1):
        self.term: str = term
        self.postings: Dict[str, int] = {}
        if doc_id is not None:
            self.postings[doc_id] = count
        self.height: int = 1
        self.left: Optional["AVLNode"] = None
        self.right: Optional["AVLNode"] = None

    def add_posting(self, doc_id: str, count: int = 1) -> None:
        """Add or increment the term occurrence count for a document."""
        self.postings[doc_id] = self.postings.get(doc_id, 0) + count


class AVLTree:
    """Self-balancing AVL Tree storing vocabulary terms mapped to document postings."""

    def __init__(self):
        self.root: Optional[AVLNode] = None
        self._size: int = 0

    def __len__(self) -> int:
        """Return the number of unique terms stored in the AVL tree."""
        return self._size

    @staticmethod
    def _get_height(node: Optional[AVLNode]) -> int:
        """Return height of node, or 0 if node is None."""
        return node.height if node else 0

    @classmethod
    def _get_balance(cls, node: Optional[AVLNode]) -> int:
        """Compute balance factor: height(left) - height(right)."""
        if not node:
            return 0
        return cls._get_height(node.left) - cls._get_height(node.right)

    def _rotate_right(self, y: AVLNode) -> AVLNode:
        r"""Perform a Right Rotation on node y.

             y                               x
            / \     Right Rotation          / \
           x   T3   -------------->        T1  y
          / \                                 / \
         T1  T2                              T2 T3
        """
        x = y.left
        assert x is not None
        t2 = x.right

        # Perform rotation
        x.right = y
        y.left = t2

        # Update heights
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))

        return x

    def _rotate_left(self, x: AVLNode) -> AVLNode:
        r"""Perform a Left Rotation on node x.

           x                                 y
          / \       Left Rotation           / \
         T1  y      ------------->         x   T3
            / \                           / \
           T2 T3                         T1 T2
        """
        y = x.right
        assert y is not None
        t2 = y.left

        # Perform rotation
        y.left = x
        x.right = t2

        # Update heights
        x.height = 1 + max(self._get_height(x.left), self._get_height(x.right))
        y.height = 1 + max(self._get_height(y.left), self._get_height(y.right))

        return y

    def insert(self, term: str, doc_id: str, count: int = 1) -> None:
        """Insert a term with its document occurrence into the AVL tree.

        If the term already exists, its posting list is updated in-place without
        modifying tree structure.
        """
        self.root = self._insert_node(self.root, term, doc_id, count)

    def _insert_node(
        self,
        node: Optional[AVLNode],
        term: str,
        doc_id: str,
        count: int
    ) -> AVLNode:
        # 1. Standard BST insertion
        if not node:
            self._size += 1
            return AVLNode(term, doc_id, count)

        if term == node.term:
            # Term already exists in index: append/increment posting list
            node.add_posting(doc_id, count)
            return node
        elif term < node.term:
            node.left = self._insert_node(node.left, term, doc_id, count)
        else:
            node.right = self._insert_node(node.right, term, doc_id, count)

        # 2. Update height of current ancestor node
        node.height = 1 + max(self._get_height(node.left), self._get_height(node.right))

        # 3. Check balance factor to determine if rebalancing is required
        balance = self._get_balance(node)

        # Case 1: Left-Left (LL) - Right rotation
        if balance > 1 and node.left and term < node.left.term:
            return self._rotate_right(node)

        # Case 2: Right-Right (RR) - Left rotation
        if balance < -1 and node.right and term > node.right.term:
            return self._rotate_left(node)

        # Case 3: Left-Right (LR) - Left rotation on left child, then Right rotation
        if balance > 1 and node.left and term > node.left.term:
            node.left = self._rotate_left(node.left)
            return self._rotate_right(node)

        # Case 4: Right-Left (RL) - Right rotation on right child, then Left rotation
        if balance < -1 and node.right and term < node.right.term:
            node.right = self._rotate_right(node.right)
            return self._rotate_left(node)

        return node

    def search(self, term: str) -> Optional[Dict[str, int]]:
        """Search for a term in O(log V) time and return its posting list dict.

        Returns:
            Dict[doc_id, frequency] if term exists, None otherwise.
        """
        node = self.root
        while node:
            if term == node.term:
                return node.postings
            elif term < node.term:
                node = node.left
            else:
                node = node.right
        return None

    def get_vocabulary(self) -> List[str]:
        """Perform an in-order traversal to retrieve all unique vocabulary terms sorted."""
        terms: List[str] = []

        def _in_order(node: Optional[AVLNode]):
            if not node:
                return
            _in_order(node.left)
            terms.append(node.term)
            _in_order(node.right)

        _in_order(self.root)
        return terms

    def get_height(self) -> int:
        """Return the current height of the AVL tree root."""
        return self._get_height(self.root)
