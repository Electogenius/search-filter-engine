# start fastapi backend server

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.app.api.routes import router as api_router
except ModuleNotFoundError:
    from app.api.routes import router as api_router

app = FastAPI(
    title="E-Commerce Search & Filter Engine",
    description=(
        "In-memory search, filtering, and recommendation engine using custom "
        "data structures (Inverted Index, Trie, Bloom Filter) and algorithms "
        "(BM25, WAND, Levenshtein distance)."
    ),
    version="0.1.0",
)

# enable CORS for local frontend development (plain HTML/CSS/JS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# mount API routes under /api
app.include_router(api_router, prefix="/api")


@app.get("/")
def root() -> dict:
    """Root route redirecting or describing service availability."""
    return {
        "message": "Welcome to the E-Commerce Search & Filter Engine API",
        "health": "/api/health",
        "docs": "/docs"
    }
