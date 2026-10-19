"""Indexing and tokenization module.

Components:
- Tokenizer: Text normalization, token filtering, and term frequency extraction.
- AVLInvertedIndex: Inverted index mapping terms to posting lists via AVL Tree.
"""

try:
    from backend.app.indexing.tokenizer import Tokenizer
    from backend.app.indexing.inverted_index import AVLInvertedIndex
except ModuleNotFoundError:
    from app.indexing.tokenizer import Tokenizer
    from app.indexing.inverted_index import AVLInvertedIndex

__all__ = ["Tokenizer", "AVLInvertedIndex"]

