import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.data_structures.avl_tree import AVLTree, AVLNode


def is_avl_balanced(node: AVLNode) -> bool:
    """Helper to assert that every subtree in the AVL tree satisfies the balance invariant."""
    if not node:
        return True

    left_h = node.left.height if node.left else 0
    right_h = node.right.height if node.right else 0

    if abs(left_h - right_h) > 1:
        return False

    return is_avl_balanced(node.left) and is_avl_balanced(node.right)


def test_avl_tree_insert_and_balance():
    tree = AVLTree()
    words = ["zebra", "apple", "mango", "banana", "orange", "grape", "cherry", "kiwi", "lemon"]

    for i, word in enumerate(words):
        tree.insert(term=word, doc_id=f"doc-{i}", count=1)
        assert is_avl_balanced(tree.root)

    assert len(tree) == len(words)
    assert tree.get_vocabulary() == sorted(words)


def test_avl_tree_posting_accumulation():
    tree = AVLTree()
    tree.insert("keyboard", "doc-1", 2)
    tree.insert("keyboard", "doc-2", 1)
    tree.insert("keyboard", "doc-1", 3)  # duplicate doc_id should accumulate frequency

    postings = tree.search("keyboard")
    assert postings is not None
    assert postings["doc-1"] == 5
    assert postings["doc-2"] == 1


def test_avl_tree_search_non_existent():
    tree = AVLTree()
    tree.insert("laptop", "doc-1", 1)
    assert tree.search("laptop") is not None
    assert tree.search("desktop") is None

