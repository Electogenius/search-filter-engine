# Search and Filter Engine for E-Commerce Application

A high-performance in-memory search, filtering, and recommendation engine for e-commerce product catalogues, built as a Data Structures & Algorithms term group project.

---

## 1. Project Overview

Modern e-commerce platforms handle massive catalogues requiring millisecond search responses, multi-criteria filtering (price, rating, category, availability), fault-tolerant fuzzy matching for misspelled queries, and relevant product recommendations.

This project implements an end-to-end web application backed by custom in-memory data structures and algorithmic scoring, eliminating linear searches and rigid text matching:

- **Inverted Index Tree**: Token-to-posting-list index for instant term lookups.
- **Trie (Prefix Tree)**: Fast prefix traversal for real-time autocomplete suggestions.
- **Bloom Filter**: Probabilistic set membership test to eliminate unnecessary index lookups for non-existent tokens.
- **Okapi BM25 Ranking**: Probabilistic relevance scoring factoring term frequency and inverse document frequency.
- **WAND (Weak AND) Algorithm**: Dynamic threshold pruning for efficient top-k candidate retrieval without evaluating every document.
- **Levenshtein Distance**: Dynamic programming edit-distance calculation to resolve typos and alternative spellings.
- **Market Basket Co-occurrence**: Recommendation engine computing item association frequencies from customer transaction baskets.

> **Storage Architecture Note**: All product datasets and transaction baskets are loaded directly from local JSON files into memory at startup. All index structures, trees, filters, and matrices are built and queried entirely **in memory**. No external database (SQL/NoSQL) is used.

<!-- ---

## 2. Directory Structure

```text
search-filter-engine/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                     # FastAPI application setup and middleware
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py               # REST API endpoints & route handlers
│   │   ├── data_structures/            # Custom in-memory DSA implementations
│   │   │   └── __init__.py             # (Inverted Index, Trie, Bloom Filter)
│   │   ├── indexing/                   # Dataset loader, tokenization & index builder
│   │   │   └── __init__.py
│   │   ├── ranking/                    # BM25 relevance & WAND top-k algorithms
│   │   │   └── __init__.py
│   │   ├── recommendations/            # Co-occurrence matrix & recommendation graph
│   │   │   └── __init__.py
│   │   └── search/                     # Query parsing, fuzzy matching & orchestrator
│   │       └── __init__.py
│   └── tests/
│       ├── __init__.py
│       └── test_health.py              # Automated tests (health check & route contract)
├── data/
│   ├── products.json                   # Sample product catalogue (18 products)
│   └── baskets.json                    # Customer transaction baskets for recommendations
├── docs/
│   └── api-contract.md                 # REST API parameter & response schema specification
├── frontend/
│   ├── index.html                      # Semantic UI with search bar, filters, sort, results
│   ├── styles.css                      # Modern responsive styling (no frameworks)
│   └── app.js                          # Client-side interactions & API hooks
├── .gitignore                          # Git ignore rules for Python, virtualenv, and caches
├── requirements.txt                    # Minimal backend dependencies (FastAPI, uvicorn, pytest)
└── README.md                           # Project documentation and team guidelines
``` -->

---

## Prerequisites

- **Python**: Version 3.10 or higher
- **Web Browser**: Any modern browser (Chrome, Firefox, Safari, Edge)

---

## Setup and Run Instructions

### Backend Setup

1. **Navigate to the project root**:
   ```bash
   cd search-filter-engine
   ```

2. **Create and activate a Python virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the backend development server**:
   ```bash
   uvicorn backend.app.main:app --reload --port 8000
   ```
   - API Base URL: `http://localhost:8000`
   - Interactive Swagger Docs: `http://localhost:8000/docs`
   - Health Check: `http://localhost:8000/api/health`

### Running Automated Tests

Run the test suite with `pytest`:
```bash
pytest backend/tests/ -v
```

### Running the Frontend

The frontend is built using standard HTML5, CSS3, and JavaScript, no Node.js build system, bundler, or package manager is required.

To run the frontend:
- **Option A (Python simple HTTP server)**:
  ```bash
  python3 -m http.server 3000 --directory frontend
  ```
  Open `http://localhost:3000` in your web browser.
- **Option B**:
  Simply open `frontend/index.html` directly in any web browser.

<!-- --- -->

<!-- ## Team Contribution Workflow

To adhere to the course evaluation criteria (individual GitHub accounts, clear commit history, and distinct module ownership for individual interviews):

1. **Main Branch Protection**:
   - `main` represents stable, tested code. Do not push directly to `main`.
2. **Feature Branching**:
   - Every team member must create a dedicated feature branch for their assigned component:
     - `feature/trie-autocomplete`
     - `feature/inverted-index-bloom`
     - `feature/bm25-wand-ranking`
     - `feature/fuzzy-search-levenshtein`
     - `feature/cooccurrence-recommendations`
     - `feature/frontend-integration`
3. **Individual Commits & Accounts**:
   - All commits must be made from each team member's verified individual GitHub account.
   - Use clear, descriptive commit messages (e.g., `feat(ranking): implement Okapi BM25 scoring function`).
4. **Pull Requests (PRs) & Code Review**:
   - Submit a Pull Request targeting `main`.
   - Ensure all `pytest` automated tests pass before requesting review.
   - At least one team member should review and approve the PR before merging.
 -->
